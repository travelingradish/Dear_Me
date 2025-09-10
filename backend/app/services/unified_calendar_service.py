"""
Unified Calendar Service - Cross-mode diary entry aggregation
Provides a unified interface for accessing diary entries across all modes:
- Guided diary sessions
- Casual chat entries  
- Free writing entries
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import DiarySession, DiaryEntry
from dataclasses import dataclass
import logging

@dataclass
class UnifiedEntry:
    """Standardized diary entry representation across all modes"""
    id: str
    mode: str  # 'guided', 'casual', 'free_entry'
    content: str
    language: str
    created_at: datetime
    is_crisis: bool = False
    structured_data: Optional[Dict] = None
    metadata: Optional[Dict] = None

class UnifiedCalendarService:
    """Service for unified calendar operations across all diary modes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def get_diary_dates(self, user_id: int) -> List[str]:
        """
        Get all dates that have diary entries from any mode
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of date strings in YYYY-MM-DD format, sorted desc
        """
        try:
            # Get dates from guided diary sessions (completed only)
            guided_dates = self.db.query(
                func.date(DiarySession.completed_at).label('date')
            ).filter(
                DiarySession.user_id == user_id,
                DiarySession.is_complete == True,
                DiarySession.completed_at.isnot(None)
            ).distinct().subquery()
            
            # Get dates from casual/free diary entries
            casual_dates = self.db.query(
                func.date(DiaryEntry.created_at).label('date')
            ).filter(
                DiaryEntry.user_id == user_id
            ).distinct().subquery()
            
            # Union both date sets and sort descending
            all_dates = self.db.query(guided_dates.c.date).union(
                self.db.query(casual_dates.c.date)
            ).distinct().order_by(guided_dates.c.date.desc()).all()
            
            # Convert to list of date strings
            date_strings = [str(date_obj[0]) for date_obj in all_dates]
            
            self.logger.info(f"Found {len(date_strings)} diary dates for user {user_id}")
            return date_strings
            
        except Exception as e:
            self.logger.error(f"Failed to get diary dates for user {user_id}: {e}")
            return []
    
    def get_entries_by_date(self, user_id: int, target_date: Union[str, date]) -> List[UnifiedEntry]:
        """
        Get all diary entries for a specific date across all modes
        
        Args:
            user_id: ID of the user
            target_date: Target date as string (YYYY-MM-DD) or date object
            
        Returns:
            List of UnifiedEntry objects, sorted by creation time desc
        """
        try:
            # Parse date if string
            if isinstance(target_date, str):
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            unified_entries = []
            
            # Get guided diary sessions for that date
            guided_sessions = self._get_guided_entries_for_date(user_id, target_date)
            unified_entries.extend(guided_sessions)
            
            # Get casual/free diary entries for that date
            casual_entries = self._get_casual_entries_for_date(user_id, target_date)
            unified_entries.extend(casual_entries)
            
            # Sort by creation time descending
            unified_entries.sort(key=lambda x: x.created_at, reverse=True)
            
            self.logger.info(f"Found {len(unified_entries)} entries for user {user_id} on {target_date}")
            return unified_entries
            
        except Exception as e:
            self.logger.error(f"Failed to get entries for user {user_id} on {target_date}: {e}")
            return []
    
    def get_recent_entries(self, user_id: int, limit: int = 10) -> List[UnifiedEntry]:
        """
        Get the most recent diary entries across all modes
        
        Args:
            user_id: ID of the user
            limit: Maximum number of entries to return
            
        Returns:
            List of UnifiedEntry objects, sorted by creation time desc
        """
        try:
            # Get recent guided sessions
            recent_guided = self.db.query(DiarySession).filter(
                DiarySession.user_id == user_id,
                DiarySession.is_complete == True,
                DiarySession.completed_at.isnot(None)
            ).order_by(DiarySession.completed_at.desc()).limit(limit).all()
            
            # Get recent casual/free entries
            recent_casual = self.db.query(DiaryEntry).filter(
                DiaryEntry.user_id == user_id
            ).order_by(DiaryEntry.created_at.desc()).limit(limit).all()
            
            # Convert to unified format
            unified_entries = []
            
            for session in recent_guided:
                unified_entries.append(self._session_to_unified_entry(session))
            
            for entry in recent_casual:
                unified_entries.append(self._diary_entry_to_unified_entry(entry))
            
            # Sort by creation time and limit
            unified_entries.sort(key=lambda x: x.created_at, reverse=True)
            return unified_entries[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get recent entries for user {user_id}: {e}")
            return []
    
    def get_entry_by_id(self, user_id: int, entry_id: str) -> Optional[UnifiedEntry]:
        """
        Get a specific entry by its unified ID
        
        Args:
            user_id: ID of the user
            entry_id: Unified entry ID (format: "mode_id")
            
        Returns:
            UnifiedEntry object or None if not found
        """
        try:
            # Parse entry ID
            parts = entry_id.split('_', 1)
            if len(parts) != 2:
                return None
            
            mode, id_str = parts
            entry_db_id = int(id_str)
            
            if mode == 'guided':
                session = self.db.query(DiarySession).filter(
                    DiarySession.id == entry_db_id,
                    DiarySession.user_id == user_id,
                    DiarySession.is_complete == True
                ).first()
                
                if session:
                    return self._session_to_unified_entry(session)
            
            elif mode in ['casual', 'free_entry']:
                entry = self.db.query(DiaryEntry).filter(
                    DiaryEntry.id == entry_db_id,
                    DiaryEntry.user_id == user_id
                ).first()
                
                if entry:
                    return self._diary_entry_to_unified_entry(entry)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get entry {entry_id} for user {user_id}: {e}")
            return None
    
    def get_calendar_statistics(self, user_id: int) -> Dict:
        """
        Get calendar statistics for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with calendar statistics
        """
        try:
            # Count guided sessions
            guided_count = self.db.query(DiarySession).filter(
                DiarySession.user_id == user_id,
                DiarySession.is_complete == True
            ).count()
            
            # Count casual/free entries  
            casual_count = self.db.query(DiaryEntry).filter(
                DiaryEntry.user_id == user_id
            ).count()
            
            # Count crisis sessions
            crisis_count = self.db.query(DiarySession).filter(
                DiarySession.user_id == user_id,
                DiarySession.is_crisis == True
            ).count()
            
            # Get date range
            dates = self.get_diary_dates(user_id)
            date_range = {
                'earliest': dates[-1] if dates else None,
                'latest': dates[0] if dates else None,
                'total_days': len(dates)
            }
            
            return {
                'total_entries': guided_count + casual_count,
                'guided_sessions': guided_count,
                'casual_entries': casual_count,
                'crisis_sessions': crisis_count,
                'date_range': date_range
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get calendar statistics for user {user_id}: {e}")
            return {}
    
    def _get_guided_entries_for_date(self, user_id: int, target_date: date) -> List[UnifiedEntry]:
        """Get guided diary entries for a specific date"""
        guided_sessions = self.db.query(DiarySession).filter(
            DiarySession.user_id == user_id,
            func.date(DiarySession.completed_at) == target_date,
            DiarySession.is_complete == True,
            DiarySession.completed_at.isnot(None)
        ).order_by(DiarySession.completed_at.desc()).all()
        
        return [self._session_to_unified_entry(session) for session in guided_sessions]
    
    def _get_casual_entries_for_date(self, user_id: int, target_date: date) -> List[UnifiedEntry]:
        """Get casual/free diary entries for a specific date"""
        casual_entries = self.db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id,
            func.date(DiaryEntry.created_at) == target_date
        ).order_by(DiaryEntry.created_at.desc()).all()
        
        return [self._diary_entry_to_unified_entry(entry) for entry in casual_entries]
    
    def _session_to_unified_entry(self, session: DiarySession) -> UnifiedEntry:
        """Convert DiarySession to UnifiedEntry"""
        return UnifiedEntry(
            id=f"guided_{session.id}",
            mode="guided",
            content=session.final_diary or session.composed_diary or "",
            language=session.language or "en",
            created_at=session.completed_at or session.created_at,
            is_crisis=session.is_crisis or False,
            structured_data=session.structured_data,
            metadata={
                "current_phase": session.current_phase,
                "current_intent": session.current_intent
            }
        )
    
    def _diary_entry_to_unified_entry(self, entry: DiaryEntry) -> UnifiedEntry:
        """Convert DiaryEntry to UnifiedEntry"""
        # Determine the actual mode based on the answers field
        entry_mode = "casual"  # default
        if entry.answers and isinstance(entry.answers, dict):
            if entry.answers.get("mode") == "free_entry":
                entry_mode = "free_entry"
        
        return UnifiedEntry(
            id=f"{entry_mode}_{entry.id}",
            mode=entry_mode,
            content=entry.content or "",
            language=entry.language or "en", 
            created_at=entry.created_at,
            is_crisis=False,  # DiaryEntry doesn't have crisis detection
            structured_data=entry.answers,
            metadata={
                "original_mode": entry_mode
            }
        )