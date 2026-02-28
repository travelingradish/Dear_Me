"""
Graph Conversation Service with LangGraph Integration

This service implements contextual memory integration and dynamic follow-up questioning
using LangGraph's graph-based conversation flow, replacing the linear state machine
with an adaptive, memory-driven conversation system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, TypedDict, Any
import json
import logging
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.models.models import User, UserMemory, DiarySession, ConversationMessage
from app.services.memory_service import MemoryService
from app.services.guided_llm_service import GuidedLLMService


class ConversationState(TypedDict):
    """State structure for the graph conversation service"""
    messages: List[BaseMessage]
    user_id: int
    session_id: int
    current_phase: str  # 'understanding', 'exploring', 'deepening', 'composing', 'complete'
    structured_data: Dict[str, Any]
    active_memories: List[Dict[str, Any]]
    conversation_context: Dict[str, Any]
    follow_up_opportunities: List[str]
    emotional_state: str
    language: str
    character_name: str
    is_crisis: bool


class GraphConversationService:
    """
    Graph Conversation Service that uses LangGraph for sophisticated conversation flow
    with contextual memory integration and dynamic follow-up questioning
    """

    def __init__(self, db: Session):
        self.db = db
        self.memory_service = MemoryService()
        self.llm_service = GuidedLLMService()
        self.logger = logging.getLogger(__name__)
        self.checkpointer = InMemorySaver()

        # Initialize the conversation graph
        self.conversation_graph = self._build_conversation_graph()

    def _build_conversation_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""

        workflow = StateGraph(ConversationState)

        # Add nodes for different conversation phases
        workflow.add_node("understand_user", self._understand_user_node)
        workflow.add_node("retrieve_memories", self._retrieve_memories_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("identify_follow_ups", self._identify_follow_ups_node)
        workflow.add_node("extract_new_memories", self._extract_memories_node)
        workflow.add_node("crisis_handler", self._crisis_handler_node)
        workflow.add_node("compose_diary", self._compose_diary_node)

        # Define the conversation flow with conditional routing
        workflow.add_conditional_edges(
            "understand_user",
            self._route_after_understanding,
            {
                "crisis": "crisis_handler",
                "retrieve_memories": "retrieve_memories",
                "compose": "compose_diary",
                "end": END
            }
        )

        workflow.add_edge("retrieve_memories", "generate_response")
        workflow.add_edge("generate_response", "identify_follow_ups")
        workflow.add_edge("identify_follow_ups", "extract_new_memories")
        workflow.add_edge("extract_new_memories", END)
        workflow.add_edge("crisis_handler", END)
        workflow.add_edge("compose_diary", END)

        # Set entry point
        workflow.set_entry_point("understand_user")

        return workflow.compile(checkpointer=self.checkpointer)

    def process_conversation(self, session_id: int, user_message: str) -> Dict[str, Any]:
        """
        Process a conversation message through the graph conversation system

        Args:
            session_id: The diary session ID
            user_message: The user's message

        Returns:
            Dict containing response, insights, and conversation metadata
        """
        try:
            # Get session and user information
            session = self.db.query(DiarySession).filter(DiarySession.id == session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")

            user = self.db.query(User).filter(User.id == session.user_id).first()
            if not user:
                raise ValueError(f"User {session.user_id} not found")

            # Build conversation state
            state = ConversationState(
                messages=[HumanMessage(content=user_message)],
                user_id=session.user_id,
                session_id=session_id,
                current_phase=session.current_phase or 'understanding',
                structured_data=session.structured_data or {},
                active_memories=[],
                conversation_context={},
                follow_up_opportunities=[],
                emotional_state='neutral',
                language=session.language or 'en',
                character_name=user.ai_character_name or 'AI Assistant',
                is_crisis=session.is_crisis or False
            )

            # Process through the graph
            config = {"configurable": {"thread_id": f"session_{session_id}"}}
            result = self.conversation_graph.invoke(state, config)

            # Extract response and metadata
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            response = ai_messages[-1].content if ai_messages else "I'm here to listen."

            # Update session with new information
            session.structured_data = result["structured_data"]
            session.current_phase = result["current_phase"]
            session.is_crisis = result["is_crisis"]

            # Store conversation messages
            self._store_conversation_turn(session, user_message, response, result)

            self.db.commit()

            return {
                "response": response,
                "insights": {
                    "emotional_state": result["emotional_state"],
                    "follow_up_opportunities": result["follow_up_opportunities"],
                    "memories_activated": len(result["active_memories"]),
                    "phase": result["current_phase"]
                },
                "metadata": {
                    "is_crisis": result["is_crisis"],
                    "structured_data": result["structured_data"]
                }
            }

        except Exception as e:
            self.logger.error(f"Error processing conversation: {e}")
            return {
                "response": "I'm sorry, something went wrong. Could you try again?",
                "insights": {},
                "metadata": {"error": str(e)}
            }

    def _understand_user_node(self, state: ConversationState) -> ConversationState:
        """Analyze user message for intent, emotion, and content"""

        user_message = state["messages"][-1].content

        # Use LLM to understand user intent and emotional state
        try:
            understanding = self._analyze_user_message(
                user_message,
                state["language"],
                state["current_phase"]
            )

            state["emotional_state"] = understanding.get("emotional_state", "neutral")
            state["conversation_context"] = understanding.get("context", {})

            # Check for crisis indicators
            crisis_keywords = ["suicide", "kill myself", "end it all", "不想活", "自杀", "想死"]
            if any(keyword in user_message.lower() for keyword in crisis_keywords):
                state["is_crisis"] = True

        except Exception as e:
            self.logger.error(f"Error understanding user message: {e}")
            state["emotional_state"] = "neutral"

        return state

    def _retrieve_memories_node(self, state: ConversationState) -> ConversationState:
        """Retrieve contextually relevant memories"""

        user_message = state["messages"][-1].content

        # Get relevant memories using enhanced context
        relevant_memories = self.memory_service.get_relevant_memories(
            user_id=state["user_id"],
            context=user_message,
            db_session=self.db,
            limit=10,
            conversation_type="current"
        )

        # Convert to serializable format and add contextual scoring
        state["active_memories"] = []
        for memory in relevant_memories:
            memory_data = {
                "id": memory.id,
                "category": memory.category,
                "content": memory.memory_value,
                "confidence": memory.confidence_score,
                "relevance_reason": self._explain_memory_relevance(memory, user_message)
            }
            state["active_memories"].append(memory_data)

        return state

    def _generate_response_node(self, state: ConversationState) -> ConversationState:
        """Generate contextually aware response with memory integration"""

        user_message = state["messages"][-1].content

        # Build rich context for response generation
        memory_context = self._format_memories_for_context(state["active_memories"])
        conversation_history = self._get_recent_conversation_history(state["session_id"])

        # Generate response using LLM with enhanced context
        try:
            response_data = self._generate_contextual_response(
                user_message=user_message,
                memory_context=memory_context,
                conversation_history=conversation_history,
                emotional_state=state["emotional_state"],
                current_phase=state["current_phase"],
                language=state["language"],
                character_name=state["character_name"]
            )

            ai_response = response_data.get("response", "I understand. Tell me more.")
            state["messages"].append(AIMessage(content=ai_response))

            # Update structured data based on response
            if "data_updates" in response_data:
                state["structured_data"].update(response_data["data_updates"])

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            ai_response = "I'm listening. Please continue."
            state["messages"].append(AIMessage(content=ai_response))

        return state

    def _identify_follow_ups_node(self, state: ConversationState) -> ConversationState:
        """Identify opportunities for follow-up questions based on context and memories"""

        user_message = state["messages"][-1].content

        # Analyze for follow-up opportunities
        follow_ups = []

        # Memory-based follow-ups
        for memory in state["active_memories"]:
            if memory["category"] in ["relationships", "challenges", "goals"]:
                follow_up = self._generate_memory_based_follow_up(memory, user_message)
                if follow_up:
                    follow_ups.append(follow_up)

        # Emotional state-based follow-ups
        if state["emotional_state"] in ["sad", "anxious", "stressed"]:
            emotional_follow_up = self._generate_emotional_follow_up(
                state["emotional_state"],
                user_message,
                state["language"]
            )
            if emotional_follow_up:
                follow_ups.append(emotional_follow_up)

        # Conversation gap-based follow-ups
        if state["current_phase"] == "understanding" and len(state["structured_data"]) < 3:
            gap_follow_up = self._generate_information_gap_follow_up(
                state["structured_data"],
                state["language"]
            )
            if gap_follow_up:
                follow_ups.append(gap_follow_up)

        state["follow_up_opportunities"] = follow_ups[:3]  # Limit to top 3
        return state

    def _extract_memories_node(self, state: ConversationState) -> ConversationState:
        """Extract and store new memories from the conversation"""

        user_message = state["messages"][-1].content

        # Extract memories using the existing memory service
        try:
            extracted_memories = self.memory_service.extract_memories_from_text(
                user_message,
                state["user_id"],
                "graph_conversation"
            )

            if extracted_memories:
                # Store new memories
                stored_memories = self.memory_service.store_memories_internal(
                    self.db,
                    state["user_id"],
                    extracted_memories
                )

                self.logger.info(
                    f"Extracted and stored {len(stored_memories)} memories for user {state['user_id']}"
                )

        except Exception as e:
            self.logger.error(f"Error extracting memories: {e}")

        return state

    def _crisis_handler_node(self, state: ConversationState) -> ConversationState:
        """Handle crisis situations with appropriate responses"""

        if state["language"] == "zh":
            crisis_response = (
                "听到这些我很担心你。你的感受很重要，你值得得到帮助。"
                "如果你现在处于危险中，请立即拨打当地紧急电话或联系心理健康专线。"
                "我在这里支持你，但请务必寻求专业帮助。"
            )
        else:
            crisis_response = (
                "I'm very concerned about what you're sharing. Your feelings matter and you deserve help. "
                "If you're in immediate danger, please call your local emergency number or contact a mental health crisis line. "
                "I'm here to support you, but please make sure to seek professional help."
            )

        state["messages"].append(AIMessage(content=crisis_response))
        state["current_phase"] = "crisis_support"

        return state

    def _compose_diary_node(self, state: ConversationState) -> ConversationState:
        """Compose diary entry when ready"""

        try:
            diary_entry = self.llm_service.compose_diary_entry(
                structured_data=state["structured_data"],
                language=state["language"],
                character_name=state["character_name"]
            )

            if state["language"] == "zh":
                response = f"根据我们的对话，我为你写了今天的日记：\n\n{diary_entry}"
            else:
                response = f"Based on our conversation, I've written your diary entry:\n\n{diary_entry}"

            state["messages"].append(AIMessage(content=response))
            state["current_phase"] = "complete"

        except Exception as e:
            self.logger.error(f"Error composing diary: {e}")
            fallback = "抱歉，生成日记时出现问题。" if state["language"] == "zh" else "Sorry, there was an error creating your diary."
            state["messages"].append(AIMessage(content=fallback))

        return state

    def _route_after_understanding(self, state: ConversationState) -> str:
        """Determine next node based on current state"""

        if state["is_crisis"]:
            return "crisis"

        # Check if ready to compose diary
        structured_data = state["structured_data"]
        required_fields = ["mood", "activities", "reflection"]
        if all(field in structured_data and structured_data[field] for field in required_fields):
            return "compose"

        # Continue with memory retrieval for normal conversation
        return "retrieve_memories"

    # Helper methods for LLM interactions and context building

    def _analyze_user_message(self, message: str, language: str, current_phase: str) -> Dict[str, Any]:
        """Analyze user message for intent and emotional state"""
        # This would use the LLM to analyze the message
        # For now, return basic analysis
        return {
            "emotional_state": "neutral",
            "intent": "share",
            "context": {"topic": "daily_reflection"}
        }

    def _explain_memory_relevance(self, memory: UserMemory, user_message: str) -> str:
        """Explain why a memory is relevant to the current message"""
        # Simple relevance explanation - could be enhanced with LLM
        return f"Related to {memory.category} context"

    def _format_memories_for_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for use in LLM context"""
        if not memories:
            return ""

        context = "Relevant user context:\n"
        for memory in memories[:5]:  # Limit to prevent context overflow
            context += f"- {memory['category']}: {memory['content']}\n"

        return context

    def _get_recent_conversation_history(self, session_id: int) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        messages = self.db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == session_id
        ).order_by(ConversationMessage.created_at.desc()).limit(10).all()

        history = []
        for msg in reversed(messages):  # Reverse to get chronological order
            history.append({
                "role": msg.role,
                "content": msg.content
            })

        return history

    def _generate_contextual_response(self, **kwargs) -> Dict[str, Any]:
        """Generate response with full context awareness"""
        # This would use the LLM to generate a contextually aware response
        # For now, return a basic response structure
        return {
            "response": "I understand. That sounds important to reflect on.",
            "data_updates": {}
        }

    def _generate_memory_based_follow_up(self, memory: Dict[str, Any], user_message: str) -> Optional[str]:
        """Generate follow-up question based on memory context"""
        if memory["category"] == "relationships":
            return f"How did that affect your relationship with them?"
        elif memory["category"] == "challenges":
            return "How are you handling that challenge now?"
        return None

    def _generate_emotional_follow_up(self, emotional_state: str, user_message: str, language: str) -> Optional[str]:
        """Generate follow-up based on emotional state"""
        if language == "zh":
            if emotional_state == "sad":
                return "你想谈谈是什么让你感到难过吗？"
            elif emotional_state == "anxious":
                return "这种担心的感觉是什么时候开始的？"
        else:
            if emotional_state == "sad":
                return "Would you like to share what's making you feel this way?"
            elif emotional_state == "anxious":
                return "When did you start feeling anxious about this?"
        return None

    def _generate_information_gap_follow_up(self, structured_data: Dict[str, Any], language: str) -> Optional[str]:
        """Generate follow-up to fill information gaps"""
        if "mood" not in structured_data:
            return "你今天感觉怎么样？" if language == "zh" else "How are you feeling today?"
        elif "activities" not in structured_data:
            return "你今天做了什么特别的事吗？" if language == "zh" else "What did you do today?"
        return None

    def _store_conversation_turn(self, session: DiarySession, user_message: str, ai_response: str, state: ConversationState):
        """Store the conversation turn in the database"""

        # Store user message
        user_msg = ConversationMessage(
            diary_session_id=session.id,
            role="user",
            content=user_message,
            intent=state.get("conversation_context", {}).get("intent", "share")
        )
        self.db.add(user_msg)

        # Store AI response with metadata
        ai_msg = ConversationMessage(
            diary_session_id=session.id,
            role="assistant",
            content=ai_response,
            intent="respond",
            slot_updates={
                "emotional_state": state["emotional_state"],
                "follow_up_opportunities": state["follow_up_opportunities"],
                "memories_used": len(state["active_memories"])
            }
        )
        self.db.add(ai_msg)