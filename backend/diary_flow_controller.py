from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from models import DiarySession, ConversationMessage, User
from guided_llm_service import GuidedLLMService
from memory_service import MemoryService
import json
import logging

class DiaryFlowController:
    """Controller for managing the guided diary conversation flow"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = GuidedLLMService()
        self.memory_service = MemoryService()
        self.logger = logging.getLogger(__name__)
        
        # Intent flow mapping
        self.intent_flow = {
            'ASK_MOOD': 'ASK_ACTIVITIES',
            'ASK_ACTIVITIES': 'ASK_CHALLENGES_WINS', 
            'ASK_CHALLENGES_WINS': 'ASK_GRATITUDE',
            'ASK_GRATITUDE': 'ASK_HOPE',
            'ASK_HOPE': 'ASK_EXTRA',
            'ASK_EXTRA': 'COMPOSE',
            'COMPOSE': 'COMPLETE',
            'CRISIS_FLOW': 'CRISIS_FLOW'
        }
    
    def start_diary_session(self, user: User, language: str = 'en', model: str = 'gemma3:4b') -> DiarySession:
        """Start a new diary session"""
        
        # Check if there's an incomplete session from today
        today = datetime.now().date()
        existing_session = self.db.query(DiarySession).filter(
            DiarySession.user_id == user.id,
            DiarySession.is_complete == False,
            DiarySession.created_at >= today
        ).first()
        
        if existing_session:
            return existing_session
        
        # Create new session
        session = DiarySession(
            user_id=user.id,
            language=language,
            current_phase='guide',
            current_intent='ASK_MOOD',
            structured_data={
                'mood': '',
                'activities': '',
                'challenges': '',
                'gratitude': '',
                'hope': '',
                'extra_notes': ''
            }
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Create initial greeting message
        if language == 'zh':
            greeting = "你好！让我们一起回顾一下你今天的经历。你今天感觉怎么样？"
        else:
            greeting = "Hello! Let's reflect on your day together. How are you feeling today?"
        
        self._add_conversation_message(
            session,
            role='assistant',
            content=greeting,
            intent='ASK_MOOD'
        )
        
        return session
    
    def process_user_message(self, session: DiarySession, user_message: str, model: str = 'gemma3:4b') -> Tuple[str, bool]:
        """
        Process user message and return assistant response
        Returns: (assistant_response, is_complete)
        """
        
        # Check if session is in crisis mode
        if session.is_crisis:
            return self._handle_crisis_response(session, user_message)
        
        # Check if session is complete
        if session.is_complete:
            if session.language == 'zh':
                return "你今天的日记已经完成了。明天再见！", True
            else:
                return "Your diary for today is complete. See you tomorrow!", True
        
        # Record user message
        self._add_conversation_message(
            session,
            role='user',
            content=user_message
        )
        
        # Process based on current phase
        if session.current_phase == 'guide':
            return self._process_guide_phase(session, user_message, model)
        elif session.current_phase == 'compose':
            return self._process_compose_phase(session, model)
        else:
            return "Something went wrong with the conversation flow.", False
    
    def _process_guide_phase(self, session: DiarySession, user_message: str, model: str = 'gemma3:4b') -> Tuple[str, bool]:
        """Process guide phase conversation"""
        
        try:
            # Get conversation history for this session
            conversation_history = []
            messages = self.db.query(ConversationMessage).filter(
                ConversationMessage.diary_session_id == session.id
            ).order_by(ConversationMessage.created_at).all()
            
            for msg in messages:
                conversation_history.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            # Get relevant memories for context
            user_memories = self.memory_service.get_relevant_memories(
                self.db, session.user_id, user_message
            )
            
            # Process with LLM
            assistant_response, slot_updates, next_intent = self.llm_service.guide_conversation_turn(
                user_message=user_message,
                current_intent=session.current_intent,
                structured_data=session.structured_data,
                conversation_history=conversation_history,
                language=session.language,
                model_name=model,
                user_memories=user_memories
            )
            
            # Check for crisis
            if next_intent == 'CRISIS_FLOW':
                session.is_crisis = True
                session.current_phase = 'crisis'
                session.current_intent = 'CRISIS_FLOW'
                
                # Override assistant response with crisis message
                if session.language == 'zh':
                    crisis_response = "听到这些我很难过。你值得被支持。如果你正处在紧急危险中，请立刻拨打当地的紧急电话。也可以联系你信任的人或专业的危机援助热线。"
                else:
                    crisis_response = "I'm really sorry you're going through this. You deserve support. If you're in immediate danger, please call your local emergency number. You can also reach out to a trusted person or a professional crisis line."
                
                self._add_conversation_message(
                    session,
                    role='assistant', 
                    content=crisis_response,
                    intent='CRISIS_FLOW'
                )
                
                self.db.commit()
                return crisis_response, False
            
            # Update structured data with slot updates  
            current_data = session.structured_data or {}
            
            # Use the LLM service to extract slot data based on current intent
            extracted_slots = self.llm_service._extract_slot_data(
                session.current_intent, user_message, current_data
            )
            
            # Merge extracted slots
            for key, value in extracted_slots.items():
                if value:  # Only update if there's actual content
                    current_data[key] = value
            
            # Also include any explicit slot updates from LLM response
            for key, value in slot_updates.items():
                if value:
                    current_data[key] = value
            
            session.structured_data = current_data
            session.current_intent = next_intent
            
            # Check if we should move to compose phase
            if next_intent == 'COMPOSE':
                session.current_phase = 'compose'
                self.db.commit()
                
                # Record the transition message
                self._add_conversation_message(
                    session,
                    role='assistant',
                    content=assistant_response,
                    intent=next_intent,
                    slot_updates=slot_updates
                )
                
                # Compose diary entry
                return self._process_compose_phase(session)
            
            # Record assistant response
            self._add_conversation_message(
                session,
                role='assistant',
                content=assistant_response,
                intent=next_intent,
                slot_updates=slot_updates
            )
            
            self.db.commit()
            
            return assistant_response, False
            
        except Exception as e:
            self.logger.error(f"Error in guide phase: {e}")
            if session.language == 'zh':
                return "抱歉，出现了一些问题。请再试一次。", False
            else:
                return "Sorry, something went wrong. Please try again.", False
    
    def _process_compose_phase(self, session: DiarySession, model: str = 'gemma3:4b') -> Tuple[str, bool]:
        """Process compose phase - generate diary entry"""
        
        try:
            # Generate diary entry using structured data
            diary_entry = self.llm_service.compose_diary_entry(
                structured_data=session.structured_data,
                language=session.language,
                model_name=model
            )
            
            # Store composed diary
            session.composed_diary = diary_entry
            session.final_diary = diary_entry  # Default to composed version
            session.current_phase = 'complete'
            session.is_complete = True
            session.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Process memories from the completed session
            try:
                self.memory_service.process_diary_session_memories(self.db, session.id)
                self.logger.info(f"Processed memories for diary session {session.id}")
            except Exception as e:
                self.logger.error(f"Failed to process memories for session {session.id}: {e}")
                # Don't fail the entire operation if memory processing fails
            
            # Return composed diary with editing prompt
            if session.language == 'zh':
                response = f"基于我们的对话，我为你写了今天的日记：\n\n{diary_entry}\n\n你可以编辑这篇日记，或者直接保存。"
            else:
                response = f"Based on our conversation, I've written your diary for today:\n\n{diary_entry}\n\nYou can edit this diary entry or save it as is."
            
            self._add_conversation_message(
                session,
                role='assistant',
                content=response,
                intent='COMPOSE'
            )
            
            return response, True
            
        except Exception as e:
            self.logger.error(f"Error in compose phase: {e}")
            if session.language == 'zh':
                return "抱歉，生成日记时出现了问题。", False
            else:
                return "Sorry, there was an error generating your diary.", False
    
    def _handle_crisis_response(self, session: DiarySession, user_message: str) -> Tuple[str, bool]:
        """Handle responses when in crisis mode"""
        
        # Record user message
        self._add_conversation_message(
            session,
            role='user',
            content=user_message
        )
        
        if session.language == 'zh':
            response = "我理解你现在很困难。如果你愿意，我们可以明天再继续记录。请记得寻求支持。"
        else:
            response = "I understand you're going through a difficult time. We can continue journaling tomorrow if you'd like. Please remember to seek support."
        
        self._add_conversation_message(
            session,
            role='assistant',
            content=response,
            intent='CRISIS_FLOW'
        )
        
        return response, False
    
    def _add_conversation_message(self, 
                                 session: DiarySession,
                                 role: str,
                                 content: str,
                                 intent: Optional[str] = None,
                                 slot_updates: Optional[Dict] = None):
        """Add a conversation message to the database"""
        
        message = ConversationMessage(
            diary_session_id=session.id,
            role=role,
            content=content,
            intent=intent,
            slot_updates=slot_updates
        )
        
        self.db.add(message)
        self.db.commit()
    
    def update_final_diary(self, session: DiarySession, edited_content: str):
        """Update the final diary with user edits"""
        
        session.final_diary = edited_content
        self.db.commit()
    
    def get_session_by_id(self, session_id: int, user_id: int) -> Optional[DiarySession]:
        """Get diary session by ID for a specific user"""
        
        return self.db.query(DiarySession).filter(
            DiarySession.id == session_id,
            DiarySession.user_id == user_id
        ).first()
    
    def get_active_session(self, user_id: int) -> Optional[DiarySession]:
        """Get the active diary session for a user"""
        
        return self.db.query(DiarySession).filter(
            DiarySession.user_id == user_id,
            DiarySession.is_complete == False
        ).order_by(DiarySession.created_at.desc()).first()
    
    def get_conversation_history(self, session: DiarySession) -> List[Dict]:
        """Get full conversation history for a session"""
        
        messages = self.db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == session.id
        ).order_by(ConversationMessage.created_at).all()
        
        return [{
            'role': msg.role,
            'content': msg.content,
            'intent': msg.intent,
            'slot_updates': msg.slot_updates,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]