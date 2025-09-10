"""
Session Lifecycle Service - Centralized management of diary session completion
Ensures proper state transitions and timestamp handling for DiarySession objects.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import DiarySession, User
from app.services.memory_service import MemoryService
import logging

class SessionLifecycleService:
    """Service for managing the complete lifecycle of diary sessions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.memory_service = MemoryService()
        self.logger = logging.getLogger(__name__)
    
    def complete_session(self, session: DiarySession, diary_content: str) -> DiarySession:
        """
        Atomically complete a diary session with proper state updates
        
        Args:
            session: The DiarySession to complete
            diary_content: The final diary content
            
        Returns:
            The completed DiarySession
        """
        try:
            # Update session state atomically
            session.is_complete = True
            session.completed_at = datetime.utcnow()
            session.final_diary = diary_content
            session.current_phase = 'complete'
            
            # Commit the session completion first
            self.db.commit()
            self.db.refresh(session)
            
            # Process memories asynchronously after completion
            self._process_session_memories(session)
            
            self.logger.info(f"Successfully completed diary session {session.id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to complete session {session.id}: {e}")
            self.db.rollback()
            raise
    
    def mark_session_in_crisis(self, session: DiarySession) -> DiarySession:
        """
        Mark a session as being in crisis mode
        
        Args:
            session: The DiarySession to mark as crisis
            
        Returns:
            The updated DiarySession
        """
        try:
            session.is_crisis = True
            session.current_phase = 'crisis'
            session.current_intent = 'CRISIS_FLOW'
            
            self.db.commit()
            self.db.refresh(session)
            
            self.logger.warning(f"Marked diary session {session.id} as crisis")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to mark session {session.id} as crisis: {e}")
            self.db.rollback()
            raise
    
    def update_session_state(self, session: DiarySession, 
                           phase: Optional[str] = None,
                           intent: Optional[str] = None,
                           structured_data: Optional[dict] = None) -> DiarySession:
        """
        Update session state with proper transaction handling
        
        Args:
            session: The DiarySession to update
            phase: New current_phase value
            intent: New current_intent value  
            structured_data: New structured_data value
            
        Returns:
            The updated DiarySession
        """
        try:
            if phase is not None:
                session.current_phase = phase
            if intent is not None:
                session.current_intent = intent
            if structured_data is not None:
                session.structured_data = structured_data
                
            self.db.commit()
            self.db.refresh(session)
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to update session {session.id} state: {e}")
            self.db.rollback()
            raise
    
    def _process_session_memories(self, session: DiarySession) -> None:
        """
        Process memories from a completed session
        This is called after session completion to extract and store user memories
        
        Args:
            session: The completed DiarySession
        """
        try:
            if not session.final_diary:
                return
                
            # Extract memories from the final diary content
            memories = self.memory_service.extract_memory_from_conversation(
                session.final_diary, session.user_id
            )
            
            if memories:
                # Store memories in database
                self.memory_service.store_memories(memories, self.db)
                self.logger.info(f"Processed {len(memories)} memories for session {session.id}")
            
        except Exception as e:
            # Don't fail the entire completion if memory processing fails
            self.logger.error(f"Failed to process memories for session {session.id}: {e}")
    
    def get_session_completion_status(self, session: DiarySession) -> dict:
        """
        Get detailed completion status for a session
        
        Args:
            session: The DiarySession to check
            
        Returns:
            Dictionary with completion status details
        """
        return {
            "id": session.id,
            "is_complete": session.is_complete,
            "current_phase": session.current_phase,
            "current_intent": session.current_intent,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "has_final_diary": bool(session.final_diary),
            "is_crisis": session.is_crisis,
            "created_at": session.created_at.isoformat() if session.created_at else None
        }
    
    def cleanup_incomplete_sessions(self, user_id: int, older_than_hours: int = 24) -> int:
        """
        Clean up incomplete sessions older than specified hours
        
        Args:
            user_id: User whose sessions to clean up
            older_than_hours: Age threshold in hours
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            incomplete_sessions = self.db.query(DiarySession).filter(
                DiarySession.user_id == user_id,
                DiarySession.is_complete == False,
                DiarySession.created_at < cutoff_time
            ).all()
            
            count = len(incomplete_sessions)
            
            for session in incomplete_sessions:
                self.db.delete(session)
            
            self.db.commit()
            
            self.logger.info(f"Cleaned up {count} incomplete sessions for user {user_id}")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup sessions for user {user_id}: {e}")
            self.db.rollback()
            raise