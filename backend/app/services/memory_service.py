import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from app.models.models import User, UserMemory, MemorySnapshot, DiarySession, ConversationMessage
from app.core.database import SessionLocal

# Simple data class for memory objects returned by extraction
class ExtractedMemory:
    def __init__(self, category: str, content: str, confidence: float):
        self.category = category
        self.content = content
        self.confidence = confidence

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
                    r'i watch ([^.]+)',
                    r'([^.]+) is my passion',
                    r'my passion is ([^.]+)',
                    r'i am passionate about ([^.]+)'
                ],
                'keywords': ['love', 'enjoy', 'like', 'hate', 'dislike', 'hobby', 'play', 'watch', 'read', 'listen', 'passion', 'passionate']
            },
            'challenges': {
                'patterns': [
                    r'i struggle with ([^.]+)',
                    r'i have trouble ([^.]+)',
                    r'i\'m having trouble ([^.]+)',
                    r'([^.]+) is difficult for me',
                    r'([^.]+) is a daily battle',
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
                    r'i typically ([^.]+)',
                    r'i\'m a ([^.]+)',
                    r'i am a ([^.]+)',
                    r'i like waking up ([^.]+)'
                ],
                'keywords': ['prefer', 'usually', 'always', 'never', 'typically', 'favorite', 'routine', 'vegetarian', 'vegan']
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
        
        # Remove duplicates and very similar memories at extraction level
        deduplicated_memories = []
        
        for memory in extracted_memories:
            is_duplicate = False
            memory_words = set(memory['memory_value'].lower().split())
            
            for existing in deduplicated_memories:
                if (existing['category'] == memory['category'] and 
                    existing['memory_key'] == memory['memory_key']):
                    is_duplicate = True
                    break
                    
                # Check for content similarity within same category OR different categories (prevent cross-category duplicates)
                existing_words = set(existing['memory_value'].lower().split())
                overlap = len(memory_words & existing_words)
                total_unique = len(memory_words | existing_words)
                if total_unique > 0 and (overlap / total_unique) > 0.6:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated_memories.append(memory)
        
        return deduplicated_memories
    
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
    
    def get_relevant_memories_original(self, db: Session, user_id: int, context: str = "", categories: List[str] = None, limit: int = 10) -> List[UserMemory]:
        """Retrieve contextually relevant memories (original interface)"""
        # Use the enhanced method with parameter order adjustment
        relevant_memories = self.get_relevant_memories(user_id, context, db, limit)
        
        # Apply category filtering if specified
        if categories:
            relevant_memories = [m for m in relevant_memories if m.category in categories]
        
        return relevant_memories
    
    def format_memories_for_prompt(self, memories: List[UserMemory], language: str = "en", context: str = "") -> str:
        """Format memories into a contextually appropriate prompt string"""
        if not memories:
            return ""
        
        # Apply final filtering based on context to prevent irrelevant information
        filtered_memories = self._filter_memories_by_conversational_context(memories, context)
        
        if not filtered_memories:
            return ""
        
        if language == "zh":
            memory_text = "用户相关信息（请谨慎使用，仅在直接相关时引用）：\n"
        else:
            memory_text = "Relevant user context (use sparingly, only when directly relevant):\n"
        
        # Group memories by category
        categorized = {}
        for memory in filtered_memories:
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
        stored_memories = self.store_memories_internal(db, session.user_id, extracted_memories)
        
        # Get active memories for context
        active_memories = self.get_relevant_memories_original(db, session.user_id, full_conversation)
        
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
    
    # COMPATIBILITY METHODS FOR TESTS
    # These methods match the interface expected by the test suite
    
    def extract_memory_from_conversation(self, conversation: str, user_id: int) -> List[ExtractedMemory]:
        """Extract memories from conversation text - test-compatible interface"""
        extracted_data = self.extract_memories_from_text(conversation, user_id, "conversation")
        
        # Convert to ExtractedMemory objects expected by tests
        extracted_memories = []
        for data in extracted_data:
            memory = ExtractedMemory(
                category=data['category'],
                content=data['memory_value'],
                confidence=data['confidence_score']
            )
            extracted_memories.append(memory)
        
        return extracted_memories
    
    def store_memories(self, memories: List[ExtractedMemory], db_session: Session, user_id: int = None) -> List[UserMemory]:
        """Store extracted memories - test-compatible interface"""
        # Convert ExtractedMemory objects back to dict format for internal method
        memory_dicts = []
        for mem in memories:
            # Create a more specific memory key based on content
            content_words = mem.content.lower().split()[:3]  # First 3 words
            memory_key = f"{mem.category}_{'_'.join(content_words)}"
            
            memory_dicts.append({
                'category': mem.category,
                'memory_key': memory_key,
                'memory_value': mem.content,
                'confidence_score': mem.confidence,
                'source_type': 'conversation'
            })
        
        # Get user_id from parameter or try to extract from context
        if user_id is None:
            # Try to get user_id from the memories if available, otherwise default to 1
            user_id = getattr(memories[0], 'user_id', 1) if memories and hasattr(memories[0], 'user_id') else 1
            
        if memory_dicts:
            stored_memories = self.store_memories_internal(db_session, user_id, memory_dicts)
            # Add content property for test compatibility
            for memory in stored_memories:
                if not hasattr(memory, 'content'):
                    memory.content = memory.memory_value
                if not hasattr(memory, 'confidence'):
                    memory.confidence = memory.confidence_score
            return stored_memories
        return []
    
    def store_memories_internal(self, db: Session, user_id: int, extracted_memories: List[Dict[str, Any]]) -> List[UserMemory]:
        """Internal method that matches the original store_memories logic"""
        stored_memories = []
        
        for memory_data in extracted_memories:
            # First check for exact memory_key match
            existing_memory = db.query(UserMemory).filter(
                UserMemory.user_id == user_id,
                UserMemory.category == memory_data['category'],
                UserMemory.memory_key == memory_data['memory_key']
            ).first()
            
            # If no exact match, check for content similarity in same category
            if not existing_memory:
                similar_memories = db.query(UserMemory).filter(
                    UserMemory.user_id == user_id,
                    UserMemory.category == memory_data['category']
                ).all()
                
                new_content_words = set(memory_data['memory_value'].lower().split())
                for similar_memory in similar_memories:
                    existing_content_words = set(similar_memory.memory_value.lower().split())
                    # Check if content has significant overlap (>70% of words match)
                    overlap = len(new_content_words & existing_content_words)
                    total_unique = len(new_content_words | existing_content_words)
                    if total_unique > 0 and (overlap / total_unique) > 0.7:
                        existing_memory = similar_memory
                        break
            
            if existing_memory:
                # Update existing memory
                existing_memory.memory_value = memory_data['memory_value']
                existing_memory.confidence_score = min(1.0, existing_memory.confidence_score + 0.1)
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
    
    def get_relevant_memories(self, user_id: int, context: str, db_session: Session, limit: int = 10, current_time: datetime = None, conversation_type: str = "current") -> List[UserMemory]:
        """Get contextually relevant memories with improved relevance scoring"""
        if not current_time:
            current_time = datetime.now()  # Use local time instead of UTC
            
        query = db_session.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.is_active == True
        )
        
        # Get all memories for this user
        all_memories = query.order_by(
            UserMemory.confidence_score.desc(),
            UserMemory.last_updated.desc()
        ).all()
        
        # Add 'content' property for test compatibility
        for memory in all_memories:
            if not hasattr(memory, 'content'):
                memory.content = memory.memory_value
            if not hasattr(memory, 'confidence'):
                memory.confidence = memory.confidence_score
        
        # If no context provided, return recent high-confidence memories (but filtered)
        if not context or not context.strip():
            return self._filter_memories_by_context_type(all_memories[:limit * 2], conversation_type, current_time)[:limit]
        
        # Enhanced relevance scoring with time awareness
        scored_memories = []
        context_lower = context.lower()
        context_words = set(context_lower.split())
        
        # Time-related keywords to identify temporal memories
        time_keywords = {'morning', 'afternoon', 'evening', 'night', 'wake', 'sleep', 'early', 'late', 'time', 'clock', 'schedule', 'routine'}
        current_time_keywords = {'now', 'currently', 'today', 'this morning', 'this afternoon', 'this evening', 'right now', 'at the moment'}
        
        # Define conversation intent keywords to understand context better
        mood_keywords = {'feel', 'feeling', 'mood', 'emotional', 'happy', 'sad', 'angry', 'excited', 'tired', 'stressed', 'calm', 'anxious'}
        activity_keywords = {'did', 'went', 'work', 'school', 'meeting', 'exercise', 'run', 'walk', 'eat', 'cook', 'watch', 'read', 'play'}
        relationship_keywords = {'friend', 'family', 'partner', 'colleague', 'mom', 'dad', 'wife', 'husband', 'boyfriend', 'girlfriend', 'cat', 'dog', 'pet'}
        challenge_keywords = {'difficult', 'hard', 'problem', 'challenge', 'struggle', 'win', 'success', 'achievement', 'accomplish'}
        
        # Determine context type and time relevance
        context_type = 'general'
        is_current_time_query = any(word in context_words for word in current_time_keywords)
        has_time_context = any(word in context_words for word in time_keywords)
        
        if any(word in context_words for word in mood_keywords):
            context_type = 'mood'
        elif any(word in context_words for word in activity_keywords):
            context_type = 'activity'
        elif any(word in context_words for word in relationship_keywords):
            context_type = 'relationship'
        elif any(word in context_words for word in challenge_keywords):
            context_type = 'challenge'
        
        for memory in all_memories:
            relevance_score = 0
            memory_words = set(memory.memory_value.lower().split())
            memory_content_lower = memory.memory_value.lower()
            
            # Check if memory is time-specific (contains time references)
            memory_has_time_refs = any(word in memory_words for word in time_keywords)
            
            # TEMPORAL FILTERING: Skip time-specific memories for current conversations unless directly relevant
            if conversation_type == "current" and memory_has_time_refs and not has_time_context:
                # If this is a current conversation and memory mentions time but context doesn't, penalize heavily
                if is_current_time_query:
                    # Exception: if user is asking about current time, time memories might be relevant
                    pass  
                else:
                    # Skip memories about specific times (like wake-up times) when irrelevant
                    relevance_score -= 2.0  # Heavy penalty
            
            # 1. Direct word overlap (reduced weight)
            word_overlap = len(context_words & memory_words)
            if word_overlap > 0:
                relevance_score += word_overlap * 0.3
            
            # 2. Category relevance based on context type
            category_bonus = 0
            if context_type == 'mood' and memory.category == 'personal_info':
                category_bonus = 0.2
            elif context_type == 'activity' and memory.category == 'interests':
                category_bonus = 0.4
            elif context_type == 'relationship' and memory.category == 'relationships':
                category_bonus = 0.5
            elif context_type == 'challenge' and memory.category in ['goals', 'challenges']:
                category_bonus = 0.4
            
            relevance_score += category_bonus
            
            # 3. Semantic relevance - check for related concepts
            if context_type == 'mood':
                # For mood contexts, prefer emotional or personal memories
                emotion_indicators = ['feel', 'emotion', 'mood', 'happy', 'sad', 'stress', 'calm', 'love', 'hate', 'enjoy', 'like', 'dislike']
                if any(indicator in memory_content_lower for indicator in emotion_indicators):
                    relevance_score += 0.3
            
            # 4. Penalize potentially irrelevant memories
            # If context is about today's activities but memory is about personal info, reduce relevance
            if context_type == 'activity' and memory.category == 'personal_info':
                relevance_score *= 0.5
            
            # 5. Boost recent memories if they're somewhat relevant
            if relevance_score > 0 and memory.last_updated:
                days_old = (current_time - memory.last_updated).days
                if days_old < 7:  # Recent memories get slight boost
                    relevance_score += 0.1
            
            # 6. Consider confidence score
            relevance_score += memory.confidence_score * 0.2
            
            # Only include memories with meaningful relevance
            if relevance_score > 0.2:  # Minimum threshold
                scored_memories.append((memory, relevance_score))
        
        # Sort by relevance score and return top memories
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        relevant_memories = [memory for memory, score in scored_memories[:limit]]
        
        # If no relevant memories found, return a small set of high-confidence recent memories
        if not relevant_memories:
            return all_memories[:min(3, limit)]
        
        return relevant_memories
    
    def _filter_memories_by_context_type(self, memories: List[UserMemory], conversation_type: str, current_time: datetime) -> List[UserMemory]:
        """Filter memories based on conversation context type"""
        if not memories:
            return memories
            
        filtered_memories = []
        
        for memory in memories:
            include_memory = True
            memory_content_lower = memory.memory_value.lower()
            
            # Filter out time-specific memories for current conversations
            if conversation_type == "current":
                time_indicators = ['wake up at', 'get up at', 'sleep at', 'bedtime', 'morning routine', 'evening routine', '早上', '晚上', '睡觉时间']
                if any(indicator in memory_content_lower for indicator in time_indicators):
                    # Only include if it's recent (within 24 hours) or very high confidence
                    if memory.last_updated and current_time:
                        hours_old = (current_time - memory.last_updated).total_seconds() / 3600
                        if hours_old > 24 and memory.confidence_score < 0.9:
                            include_memory = False
            
            if include_memory:
                filtered_memories.append(memory)
        
        return filtered_memories
    
    def _filter_memories_by_conversational_context(self, memories: List[UserMemory], context: str) -> List[UserMemory]:
        """Apply final context-aware filtering to prevent inappropriate memory quotations"""
        if not context or not memories:
            return memories
        
        context_lower = context.lower()
        filtered_memories = []
        
        # Define contexts where certain memory types should be avoided
        casual_greeting_patterns = ['hello', 'hi', 'how are you', 'good morning', 'good evening', '你好', '早上好', '晚上好']
        simple_activity_patterns = ['today i', 'went to', 'had lunch', 'at work', 'in meeting', '今天我', '去了', '吃了午饭', '在工作']
        mood_only_patterns = ['feeling', 'feel', 'mood', 'tired', 'happy', 'sad', '感觉', '心情', '累了', '开心', '难过']
        
        is_casual_greeting = any(pattern in context_lower for pattern in casual_greeting_patterns)
        is_simple_activity = any(pattern in context_lower for pattern in simple_activity_patterns)
        is_mood_only = any(pattern in context_lower for pattern in mood_only_patterns) and len(context.split()) < 8
        
        for memory in memories:
            should_include = True
            
            # Skip personal info for casual greetings
            if is_casual_greeting and memory.category == 'personal_info':
                should_include = False
            
            # Skip relationship info for simple activity updates unless relationships are mentioned
            if (is_simple_activity and memory.category == 'relationships' and 
                not any(word in context_lower for word in ['friend', 'family', 'partner', 'with', '朋友', '家人', '伙伴', '和'])):
                should_include = False
            
            # For mood-only contexts, limit to recent emotional memories
            if is_mood_only and memory.category not in ['personal_info'] and memory.last_updated:
                days_old = (datetime.utcnow() - memory.last_updated).days
                if days_old > 30:  # Skip older memories for simple mood updates
                    should_include = False
            
            # Skip very specific memories that don't relate to current context
            memory_words = set(memory.memory_value.lower().split())
            context_words = set(context_lower.split())
            
            # If memory is very specific but has no word overlap with context, skip it
            specific_indicators = ['named', 'called', 'lives in', 'works at', 'studies', 'born in']
            is_specific_memory = any(indicator in memory.memory_value.lower() for indicator in specific_indicators)
            has_context_overlap = len(memory_words & context_words) > 0
            
            if is_specific_memory and not has_context_overlap and len(context_words) > 3:
                should_include = False
            
            # Always include memories that have direct relevance to current conversation
            direct_relevance_score = len(memory_words & context_words) / max(len(context_words), 1)
            if direct_relevance_score > 0.3:  # Strong overlap
                should_include = True
            
            if should_include:
                filtered_memories.append(memory)
        
        # Limit the number of memories to prevent overwhelming the prompt
        max_memories = 3 if len(context.split()) < 10 else 5
        return filtered_memories[:max_memories]
    
    def create_memory_snapshot(self, user_id: int, db_session: Session, diary_session_id: Optional[int] = None) -> MemorySnapshot:
        """Create memory snapshot - test-compatible interface"""
        # Get current memories for this user
        memories = db_session.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.is_active == True
        ).all()
        
        # Create snapshot data
        extracted_memories = []  # Empty for this test interface
        session_summary = f"Memory snapshot created at {datetime.utcnow()}"
        
        # Create the snapshot manually instead of calling parent method
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
            } for mem in memories],
            session_summary=session_summary
        )
        
        db_session.add(snapshot)
        db_session.commit()
        return snapshot