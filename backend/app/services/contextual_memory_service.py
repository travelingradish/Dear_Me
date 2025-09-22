"""
Contextual Memory Service for Deep Agent Integration

This service enhances the existing MemoryService with sophisticated contextual
retrieval and follow-up question generation based on memory patterns and user history.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
import json
import logging
from sqlalchemy.orm import Session

from app.models.models import User, UserMemory, DiarySession, ConversationMessage
from app.services.memory_service import MemoryService


class MemoryInsight:
    """Represents an insight derived from memory analysis"""

    def __init__(self, memory_id: int, insight_type: str, content: str, confidence: float, follow_up_question: str = None):
        self.memory_id = memory_id
        self.insight_type = insight_type  # 'pattern', 'gap', 'evolution', 'contradiction'
        self.content = content
        self.confidence = confidence
        self.follow_up_question = follow_up_question


class ContextualMemoryService(MemoryService):
    """Enhanced memory service with contextual analysis and follow-up generation"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_contextual_memories_with_insights(self,
                                            user_id: int,
                                            current_message: str,
                                            db: Session,
                                            conversation_history: List[Dict[str, str]] = None,
                                            limit: int = 10) -> Dict[str, Any]:
        """
        Get memories with rich contextual insights and follow-up opportunities

        Returns:
            Dict containing memories, insights, and suggested follow-up questions
        """

        # Get base relevant memories
        relevant_memories = self.get_relevant_memories(
            user_id=user_id,
            context=current_message,
            db_session=db,
            limit=limit * 2  # Get more to filter and rank
        )

        # Analyze memories for patterns and insights
        insights = self._analyze_memory_patterns(relevant_memories, current_message, conversation_history)

        # Generate contextual follow-up questions
        follow_up_questions = self._generate_contextual_follow_ups(
            relevant_memories, current_message, insights, conversation_history
        )

        # Rank memories by contextual relevance
        ranked_memories = self._rank_memories_by_context(
            relevant_memories, current_message, insights
        )[:limit]

        # Identify memory gaps that could guide conversation
        memory_gaps = self._identify_memory_gaps(user_id, db, current_message)

        return {
            "memories": [self._serialize_memory_with_context(mem, insights) for mem in ranked_memories],
            "insights": [self._serialize_insight(insight) for insight in insights],
            "follow_up_questions": follow_up_questions,
            "memory_gaps": memory_gaps,
            "context_summary": self._generate_context_summary(ranked_memories, insights)
        }

    def _analyze_memory_patterns(self,
                                memories: List[UserMemory],
                                current_message: str,
                                conversation_history: List[Dict[str, str]] = None) -> List[MemoryInsight]:
        """Analyze memories for patterns, evolution, and contradictions"""

        insights = []
        current_message_lower = current_message.lower()

        # Group memories by category for pattern analysis
        categorized_memories = {}
        for memory in memories:
            if memory.category not in categorized_memories:
                categorized_memories[memory.category] = []
            categorized_memories[memory.category].append(memory)

        # Pattern analysis by category
        for category, cat_memories in categorized_memories.items():
            # Time-based evolution analysis
            if len(cat_memories) >= 2:
                evolution_insight = self._analyze_memory_evolution(cat_memories, category)
                if evolution_insight:
                    insights.append(evolution_insight)

            # Contradiction detection
            contradiction_insight = self._detect_memory_contradictions(cat_memories, category)
            if contradiction_insight:
                insights.append(contradiction_insight)

            # Frequency pattern analysis
            if category in ['challenges', 'goals', 'interests']:
                frequency_insight = self._analyze_mention_frequency(cat_memories, category, current_message)
                if frequency_insight:
                    insights.append(frequency_insight)

        # Cross-category relationship insights
        relationship_insights = self._analyze_cross_category_relationships(categorized_memories, current_message)
        insights.extend(relationship_insights)

        return insights

    def _analyze_memory_evolution(self, memories: List[UserMemory], category: str) -> Optional[MemoryInsight]:
        """Analyze how memories in a category have evolved over time"""

        if len(memories) < 2:
            return None

        # Sort by last updated to see evolution
        sorted_memories = sorted(memories, key=lambda m: m.last_updated or datetime.min)

        # Look for evolution patterns
        if category == 'challenges':
            # Check if challenges are being resolved or getting worse
            recent_memory = sorted_memories[-1]
            older_memory = sorted_memories[0]

            # Simple keyword analysis for improvement/worsening
            improvement_keywords = ['better', 'easier', 'improving', 'resolved', 'overcome']
            worsening_keywords = ['worse', 'harder', 'struggling', 'difficult']

            recent_content = recent_memory.memory_value.lower()

            if any(keyword in recent_content for keyword in improvement_keywords):
                return MemoryInsight(
                    memory_id=recent_memory.id,
                    insight_type='evolution',
                    content=f"User shows improvement in {category}: {recent_memory.memory_value}",
                    confidence=0.7,
                    follow_up_question="How do you feel about the progress you've made with this challenge?"
                )
            elif any(keyword in recent_content for keyword in worsening_keywords):
                return MemoryInsight(
                    memory_id=recent_memory.id,
                    insight_type='evolution',
                    content=f"User may be struggling more with {category}",
                    confidence=0.6,
                    follow_up_question="Would you like to talk about what's making this more difficult lately?"
                )

        elif category == 'goals':
            # Check for goal progression
            recent_memory = sorted_memories[-1]
            progress_keywords = ['achieved', 'completed', 'closer', 'progress', 'working towards']

            if any(keyword in recent_memory.memory_value.lower() for keyword in progress_keywords):
                return MemoryInsight(
                    memory_id=recent_memory.id,
                    insight_type='evolution',
                    content=f"User shows goal progression: {recent_memory.memory_value}",
                    confidence=0.8,
                    follow_up_question="What steps have been most helpful in working towards this goal?"
                )

        return None

    def _detect_memory_contradictions(self, memories: List[UserMemory], category: str) -> Optional[MemoryInsight]:
        """Detect contradictions within memory categories"""

        if len(memories) < 2:
            return None

        # Look for contradictory statements
        contradiction_pairs = [
            (['love', 'enjoy', 'like'], ['hate', 'dislike', 'can\'t stand']),
            (['easy', 'simple', 'no problem'], ['difficult', 'hard', 'struggle']),
            (['always', 'every day', 'constantly'], ['never', 'rarely', 'seldom'])
        ]

        for memory1 in memories:
            for memory2 in memories:
                if memory1.id >= memory2.id:  # Avoid duplicate comparisons
                    continue

                content1 = memory1.memory_value.lower()
                content2 = memory2.memory_value.lower()

                for positive_words, negative_words in contradiction_pairs:
                    has_positive_1 = any(word in content1 for word in positive_words)
                    has_negative_1 = any(word in content1 for word in negative_words)
                    has_positive_2 = any(word in content2 for word in positive_words)
                    has_negative_2 = any(word in content2 for word in negative_words)

                    if (has_positive_1 and has_negative_2) or (has_negative_1 and has_positive_2):
                        return MemoryInsight(
                            memory_id=memory2.id,  # More recent memory
                            insight_type='contradiction',
                            content=f"Potential change in perspective about {category}",
                            confidence=0.6,
                            follow_up_question="I notice your feelings about this might have changed. How do you feel about it now?"
                        )

        return None

    def _analyze_mention_frequency(self, memories: List[UserMemory], category: str, current_message: str) -> Optional[MemoryInsight]:
        """Analyze how frequently certain topics are mentioned"""

        # Count mentions of memories that are highly confident and frequently updated
        frequent_memories = [m for m in memories if m.mention_count > 2 and m.confidence_score > 0.7]

        if frequent_memories:
            most_frequent = max(frequent_memories, key=lambda m: m.mention_count)

            # Check if current message relates to this frequent topic
            memory_words = set(most_frequent.memory_value.lower().split())
            message_words = set(current_message.lower().split())
            overlap = len(memory_words & message_words)

            if overlap > 0:
                return MemoryInsight(
                    memory_id=most_frequent.id,
                    insight_type='pattern',
                    content=f"Recurring theme in {category}: {most_frequent.memory_value}",
                    confidence=0.8,
                    follow_up_question="This seems to be something important to you. How has it been affecting you lately?"
                )

        return None

    def _analyze_cross_category_relationships(self, categorized_memories: Dict[str, List[UserMemory]], current_message: str) -> List[MemoryInsight]:
        """Find relationships between different memory categories"""

        insights = []

        # Relationship between challenges and goals
        if 'challenges' in categorized_memories and 'goals' in categorized_memories:
            challenges = categorized_memories['challenges']
            goals = categorized_memories['goals']

            for challenge in challenges:
                for goal in goals:
                    # Look for related concepts
                    challenge_words = set(challenge.memory_value.lower().split())
                    goal_words = set(goal.memory_value.lower().split())
                    overlap = len(challenge_words & goal_words)

                    if overlap >= 2:  # Significant word overlap
                        insights.append(MemoryInsight(
                            memory_id=goal.id,
                            insight_type='pattern',
                            content=f"Goal may be related to overcoming challenge: {challenge.memory_value}",
                            confidence=0.7,
                            follow_up_question="How is working towards this goal helping you with that challenge?"
                        ))

        # Relationship between interests and mood/challenges
        if 'interests' in categorized_memories and 'challenges' in categorized_memories:
            interests = categorized_memories['interests']
            challenges = categorized_memories['challenges']

            for interest in interests:
                if 'enjoy' in interest.memory_value.lower() or 'love' in interest.memory_value.lower():
                    insights.append(MemoryInsight(
                        memory_id=interest.id,
                        insight_type='pattern',
                        content=f"Positive interest that could help with challenges: {interest.memory_value}",
                        confidence=0.6,
                        follow_up_question="Have you been able to spend time on this lately? How does it make you feel?"
                    ))

        return insights

    def _generate_contextual_follow_ups(self,
                                       memories: List[UserMemory],
                                       current_message: str,
                                       insights: List[MemoryInsight],
                                       conversation_history: List[Dict[str, str]] = None) -> List[str]:
        """Generate contextual follow-up questions based on memories and insights"""

        follow_ups = []
        current_message_lower = current_message.lower()

        # From insights
        for insight in insights:
            if insight.follow_up_question and insight.confidence > 0.6:
                follow_ups.append(insight.follow_up_question)

        # From memory categories present
        categories_present = set(memory.category for memory in memories)

        if 'relationships' in categories_present:
            relationship_memories = [m for m in memories if m.category == 'relationships']
            for rel_memory in relationship_memories[:2]:
                if any(word in current_message_lower for word in ['friend', 'family', 'partner', 'work']):
                    follow_ups.append("How are things with them lately?")
                    break

        if 'challenges' in categories_present and any(word in current_message_lower for word in ['difficult', 'hard', 'problem']):
            follow_ups.append("Is this similar to challenges you've faced before?")

        if 'goals' in categories_present and any(word in current_message_lower for word in ['want', 'plan', 'hope']):
            follow_ups.append("How does this relate to what you're working towards?")

        # Emotional context follow-ups
        if any(word in current_message_lower for word in ['tired', 'stressed', 'overwhelmed']):
            follow_ups.append("What usually helps you feel better when you're feeling this way?")

        if any(word in current_message_lower for word in ['happy', 'excited', 'good']):
            follow_ups.append("What do you think contributed to feeling this way?")

        # Remove duplicates and limit
        unique_follow_ups = list(dict.fromkeys(follow_ups))  # Preserves order while removing duplicates
        return unique_follow_ups[:5]

    def _identify_memory_gaps(self, user_id: int, db: Session, current_message: str) -> List[Dict[str, Any]]:
        """Identify gaps in user memory that could guide conversation"""

        gaps = []

        # Check which categories are missing or sparse
        all_memories = db.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.is_active == True
        ).all()

        category_counts = {}
        for memory in all_memories:
            category_counts[memory.category] = category_counts.get(memory.category, 0) + 1

        # Expected categories and their importance
        expected_categories = {
            'personal_info': {'min_expected': 2, 'importance': 'medium'},
            'relationships': {'min_expected': 1, 'importance': 'high'},
            'interests': {'min_expected': 2, 'importance': 'high'},
            'goals': {'min_expected': 1, 'importance': 'high'},
            'challenges': {'min_expected': 1, 'importance': 'medium'},
            'preferences': {'min_expected': 1, 'importance': 'low'}
        }

        for category, config in expected_categories.items():
            count = category_counts.get(category, 0)
            if count < config['min_expected']:
                gaps.append({
                    'category': category,
                    'current_count': count,
                    'importance': config['importance'],
                    'suggested_question': self._generate_gap_filling_question(category, current_message)
                })

        # Sort by importance
        importance_order = {'high': 3, 'medium': 2, 'low': 1}
        gaps.sort(key=lambda x: importance_order[x['importance']], reverse=True)

        return gaps[:3]  # Return top 3 gaps

    def _generate_gap_filling_question(self, category: str, current_message: str) -> str:
        """Generate questions to fill memory gaps"""

        gap_questions = {
            'relationships': [
                "Who are the most important people in your life?",
                "Tell me about your family or close friends.",
                "How do you usually spend time with people you care about?"
            ],
            'interests': [
                "What do you enjoy doing in your free time?",
                "What activities make you feel energized or happy?",
                "Is there something you're passionate about?"
            ],
            'goals': [
                "What are you working towards right now?",
                "Is there something you're hoping to achieve?",
                "What would you like to be different in your life?"
            ],
            'challenges': [
                "What's been challenging for you lately?",
                "Is there anything you're struggling with?",
                "What obstacles are you facing right now?"
            ],
            'preferences': [
                "What kind of environment do you prefer?",
                "How do you like to start your day?",
                "What are your favorite ways to relax?"
            ],
            'personal_info': [
                "Tell me a bit about yourself.",
                "What's your typical day like?",
                "Where do you live? Do you like it there?"
            ]
        }

        questions = gap_questions.get(category, ["Tell me more about yourself."])

        # Choose question based on current message context if possible
        current_message_lower = current_message.lower()

        if category == 'relationships' and any(word in current_message_lower for word in ['lonely', 'alone']):
            return "Do you have people you can talk to when you're feeling this way?"

        if category == 'interests' and 'bored' in current_message_lower:
            return "What usually helps when you're feeling bored? What do you enjoy doing?"

        return questions[0]  # Default to first question

    def _rank_memories_by_context(self, memories: List[UserMemory], current_message: str, insights: List[MemoryInsight]) -> List[UserMemory]:
        """Rank memories by contextual relevance including insights"""

        scored_memories = []
        current_words = set(current_message.lower().split())

        # Get insight memory IDs for boosting
        insight_memory_ids = {insight.memory_id for insight in insights if insight.confidence > 0.6}

        for memory in memories:
            score = 0

            # Base relevance score
            memory_words = set(memory.memory_value.lower().split())
            word_overlap = len(current_words & memory_words)
            score += word_overlap * 2

            # Confidence boost
            score += memory.confidence_score * 1.5

            # Recency boost
            if memory.last_updated:
                days_old = (datetime.utcnow() - memory.last_updated).days
                if days_old < 7:
                    score += 3
                elif days_old < 30:
                    score += 1

            # Insight boost
            if memory.id in insight_memory_ids:
                score += 5

            # Category relevance based on current message
            if memory.category == 'challenges' and any(word in current_message.lower() for word in ['difficult', 'hard', 'problem', 'struggle']):
                score += 3
            elif memory.category == 'relationships' and any(word in current_message.lower() for word in ['friend', 'family', 'partner', 'with']):
                score += 3
            elif memory.category == 'goals' and any(word in current_message.lower() for word in ['want', 'plan', 'hope', 'future']):
                score += 3
            elif memory.category == 'interests' and any(word in current_message.lower() for word in ['enjoy', 'fun', 'love', 'like']):
                score += 3

            scored_memories.append((memory, score))

        # Sort by score descending
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, score in scored_memories]

    def _generate_context_summary(self, memories: List[UserMemory], insights: List[MemoryInsight]) -> str:
        """Generate a summary of the current memory context"""

        if not memories:
            return "No relevant memories found."

        # Categorize memories
        categories = {}
        for memory in memories:
            if memory.category not in categories:
                categories[memory.category] = 0
            categories[memory.category] += 1

        # Create summary
        summary_parts = []

        # Memory categories
        if categories:
            category_summary = ", ".join([f"{count} {cat}" for cat, count in categories.items()])
            summary_parts.append(f"Active memories: {category_summary}")

        # Insights summary
        if insights:
            insight_types = {}
            for insight in insights:
                insight_types[insight.insight_type] = insight_types.get(insight.insight_type, 0) + 1

            insight_summary = ", ".join([f"{count} {itype}" for itype, count in insight_types.items()])
            summary_parts.append(f"Insights: {insight_summary}")

        return "; ".join(summary_parts) if summary_parts else "Basic memory context available."

    def _serialize_memory_with_context(self, memory: UserMemory, insights: List[MemoryInsight]) -> Dict[str, Any]:
        """Serialize memory with contextual information"""

        # Find related insights
        related_insights = [insight for insight in insights if insight.memory_id == memory.id]

        return {
            "id": memory.id,
            "category": memory.category,
            "content": memory.memory_value,
            "confidence": memory.confidence_score,
            "last_updated": memory.last_updated.isoformat() if memory.last_updated else None,
            "mention_count": memory.mention_count,
            "related_insights": [self._serialize_insight(insight) for insight in related_insights]
        }

    def _serialize_insight(self, insight: MemoryInsight) -> Dict[str, Any]:
        """Serialize insight object"""
        return {
            "memory_id": insight.memory_id,
            "type": insight.insight_type,
            "content": insight.content,
            "confidence": insight.confidence,
            "follow_up_question": insight.follow_up_question
        }