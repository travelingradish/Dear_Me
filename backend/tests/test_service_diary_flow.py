"""
Test suite for DiaryFlowController.
Tests the guided conversation state machine, intent progression, and crisis handling.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.diary_flow_controller import DiaryFlowController
from app.models.models import DiarySession, ConversationMessage, User


@pytest.fixture
def flow_controller(db_session):
    """Create a DiaryFlowController instance for testing."""
    return DiaryFlowController(db_session)


@pytest.fixture
def active_session(db_session, test_user):
    """Create an active diary session for testing."""
    session = DiarySession(
        user_id=test_user.id,
        language="en",
        current_phase="guide",
        current_intent="ASK_MOOD",
        structured_data={},
        is_complete=False
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.mark.unit
def test_intent_flow_progression(flow_controller):
    """Test that intent flow mapping is correct."""
    expected_flow = {
        'ASK_MOOD': 'ASK_ACTIVITIES',
        'ASK_ACTIVITIES': 'ASK_CHALLENGES_WINS', 
        'ASK_CHALLENGES_WINS': 'ASK_GRATITUDE',
        'ASK_GRATITUDE': 'ASK_HOPE',
        'ASK_HOPE': 'ASK_EXTRA',
        'ASK_EXTRA': 'COMPOSE',
        'COMPOSE': 'COMPLETE',
        'CRISIS_FLOW': 'CRISIS_FLOW'
    }
    
    assert flow_controller.intent_flow == expected_flow


@pytest.mark.integration
def test_start_diary_session_new(flow_controller, test_user):
    """Test starting a new diary session."""
    with patch('app.services.guided_llm_service.GuidedLLMService.get_initial_greeting') as mock_greeting:
        mock_greeting.return_value = f"Hi, {test_user.ai_character_name} here. How are you feeling today?"
        
        session = flow_controller.start_diary_session(test_user, language="en")
        
        assert session is not None
        assert session.user_id == test_user.id
        assert session.language == "en"
        assert session.current_phase == "guide"
        assert session.current_intent == "ASK_MOOD"
        assert session.is_complete == False
        assert session.is_crisis == False
        
        # Should have created initial greeting message
        messages = flow_controller.db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == session.id
        ).all()
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert test_user.ai_character_name in messages[0].content


@pytest.mark.integration
def test_start_diary_session_existing_incomplete(flow_controller, test_user, active_session):
    """Test starting session when an incomplete session exists today."""
    with patch('app.services.guided_llm_service.GuidedLLMService.get_initial_greeting') as mock_greeting:
        mock_greeting.return_value = f"Hi, {test_user.ai_character_name} here. How are you feeling today?"
        
        session = flow_controller.start_diary_session(test_user, language="en")
        
        # Should return the existing session
        assert session.id == active_session.id
        assert session.current_intent == "ASK_MOOD"


@pytest.mark.integration
def test_process_user_message_normal_flow(flow_controller, test_user, active_session):
    """Test processing user message in normal conversation flow."""
    mock_response = {
        "response": "That's wonderful! What activities did you do today?",
        "next_intent": "ASK_ACTIVITIES",
        "slot_updates": {"mood": "great, excited"},
        "is_crisis": False
    }
    
    with patch.object(flow_controller.llm_service, 'process_guided_message') as mock_process:
        mock_process.return_value = mock_response
        
        result = flow_controller.process_user_message(
            active_session.id, 
            "I'm feeling great today, really excited!"
        )
        
        assert result["response"] == mock_response["response"]
        assert result["next_intent"] == mock_response["next_intent"]
        assert result["slot_updates"] == mock_response["slot_updates"]
        assert result["is_crisis"] == False
        
        # Session should be updated
        flow_controller.db.refresh(active_session)
        assert active_session.current_intent == "ASK_ACTIVITIES"
        assert active_session.structured_data["mood"] == "great, excited"


@pytest.mark.integration
def test_process_user_message_crisis_detection(flow_controller, test_user, active_session):
    """Test crisis detection and handling during conversation."""
    mock_crisis_response = {
        "response": "I'm concerned about you. It sounds like you're going through a difficult time.",
        "next_intent": "CRISIS_FLOW",
        "slot_updates": {},
        "is_crisis": True
    }
    
    with patch.object(flow_controller.llm_service, 'process_guided_message') as mock_process:
        mock_process.return_value = mock_crisis_response
        
        result = flow_controller.process_user_message(
            active_session.id,
            "I feel hopeless and don't want to be here anymore"
        )
        
        assert result["is_crisis"] == True
        assert result["next_intent"] == "CRISIS_FLOW"
        
        # Session should be marked as crisis
        flow_controller.db.refresh(active_session)
        assert active_session.is_crisis == True
        assert active_session.current_intent == "CRISIS_FLOW"
        assert active_session.current_phase == "crisis"


@pytest.mark.integration
def test_process_user_message_compose_phase(flow_controller, test_user, active_session):
    """Test processing message during compose phase."""
    # Set session to compose phase
    active_session.current_phase = "compose"
    active_session.current_intent = "COMPOSE"
    active_session.structured_data = {
        "mood": "good",
        "activities": "work, exercise",
        "gratitude": "health, family"
    }
    flow_controller.db.commit()
    
    mock_compose_response = {
        "response": "Based on our conversation, here's your diary entry: Today was a good day...",
        "next_intent": "COMPLETE",
        "slot_updates": {},
        "is_crisis": False,
        "composed_diary": "Today was a good day. I felt positive and accomplished my work and exercise goals. I'm grateful for my health and family."
    }
    
    with patch.object(flow_controller.llm_service, 'compose_diary_entry') as mock_compose:
        mock_compose.return_value = mock_compose_response
        
        result = flow_controller.process_user_message(
            active_session.id,
            "Please create my diary entry"
        )
        
        assert result["composed_diary"] is not None
        assert len(result["composed_diary"]) > 50  # Should be substantial content
        assert result["next_intent"] == "COMPLETE"
        
        # Session should be updated with composed diary
        flow_controller.db.refresh(active_session)
        assert active_session.composed_diary is not None
        assert active_session.current_phase == "complete"
        assert active_session.is_complete == True


@pytest.mark.integration
def test_process_user_message_session_not_found(flow_controller):
    """Test processing message for non-existent session."""
    with pytest.raises(Exception):  # Should raise appropriate exception
        flow_controller.process_user_message(99999, "Test message")


@pytest.mark.integration
def test_process_user_message_completed_session(flow_controller, test_user, active_session):
    """Test processing message for already completed session."""
    # Mark session as complete
    active_session.is_complete = True
    active_session.current_phase = "complete"
    flow_controller.db.commit()
    
    with pytest.raises(Exception):  # Should not allow messages to completed sessions
        flow_controller.process_user_message(active_session.id, "Test message")


@pytest.mark.integration
def test_intent_progression_through_full_flow(flow_controller, test_user, active_session):
    """Test complete intent progression from ASK_MOOD to COMPLETE."""
    intent_progression = [
        ("ASK_MOOD", "I'm feeling good today"),
        ("ASK_ACTIVITIES", "I went for a run and read a book"),
        ("ASK_CHALLENGES_WINS", "The main challenge was waking up early"),
        ("ASK_GRATITUDE", "I'm grateful for my health"),
        ("ASK_HOPE", "I hope tomorrow will be even better"),
        ("ASK_EXTRA", "Nothing else to add"),
        ("COMPOSE", "Please generate my diary")
    ]
    
    for expected_intent, user_message in intent_progression:
        # Verify current intent
        flow_controller.db.refresh(active_session)
        assert active_session.current_intent == expected_intent
        
        # Mock appropriate response based on intent
        if expected_intent == "COMPOSE":
            mock_response = {
                "response": "Here's your diary entry...",
                "next_intent": "COMPLETE",
                "slot_updates": {},
                "is_crisis": False,
                "composed_diary": "Today was a wonderful day..."
            }
            with patch.object(flow_controller.llm_service, 'compose_diary_entry') as mock_compose:
                mock_compose.return_value = mock_response
                result = flow_controller.process_user_message(active_session.id, user_message)
        else:
            next_intent = flow_controller.intent_flow[expected_intent]
            mock_response = {
                "response": f"Response to {expected_intent}",
                "next_intent": next_intent,
                "slot_updates": {expected_intent.lower(): "extracted_info"},
                "is_crisis": False
            }
            with patch.object(flow_controller.llm_service, 'process_guided_message') as mock_process:
                mock_process.return_value = mock_response
                result = flow_controller.process_user_message(active_session.id, user_message)
    
    # Final state should be complete
    flow_controller.db.refresh(active_session)
    assert active_session.is_complete == True
    assert active_session.current_phase == "complete"
    assert active_session.composed_diary is not None


@pytest.mark.integration
def test_memory_integration_during_conversation(flow_controller, test_user, active_session):
    """Test that memory service is used during conversation processing."""
    with patch.object(flow_controller.memory_service, 'extract_memory_from_conversation') as mock_extract, \
         patch.object(flow_controller.memory_service, 'store_memories') as mock_store, \
         patch.object(flow_controller.llm_service, 'process_guided_message') as mock_process:
        
        mock_extract.return_value = [MagicMock(category="interests", content="likes running")]
        mock_store.return_value = [MagicMock()]
        mock_process.return_value = {
            "response": "Great! Running is excellent exercise.",
            "next_intent": "ASK_ACTIVITIES",
            "slot_updates": {"mood": "energetic"},
            "is_crisis": False
        }
        
        flow_controller.process_user_message(
            active_session.id,
            "I'm feeling energetic because I love running"
        )
        
        # Verify memory extraction was called
        mock_extract.assert_called_once_with("I'm feeling energetic because I love running", test_user.id)
        mock_store.assert_called_once()


@pytest.mark.integration
def test_conversation_message_storage(flow_controller, test_user, active_session):
    """Test that conversation messages are properly stored."""
    mock_response = {
        "response": "That's wonderful to hear!",
        "next_intent": "ASK_ACTIVITIES", 
        "slot_updates": {"mood": "happy"},
        "is_crisis": False
    }
    
    with patch.object(flow_controller.llm_service, 'process_guided_message') as mock_process:
        mock_process.return_value = mock_response
        
        flow_controller.process_user_message(
            active_session.id,
            "I'm feeling really happy today!"
        )
        
        # Check that both user and assistant messages were stored
        messages = flow_controller.db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == active_session.id
        ).order_by(ConversationMessage.created_at).all()
        
        # Should have initial greeting + user message + assistant response
        assert len(messages) >= 3
        
        # Find the user message
        user_message = next((m for m in messages if m.role == "user" and "happy" in m.content), None)
        assert user_message is not None
        assert user_message.content == "I'm feeling really happy today!"
        
        # Find the assistant response
        assistant_message = next((m for m in messages if m.role == "assistant" and m.content == mock_response["response"]), None)
        assert assistant_message is not None
        assert assistant_message.intent == "ASK_ACTIVITIES"


@pytest.mark.integration
def test_character_name_in_greeting_update(flow_controller, test_user):
    """Test that character name changes are reflected in session greetings."""
    # Start with default character name
    with patch('app.services.guided_llm_service.GuidedLLMService.get_initial_greeting') as mock_greeting:
        mock_greeting.return_value = f"Hi, {test_user.ai_character_name} here. How are you feeling today?"
        
        session1 = flow_controller.start_diary_session(test_user, language="en")
        
        # Check initial greeting
        messages = flow_controller.db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == session1.id
        ).all()
        initial_greeting = messages[0].content
        assert test_user.ai_character_name in initial_greeting
        
        # Update character name
        test_user.ai_character_name = "Buddy"
        flow_controller.db.commit()
        
        # Start new session with updated name
        mock_greeting.return_value = f"Hi, Buddy here. How are you feeling today?"
        session2 = flow_controller.start_diary_session(test_user, language="en")
        
        # Check that new greeting uses updated name
        new_messages = flow_controller.db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == session2.id
        ).all()
        new_greeting = new_messages[0].content
        assert "Buddy" in new_greeting


@pytest.mark.unit
def test_crisis_intent_loops(flow_controller):
    """Test that crisis intent stays in CRISIS_FLOW."""
    # Crisis flow should loop back to itself
    assert flow_controller.intent_flow["CRISIS_FLOW"] == "CRISIS_FLOW"


@pytest.mark.integration
def test_structured_data_accumulation(flow_controller, test_user, active_session):
    """Test that structured data accumulates correctly throughout conversation."""
    conversation_steps = [
        ("ASK_MOOD", "I feel great today", {"mood": "great"}),
        ("ASK_ACTIVITIES", "I went swimming", {"activities": "swimming"}),
        ("ASK_CHALLENGES_WINS", "No major challenges", {"challenges": "none"}),
        ("ASK_GRATITUDE", "Grateful for good weather", {"gratitude": "good weather"})
    ]
    
    for expected_intent, message, expected_slot_update in conversation_steps:
        # Verify current intent
        flow_controller.db.refresh(active_session)
        assert active_session.current_intent == expected_intent
        
        # Process message
        next_intent = flow_controller.intent_flow[expected_intent]
        mock_response = {
            "response": f"Response to {expected_intent}",
            "next_intent": next_intent,
            "slot_updates": expected_slot_update,
            "is_crisis": False
        }
        
        with patch.object(flow_controller.llm_service, 'process_guided_message') as mock_process:
            mock_process.return_value = mock_response
            flow_controller.process_user_message(active_session.id, message)
        
        # Verify structured data accumulation
        flow_controller.db.refresh(active_session)
        for key, value in expected_slot_update.items():
            assert key in active_session.structured_data
            assert active_session.structured_data[key] == value
    
    # Final structured data should contain all accumulated information
    final_data = active_session.structured_data
    assert "mood" in final_data
    assert "activities" in final_data  
    assert "challenges" in final_data
    assert "gratitude" in final_data