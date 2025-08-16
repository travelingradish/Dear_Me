import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from models import User, UserMemory, MemorySnapshot, DiarySession, ConversationMessage
from database import SessionLocal

class MemoryService:
    """Service for managing user memories - extraction, storage, and retrieval"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Memory categories and their patterns
        self.memory_categories = {
            'personal_info': {
                'patterns': [
                    r'my name is (\w+)',
                    r'i am (\d+) years old',
                    r'i live in ([^.]+)',
                    r'i work as a ([^.]+)',
                    r'i am a ([^.]+)',
                    r'my job is ([^.]+)',
                    r'i study ([^.]+)',
                    r'i am from ([^.]+)'
                ],
                'keywords': ['name', 'age', 'live', 'work', 'job', 'study', 'from', 'hometown']
            },
            'relationships': {
                'patterns': [
                    r'my (\w+) is (\w+)',  # my wife is Sarah
                    r'i have a (\w+) named (\w+)',  # i have a cat named Whiskers
                    r'my (\w+) and i ([^.]+)',  # my partner and I went out
                    r'(\w+) and i ([^.]+)'  # John and I had lunch
                ],
                'keywords': ['wife', 'husband', 'partner', 'boyfriend', 'girlfriend', 'cat', 'dog', 'pet', 'mom', 'dad', 'mother', 'father', 'friend', 'colleague']
            },
            'interests': {
                'patterns': [
                    r'i love ([^.]+)',
                    r'i enjoy ([^.]+)',
                    r'i like ([^.]+)',
                    r'i hate ([^.]+)',
                    r'i dislike ([^.]+)',
                    r'i play ([^.]+)',
                    r'i watch ([^.]+)'
                ],
                'keywords': ['love', 'enjoy', 'like', 'hate', 'dislike', 'hobby', 'play', 'watch', 'read', 'listen']
            },
            'challenges': {
                'patterns': [
                    r'i struggle with ([^.]+)',
                    r'i have trouble ([^.]+)',
                    r'([^.]+) is difficult for me',
                    r'i worry about ([^.]+)',
                    r'i am stressed about ([^.]+)'
                ],
                'keywords': ['struggle', 'trouble', 'difficult', 'worry', 'stressed', 'anxiety', 'depression', 'problem']
            },
            'goals': {
                'patterns': [
                    r'i want to ([^.]+)',
                    r'i plan to ([^.]+)',
                    r'i hope to ([^.]+)',
                    r'my goal is ([^.]+)',
                    r'i am trying to ([^.]+)'
                ],
                'keywords': ['want', 'plan', 'hope', 'goal', 'trying', 'dream', 'aspire', 'wish']
            },
            'preferences': {
                'patterns': [
                    r'i prefer ([^.]+)',
                    r'i usually ([^.]+)',
                    r'i always ([^.]+)',
                    r'i never ([^.]+)',
                    r'i typically ([^.]+)'
                ],
                'keywords': ['prefer', 'usually', 'always', 'never', 'typically', 'favorite', 'routine']
            }
        }
    
    def extract_memories_from_text(self, text: str, user_id: int, source_type: str = "conversation") -> List[Dict[str, Any]]:
        """Extract potential memories from text using pattern matching and keyword detection"""
        text_lower = text.lower()
        extracted_memories = []
        
        # Process each category
        for category, config in self.memory_categories.items():
            # Pattern-based extraction
            for pattern in config['patterns']:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        memory_key = f"{category}_{match[0]}".replace(' ', '_')
                        memory_value = ' '.join(match)
                    else:
                        memory_key = f"{category}_general"
                        memory_value = match
                    
                    extracted_memories.append({
                        'category': category,
                        'memory_key': memory_key,
                        'memory_value': memory_value.strip(),
                        'confidence_score': 0.8,  # Pattern-based extraction is fairly reliable
                        'source_type': source_type
                    })
            
            # Keyword-based extraction (lower confidence)
            for keyword in config['keywords']:
                if keyword in text_lower:
                    # Find sentences containing the keyword
                    sentences = re.split(r'[.!?]+', text)
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            memory_key = f"{category}_{keyword}"
                            extracted_memories.append({
                                'category': category,
                                'memory_key': memory_key,
                                'memory_value': sentence.strip(),
                                'confidence_score': 0.6,  # Keyword-based is less reliable
                                'source_type': source_type
                            })
        
        return extracted_memories
    
    def store_memories(self, db: Session, user_id: int, extracted_memories: List[Dict[str, Any]]) -> List[UserMemory]:
        """Store extracted memories in database, handling duplicates and updates"""
        stored_memories = []
        
        for memory_data in extracted_memories:
            # Check if similar memory already exists
            existing_memory = db.query(UserMemory).filter(
                UserMemory.user_id == user_id,
                UserMemory.category == memory_data['category'],
                UserMemory.memory_key == memory_data['memory_key']
            ).first()
            
            if existing_memory:
                # Update existing memory
                existing_memory.memory_value = memory_data['memory_value']
                existing_memory.confidence_score = min(1.0, existing_memory.confidence_score + 0.1)  # Increase confidence
                existing_memory.last_updated = datetime.utcnow()
                existing_memory.mention_count += 1
                stored_memories.append(existing_memory)
            else:
                # Create new memory
                new_memory = UserMemory(
                    user_id=user_id,
                    category=memory_data['category'],
                    memory_key=memory_data['memory_key'],
                    memory_value=memory_data['memory_value'],
                    confidence_score=memory_data['confidence_score'],
                    source_type=memory_data['source_type']
                )
                db.add(new_memory)
                stored_memories.append(new_memory)
        
        db.commit()
        return stored_memories
    
    def get_relevant_memories(self, db: Session, user_id: int, context: str = "", categories: List[str] = None, limit: int = 10) -> List[UserMemory]:
        """Retrieve relevant memories for a given context"""
        query = db.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.is_active == True
        )
        
        if categories:
            query = query.filter(UserMemory.category.in_(categories))
        
        # Order by confidence and recency
        memories = query.order_by(
            UserMemory.confidence_score.desc(),
            UserMemory.last_updated.desc()
        ).limit(limit).all()
        
        # If context is provided, try to filter relevant ones
        if context and memories:
            context_lower = context.lower()
            relevant_memories = []
            
            for memory in memories:
                # Simple relevance check - if memory content appears in context
                if any(word in context_lower for word in memory.memory_value.lower().split()):
                    relevant_memories.append(memory)
            
            # If we found relevant ones, return them, otherwise return all
            return relevant_memories[:limit] if relevant_memories else memories[:limit//2]
        
        return memories
    
    def format_memories_for_prompt(self, memories: List[UserMemory], language: str = "en") -> str:
        """Format memories into a prompt-friendly string"""
        if not memories:
            return ""
        
        if language == "zh":
            memory_text = "关于用户的记忆：\n"
        else:
            memory_text = "About the user:\n"
        
        # Group memories by category
        categorized = {}
        for memory in memories:
            if memory.category not in categorized:
                categorized[memory.category] = []
            categorized[memory.category].append(memory)
        
        category_names = {
            'personal_info': '个人信息' if language == 'zh' else 'Personal Information',
            'relationships': '人际关系' if language == 'zh' else 'Relationships', 
            'interests': '兴趣爱好' if language == 'zh' else 'Interests',
            'challenges': '挑战困难' if language == 'zh' else 'Challenges',
            'goals': '目标计划' if language == 'zh' else 'Goals',
            'preferences': '偏好习惯' if language == 'zh' else 'Preferences'
        }
        
        for category, cat_memories in categorized.items():
            category_title = category_names.get(category, category.replace('_', ' ').title())
            memory_text += f"- {category_title}: "
            
            memory_values = [mem.memory_value for mem in cat_memories[:3]]  # Limit per category
            memory_text += "; ".join(memory_values) + "\n"
        
        return memory_text
    
    def create_memory_snapshot(self, db: Session, user_id: int, diary_session_id: Optional[int], 
                              extracted_memories: List[Dict[str, Any]], active_memories: List[UserMemory], 
                              session_summary: str) -> MemorySnapshot:
        """Create a snapshot of memory state for this session"""
        snapshot = MemorySnapshot(
            user_id=user_id,
            diary_session_id=diary_session_id,
            extracted_memories=extracted_memories,
            memory_context=[{
                'id': mem.id,
                'category': mem.category,
                'memory_key': mem.memory_key,
                'memory_value': mem.memory_value,
                'confidence_score': mem.confidence_score
            } for mem in active_memories],
            session_summary=session_summary
        )
        
        db.add(snapshot)
        db.commit()
        return snapshot
    
    def process_diary_session_memories(self, db: Session, diary_session_id: int) -> Dict[str, Any]:
        """Process memories from a completed diary session"""
        session = db.query(DiarySession).filter(DiarySession.id == diary_session_id).first()
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        # Gather all conversation text
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == diary_session_id
        ).all()
        
        user_messages = [msg.content for msg in messages if msg.role == 'user']
        full_conversation = ' '.join(user_messages)
        
        # Add structured data content
        if session.structured_data:
            for key, value in session.structured_data.items():
                if value:
                    full_conversation += f" {value}"
        
        # Extract memories
        extracted_memories = self.extract_memories_from_text(
            full_conversation, session.user_id, "diary_session"
        )
        
        # Store memories
        stored_memories = self.store_memories(db, session.user_id, extracted_memories)
        
        # Get active memories for context
        active_memories = self.get_relevant_memories(db, session.user_id, full_conversation)
        
        # Create memory snapshot
        session_summary = f"Diary session from {session.created_at.date()}: {len(user_messages)} messages, extracted {len(extracted_memories)} memories"
        snapshot = self.create_memory_snapshot(
            db, session.user_id, diary_session_id, extracted_memories, 
            active_memories, session_summary
        )
        
        return {
            'success': True,
            'extracted_memories_count': len(extracted_memories),
            'stored_memories_count': len(stored_memories),
            'snapshot_id': snapshot.id
        }
    
    def get_user_memory_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get a comprehensive summary of user's memories"""
        memories = db.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.is_active == True
        ).all()
        
        summary = {
            'total_memories': len(memories),
            'by_category': {},
            'high_confidence': len([m for m in memories if m.confidence_score >= 0.8]),
            'recent_memories': len([m for m in memories if m.last_updated >= datetime.utcnow() - timedelta(days=7)])
        }
        
        for memory in memories:
            if memory.category not in summary['by_category']:
                summary['by_category'][memory.category] = 0
            summary['by_category'][memory.category] += 1
        
        return summary