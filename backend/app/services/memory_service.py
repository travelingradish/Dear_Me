import logging
import re
import json
from datetime import datetime, timedelta, timezone
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

        # Memory type classifications for better temporal awareness
        self.factual_categories = {'personal_info', 'relationships'}  # Persistent facts
        self.temporal_categories = {'interests', 'challenges', 'goals', 'preferences'}  # Time-sensitive
        
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
                existing_memory.last_updated = datetime.now(timezone.utc)
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
            'recent_memories': len([m for m in memories if m.last_updated >= datetime.now(timezone.utc) - timedelta(days=7)])
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
                existing_memory.last_updated = datetime.now(timezone.utc)
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
            current_time = datetime.now(timezone.utc)  # Use timezone-aware UTC
            
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
            # For vague queries, be more strict about temporal relevance
            filtered_memories = self._filter_memories_by_context_type(all_memories[:limit * 3], conversation_type, current_time)
            # Additional temporal filter for vague queries - exclude memories older than 24 hours
            recent_memories = []
            for memory in filtered_memories:
                temporal_relevance = self._calculate_temporal_relevance_multiplier(memory, current_time)
                if temporal_relevance > 0.3:  # Only include memories less than ~24 hours old for vague queries
                    recent_memories.append(memory)
            return recent_memories[:limit]
        
        # Enhanced relevance scoring with improved temporal awareness
        # Higher scores = more relevant memories (fresher memories get higher multipliers)
        scored_memories = []
        context_lower = context.lower()
        context_words = set(context_lower.split())

        # Check for memory correction patterns first
        self.invalidate_outdated_memories(db_session, user_id, context)

        # Time-related keywords to identify temporal memories
        time_keywords = {'morning', 'afternoon', 'evening', 'night', 'wake', 'sleep', 'early', 'late', 'time', 'clock', 'schedule', 'routine'}
        current_time_keywords = {'now', 'currently', 'today', 'this morning', 'this afternoon', 'this evening', 'right now', 'at the moment'}

        # Define conversation intent keywords to understand context better
        mood_keywords = {'feel', 'feeling', 'mood', 'emotional', 'happy', 'sad', 'angry', 'excited', 'tired', 'stressed', 'calm', 'anxious'}
        activity_keywords = {'did', 'went', 'work', 'school', 'meeting', 'exercise', 'run', 'walk', 'eat', 'cook', 'watch', 'read', 'play', 'stretching', 'stretch', 'yoga', 'fitness', 'workout'}
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

            # Calculate temporal relevance multiplier (fresher = higher score)
            temporal_relevance = self._calculate_temporal_relevance_multiplier(memory, current_time)

            # Check if memory is time-specific (contains time references)
            memory_has_time_refs = any(word in memory_words for word in time_keywords)

            # TEMPORAL FILTERING: Skip old temporal memories unless highly relevant
            memory_type = self._classify_memory_type(memory)
            if memory_type == 'temporal' and temporal_relevance < 0.5:
                # For very old memories (relevance < 0.2), apply much stricter filtering
                if temporal_relevance < 0.2:
                    # Very old memories (>2 days) should almost never be included
                    # Only allow if conversation is SPECIFICALLY about that old event
                    word_overlap = len(context_words & memory_words)
                    # Require very high word overlap AND high confidence for very old memories
                    if word_overlap < 3 or memory.confidence_score < 0.9:
                        continue
                else:
                    # For moderately old memories (0.2-0.5 relevance), require some word overlap
                    word_overlap = len(context_words & memory_words)
                    if word_overlap < 2:  # Need at least 2 matching words for old memories
                        continue

            # ACTIVITY FILTER: Skip old activity memories in activity contexts
            if context_type == 'activity':
                is_activity_memory = any(word in memory.memory_value.lower() for word in
                                       ['watching', 'doing', 'activities', 'playing', 'working on'])
                if is_activity_memory and temporal_relevance < 0.1:
                    # Skip old activity memories (under 10% relevance) unless highly relevant
                    word_overlap = len(context_words & memory_words)
                    if word_overlap < 3:  # Need strong word overlap for very old activities
                        continue

            # 1. Direct word overlap (weighted by temporal relevance)
            word_overlap = len(context_words & memory_words)
            if word_overlap > 0:
                # More word overlap + fresher memory = higher relevance score
                relevance_score += word_overlap * 0.4 * temporal_relevance

            # 2. Enhanced category relevance based on context type
            category_bonus = 0
            if context_type == 'mood' and memory.category in ['challenges', 'personal_info']:
                category_bonus = 0.3
            elif context_type == 'activity' and memory.category == 'interests':
                category_bonus = 0.5
            elif context_type == 'relationship' and memory.category == 'relationships':
                category_bonus = 0.7  # Boost relationship relevance
            elif context_type == 'challenge' and memory.category in ['goals', 'challenges']:
                category_bonus = 0.5

            # Category bonus is also weighted by temporal relevance
            relevance_score += category_bonus * temporal_relevance

            # 3. Semantic relevance - check for related concepts
            if context_type == 'mood':
                emotion_indicators = ['feel', 'emotion', 'mood', 'happy', 'sad', 'stress', 'calm', 'love', 'hate', 'enjoy', 'like', 'dislike']
                if any(indicator in memory_content_lower for indicator in emotion_indicators):
                    relevance_score += 0.4 * temporal_relevance
            elif context_type == 'relationship':
                # Boost memories that mention relationship words
                if any(word in memory_content_lower for word in relationship_keywords):
                    relevance_score += 0.5 * temporal_relevance

            # 4. Enhanced cross-category irrelevance filtering
            if context_type == 'activity':
                # For activity context, heavily penalize unrelated memories
                if memory.category == 'personal_info' and word_overlap == 0:
                    relevance_score *= 0.1  # Much stricter penalty
                elif memory.category == 'interests' and word_overlap == 0:
                    # Check if it's actually related to the activity
                    activity_related = any(word in memory_content_lower for word in activity_keywords)
                    if not activity_related:
                        relevance_score *= 0.2
            elif context_type == 'relationship' and memory.category in ['interests', 'preferences']:
                relevance_score *= 0.4

            # Add strict filtering for completely unrelated content
            if word_overlap == 0 and category_bonus == 0:
                # No word overlap and no category relevance - likely irrelevant
                relevance_score *= 0.1

            # 5. Consider confidence score (weighted by temporal relevance)
            relevance_score += memory.confidence_score * 0.3 * temporal_relevance

            # 6. Boost very recent and high-confidence memories slightly
            if memory.last_updated:
                # Handle timezone-aware vs naive datetime comparison
                mem_time = memory.last_updated
                if mem_time.tzinfo is None:
                    mem_time = mem_time.replace(tzinfo=timezone.utc)
                curr_time = current_time if current_time.tzinfo else current_time.replace(tzinfo=timezone.utc)

                if (curr_time - mem_time).total_seconds() < 7200:  # 2 hours
                    relevance_score += 0.2

            # 7. FREQUENCY-BASED IMPORTANCE SCORING (NEW)
            # Memories mentioned 3+ times are clearly important to the user
            importance_boost = 0
            if memory.mention_count >= 5:
                importance_boost = 5.0  # Very important - mentioned 5+ times
                self.logger.debug(f"Very important memory (5+ mentions): {memory.memory_value[:50]}")
            elif memory.mention_count >= 3:
                importance_boost = 3.0  # Important - mentioned 3+ times
                self.logger.debug(f"Important memory (3+ mentions): {memory.memory_value[:50]}")

            relevance_score += importance_boost

            # INCREASED MINIMUM THRESHOLD for better filtering
            if relevance_score > 0.5:  # Higher threshold (was 0.2)
                scored_memories.append((memory, relevance_score))
        
        # Sort by relevance score and return top memories
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        relevant_memories = [memory for memory, score in scored_memories[:min(limit, 5)]]  # Cap at 5 memories max

        # If no relevant memories found, be very conservative with fallback
        if not relevant_memories:
            # Only return fallback memories if the context is very general
            if len(context_words) <= 2 or context_type == 'general':
                fallback_memories = []
                for memory in all_memories[:5]:  # Check fewer memories
                    if self._classify_memory_type(memory) == 'factual' and self._calculate_temporal_relevance_multiplier(memory, current_time) > 0.9:
                        fallback_memories.append(memory)
                        if len(fallback_memories) >= 1:  # Only 1 fallback memory
                            break
                return fallback_memories
            else:
                # For specific context, return empty if no relevant memories
                return []

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
                days_old = (datetime.now(timezone.utc) - memory.last_updated).days
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
        
        # Stricter memory limits to prevent overwhelming
        max_memories = 2 if len(context.split()) < 10 else 3  # Reduced from 3/5 to 2/3
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
        session_summary = f"Memory snapshot created at {datetime.now(timezone.utc)}"
        
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

    # NEW IMPROVED MEMORY METHODS

    def correct_memory(self, db: Session, user_id: int, old_value: str, new_value: str, category: str = None) -> bool:
        """Correct or update existing memory with new information"""
        try:
            # Find memories that contain the old value
            query = db.query(UserMemory).filter(
                UserMemory.user_id == user_id,
                UserMemory.is_active == True
            )

            if category:
                query = query.filter(UserMemory.category == category)

            # Find memories containing the old information
            memories_to_update = []
            for memory in query.all():
                if old_value.lower() in memory.memory_value.lower():
                    memories_to_update.append(memory)

            # Update or replace the memories
            for memory in memories_to_update:
                if category == 'relationships' or 'relationships' in memory.category:
                    # For relationships, update the memory value directly
                    memory.memory_value = memory.memory_value.replace(old_value, new_value)
                    memory.last_updated = datetime.now(timezone.utc)
                    memory.confidence_score = min(1.0, memory.confidence_score + 0.1)  # Boost confidence for corrected info
                    self.logger.info(f"Corrected relationship memory: {old_value} -> {new_value}")
                else:
                    # For other categories, mark as outdated and create new memory
                    memory.is_active = False

                    # Create new corrected memory
                    new_memory = UserMemory(
                        user_id=user_id,
                        category=memory.category,
                        memory_key=f"{memory.category}_{new_value.lower().replace(' ', '_')}",
                        memory_value=new_value,
                        confidence_score=0.9,  # High confidence for user-corrected information
                        source_type="user_correction"
                    )
                    db.add(new_memory)

            db.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error correcting memory: {e}")
            db.rollback()
            return False

    def invalidate_outdated_memories(self, db: Session, user_id: int, context: str) -> None:
        """Identify and invalidate memories that contradict current conversation"""
        try:
            # Look for explicit corrections in the conversation
            correction_patterns = [
                r"no.*(?:not|isn't|aren't|wasn't|weren't).*(\w+)",
                r"actually.*(?:is|are|was|were).*(\w+)",
                r"(?:my|the).*(?:is|are).*(\w+).*not.*(\w+)",
                r"(\w+)\s+is\s+my\s+(\w+)",  # "Pramod is my husband"
            ]

            context_lower = context.lower()

            # Check for relationship corrections specifically
            if any(word in context_lower for word in ['husband', 'wife', 'partner', 'friend', 'colleague', 'son', 'daughter']):
                # Extract relationship corrections
                import re
                for pattern in correction_patterns:
                    matches = re.findall(pattern, context_lower)
                    for match in matches:
                        if isinstance(match, tuple):
                            # Handle tuple matches (person, relationship)
                            if len(match) == 2:
                                person, relationship = match
                                self._update_relationship_memory(db, user_id, person, relationship)

        except Exception as e:
            self.logger.error(f"Error invalidating outdated memories: {e}")

    def _update_relationship_memory(self, db: Session, user_id: int, person: str, relationship: str) -> None:
        """Update or create relationship memory"""
        try:
            # Find existing memory for this person
            existing_memory = db.query(UserMemory).filter(
                UserMemory.user_id == user_id,
                UserMemory.category == 'relationships',
                UserMemory.memory_value.contains(person.title()),
                UserMemory.is_active == True
            ).first()

            new_memory_value = f"{person.title()} is my {relationship}"

            if existing_memory:
                # Update existing memory
                existing_memory.memory_value = new_memory_value
                existing_memory.last_updated = datetime.now(timezone.utc)
                existing_memory.confidence_score = 0.95  # Very high confidence for explicit corrections
            else:
                # Create new relationship memory
                new_memory = UserMemory(
                    user_id=user_id,
                    category='relationships',
                    memory_key=f"relationships_{person.lower()}_{relationship.lower()}",
                    memory_value=new_memory_value,
                    confidence_score=0.95,
                    source_type="conversation_correction"
                )
                db.add(new_memory)

            db.commit()
            self.logger.info(f"Updated relationship memory: {new_memory_value}")

        except Exception as e:
            self.logger.error(f"Error updating relationship memory: {e}")

    def _classify_memory_type(self, memory: UserMemory) -> str:
        """Classify memory as factual or temporal"""
        # First check content for strong temporal indicators (overrides category)
        temporal_indicators = [
            'today', 'yesterday', 'this morning', 'this afternoon', 'last week', 'recently',
            'went to', 'had lunch', 'had dinner', 'had breakfast', 'did', 'was doing', 'feeling', 'felt',
            'watching', 'doing', 'activities', 'playing', 'working on', 'currently',
            'visited', 'drove to', 'walked to', 'shopping', 'bought', 'ordered',
            '今天', '昨天', '早上', '下午', '上周', '最近', '去了', '吃了', '做了', '感觉', '正在'
        ]

        content_lower = memory.memory_value.lower()

        # Strong temporal indicators override category classification
        if any(indicator in content_lower for indicator in temporal_indicators):
            return 'temporal'

        # Category-based classification for non-temporal content
        if memory.category in self.factual_categories:
            return 'factual'
        elif memory.category in self.temporal_categories:
            return 'temporal'
        else:
            return 'factual'

    def _calculate_temporal_relevance_multiplier(self, memory: UserMemory, current_time: datetime) -> float:
        """
        Calculate how relevant a temporal memory is based on its age.

        Returns a multiplier between 0.01 and 1.0:
        - 1.0 = 100% relevant (very fresh memory)
        - 0.5 = 50% relevant (moderately old)
        - 0.01 = 1% relevant (very old, almost irrelevant)

        Fresher memories get HIGHER multipliers (more relevant)
        Older memories get LOWER multipliers (less relevant)
        """
        if not memory.last_updated:
            return 0.5  # Moderate relevance for memories without timestamps

        memory_type = self._classify_memory_type(memory)

        if memory_type == 'factual':
            return 1.0  # Factual memories remain fully relevant over time

        # Handle timezone-aware vs naive datetime comparison (for transition period)
        memory_time = memory.last_updated
        if memory_time.tzinfo is None:
            # Convert naive datetime to UTC-aware for comparison
            memory_time = memory_time.replace(tzinfo=timezone.utc)

        # Ensure current_time is timezone-aware
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # For temporal memories, calculate age-based relevance multiplier
        age_hours = (current_time - memory_time).total_seconds() / 3600

        # Activity memories are more time-sensitive than general temporal memories
        is_activity_memory = any(word in memory.memory_value.lower() for word in
                               ['watching', 'doing', 'activities', 'playing', 'working on'])

        # REVISED TEMPORAL DECAY CURVE - More user-friendly and less aggressive
        # User feedback: 1 day = critical, 2 days = high impact, 3+ mentions = important

        if age_hours < 24:  # 0-1 day (CRITICAL window)
            return 1.0  # 100% relevant - happened today/last 24 hours
        elif age_hours < 72:  # 1-3 days (HIGH IMPACT window)
            # Much gentler decay for 1-3 day old memories
            return 0.7 if is_activity_memory else 0.8  # 70-80% relevant
        elif age_hours < 168:  # 3-7 days (one week)
            # Still quite relevant for general memories
            return 0.4 if is_activity_memory else 0.6  # 40-60% relevant
        elif age_hours < 720:  # 7-30 days (one month)
            # Background context - still accessible
            return 0.2 if is_activity_memory else 0.3  # 20-30% relevant
        else:  # 30+ days
            # Archive tier - low but not zero relevance
            return 0.05 if is_activity_memory else 0.1  # 5-10% relevant

    def track_conversation_context(self, db: Session, user_id: int, session_id: int, context_updates: Dict[str, Any]) -> None:
        """Track conversation-specific context and corrections"""
        try:
            # Store conversation context in session structured_data
            session = db.query(DiarySession).filter(DiarySession.id == session_id).first()
            if session:
                if not session.structured_data:
                    session.structured_data = {}

                # Track memory corrections in this conversation
                if 'memory_corrections' not in session.structured_data:
                    session.structured_data['memory_corrections'] = {}

                # Update with new context
                session.structured_data['memory_corrections'].update(context_updates)
                session.last_updated = datetime.now(timezone.utc)

                db.commit()
                self.logger.info(f"Updated conversation context for session {session_id}")

        except Exception as e:
            self.logger.error(f"Error tracking conversation context: {e}")

    def get_conversation_context(self, db: Session, session_id: int) -> Dict[str, Any]:
        """Get conversation-specific context and corrections"""
        try:
            session = db.query(DiarySession).filter(DiarySession.id == session_id).first()
            if session and session.structured_data and 'memory_corrections' in session.structured_data:
                return session.structured_data['memory_corrections']
            return {}
        except Exception as e:
            self.logger.error(f"Error getting conversation context: {e}")
            return {}

    def get_relevant_memories_with_session_context(self, user_id: int, context: str, db_session: Session,
                                                  session_id: int = None, limit: int = 5) -> List[UserMemory]:
        """Enhanced memory retrieval with session-specific context awareness"""

        # Get base relevant memories
        relevant_memories = self.get_relevant_memories(user_id, context, db_session, limit)

        # Apply session-specific corrections if available
        if session_id:
            session_context = self.get_conversation_context(db_session, session_id)
            if session_context:
                # Filter out memories that have been corrected in this session
                filtered_memories = []
                for memory in relevant_memories:
                    should_include = True

                    # Check if this memory has been corrected in current session
                    for corrected_key, corrected_value in session_context.items():
                        if corrected_key.lower() in memory.memory_value.lower():
                            # This memory contains information that was corrected
                            if memory.category == 'relationships':
                                # For relationships, prefer session context over old memory
                                should_include = False
                                break

                    if should_include:
                        filtered_memories.append(memory)

                return filtered_memories

        return relevant_memories