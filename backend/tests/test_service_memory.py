"""
Test suite for MemoryService.
Tests memory extraction, categorization, and snapshot functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, date

# Import the service we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.memory_service import MemoryService
from app.models.models import User, UserMemory, MemorySnapshot


@pytest.fixture
def memory_service(db_session):
    """Create a MemoryService instance for testing."""
    return MemoryService()


@pytest.fixture
def sample_conversations():
    """Sample conversation data for memory extraction testing."""
    return [
        "I love playing guitar and spending time with my cat Whiskers. I work as a software engineer at TechCorp.",
        "My biggest challenge is managing anxiety, but I'm working with a therapist named Dr. Smith.",
        "I hope to travel to Japan next year and maybe learn Japanese. I've always been fascinated by the culture.",
        "My girlfriend Sarah and I have been together for 2 years. We enjoy hiking and cooking together.",
        "I prefer coffee over tea, and I'm vegetarian. I live in Seattle and love the rainy weather.",
        "My goal is to publish a mobile app this year. I've been working on it for 6 months now."
    ]


@pytest.mark.unit
def test_extract_memory_from_conversation_personal_info(memory_service, sample_conversations):
    """Test extraction of personal information from conversation."""
    conversation = sample_conversations[0]  # Contains name, job, pet info
    
    memories = memory_service.extract_memory_from_conversation(conversation, 1)
    
    # Should extract job and pet info
    personal_memories = [m for m in memories if m.category == "personal_info"]
    assert len(personal_memories) > 0
    
    # Check that job information was extracted
    job_memory = next((m for m in personal_memories if "engineer" in m.content.lower()), None)
    assert job_memory is not None
    assert job_memory.confidence > 0.5


@pytest.mark.unit 
def test_extract_memory_from_conversation_relationships(memory_service, sample_conversations):
    """Test extraction of relationship information."""
    conversation = sample_conversations[3]  # Contains girlfriend info
    
    memories = memory_service.extract_memory_from_conversation(conversation, 1)
    
    relationship_memories = [m for m in memories if m.category == "relationships"]
    assert len(relationship_memories) > 0
    
    # Check that girlfriend information was extracted
    sarah_memory = next((m for m in relationship_memories if "sarah" in m.content.lower()), None)
    assert sarah_memory is not None
    assert "2 years" in sarah_memory.content


@pytest.mark.unit
def test_extract_memory_from_conversation_interests(memory_service, sample_conversations):
    """Test extraction of interests and hobbies."""
    conversation = sample_conversations[0]  # Contains guitar playing
    
    memories = memory_service.extract_memory_from_conversation(conversation, 1)
    
    interest_memories = [m for m in memories if m.category == "interests"]
    assert len(interest_memories) > 0
    
    # Check that guitar interest was extracted
    guitar_memory = next((m for m in interest_memories if "guitar" in m.content.lower()), None)
    assert guitar_memory is not None


@pytest.mark.unit
def test_extract_memory_from_conversation_challenges(memory_service, sample_conversations):
    """Test extraction of challenges and difficulties."""
    conversation = sample_conversations[1]  # Contains anxiety challenge
    
    memories = memory_service.extract_memory_from_conversation(conversation, 1)
    
    challenge_memories = [m for m in memories if m.category == "challenges"]
    assert len(challenge_memories) > 0
    
    # Check that anxiety challenge was extracted
    anxiety_memory = next((m for m in challenge_memories if "anxiety" in m.content.lower()), None)
    assert anxiety_memory is not None


@pytest.mark.unit
def test_extract_memory_from_conversation_goals(memory_service, sample_conversations):
    """Test extraction of goals and aspirations."""
    conversation = sample_conversations[2]  # Contains travel goal
    
    memories = memory_service.extract_memory_from_conversation(conversation, 1)
    
    goal_memories = [m for m in memories if m.category == "goals"]
    assert len(goal_memories) > 0
    
    # Check that Japan travel goal was extracted
    japan_memory = next((m for m in goal_memories if "japan" in m.content.lower()), None)
    assert japan_memory is not None


@pytest.mark.unit
def test_extract_memory_from_conversation_preferences(memory_service, sample_conversations):
    """Test extraction of preferences and lifestyle choices."""
    conversation = sample_conversations[4]  # Contains coffee preference, diet, location
    
    memories = memory_service.extract_memory_from_conversation(conversation, 1)
    
    preference_memories = [m for m in memories if m.category == "preferences"]
    assert len(preference_memories) > 0
    
    # Check that dietary preference was extracted
    diet_memory = next((m for m in preference_memories if "vegetarian" in m.content.lower()), None)
    assert diet_memory is not None


@pytest.mark.unit
def test_extract_memory_empty_conversation(memory_service):
    """Test memory extraction from empty or meaningless conversation."""
    empty_conversations = ["", "ok", "yes", "hmm", "..."]
    
    for conversation in empty_conversations:
        memories = memory_service.extract_memory_from_conversation(conversation, 1)
        assert len(memories) == 0


@pytest.mark.integration
def test_store_memories_to_database(memory_service, db_session, test_user):
    """Test storing extracted memories to database."""
    conversation = "I work as a teacher and love reading mystery novels. My dog Max is a golden retriever."
    
    # Extract memories
    memories = memory_service.extract_memory_from_conversation(conversation, test_user.id)
    
    # Store to database
    stored_memories = memory_service.store_memories(memories, db_session)
    
    assert len(stored_memories) > 0
    
    # Verify they're in the database
    db_memories = db_session.query(UserMemory).filter(UserMemory.user_id == test_user.id).all()
    assert len(db_memories) == len(stored_memories)
    
    # Check that different categories were stored
    categories = {m.category for m in db_memories}
    assert "personal_info" in categories  # job
    assert "interests" in categories      # reading


@pytest.mark.integration
def test_get_relevant_memories(memory_service, db_session, test_user):
    """Test retrieval of relevant memories for context."""
    # Store some test memories
    test_memories = [
        UserMemory(user_id=test_user.id, category="interests", memory_key="hiking", memory_value="loves hiking", confidence_score=0.9),
        UserMemory(user_id=test_user.id, category="preferences", memory_key="coffee", memory_value="drinks coffee daily", confidence_score=0.8),
        UserMemory(user_id=test_user.id, category="goals", memory_key="climbing", memory_value="wants to climb Mount Rainier", confidence_score=0.7),
        UserMemory(user_id=test_user.id, category="challenges", memory_key="heights", memory_value="afraid of heights", confidence_score=0.6)
    ]
    
    for memory in test_memories:
        db_session.add(memory)
    db_session.commit()
    
    # Test retrieval with different contexts
    hiking_context = memory_service.get_relevant_memories(test_user.id, "hiking outdoors", db_session)
    assert len(hiking_context) > 0
    assert any("hiking" in mem.content for mem in hiking_context)
    
    coffee_context = memory_service.get_relevant_memories(test_user.id, "morning routine coffee", db_session)
    assert len(coffee_context) > 0
    assert any("coffee" in mem.content for mem in coffee_context)


@pytest.mark.integration
def test_get_relevant_memories_limit(memory_service, db_session, test_user):
    """Test that memory retrieval respects the limit parameter."""
    # Store many test memories
    for i in range(10):
        memory = UserMemory(
            user_id=test_user.id, 
            category="interests", 
            memory_key=f"interest_{i}",
            memory_value=f"interest number {i}",
            confidence_score=0.8
        )
        db_session.add(memory)
    db_session.commit()
    
    # Test with limit
    limited_memories = memory_service.get_relevant_memories(test_user.id, "interests", db_session, limit=5)
    assert len(limited_memories) == 5
    
    # Test without limit (should get more)
    all_memories = memory_service.get_relevant_memories(test_user.id, "interests", db_session, limit=20)
    assert len(all_memories) > 5


@pytest.mark.integration
def test_create_memory_snapshot(memory_service, db_session, test_user):
    """Test creating a memory snapshot."""
    # Store some test memories first
    test_memories = [
        UserMemory(user_id=test_user.id, category="interests", memory_key="piano", memory_value="plays piano", confidence_score=0.9),
        UserMemory(user_id=test_user.id, category="goals", memory_key="french", memory_value="learn French", confidence_score=0.8)
    ]
    
    for memory in test_memories:
        db_session.add(memory)
    db_session.commit()
    
    # Create snapshot
    snapshot = memory_service.create_memory_snapshot(test_user.id, db_session)
    
    assert snapshot is not None
    assert snapshot.user_id == test_user.id
    assert snapshot.memory_context is not None
    
    # Verify snapshot has memory context
    assert len(snapshot.memory_context) > 0
    memory_categories = [mem['category'] for mem in snapshot.memory_context]
    assert "interests" in memory_categories
    assert "goals" in memory_categories


@pytest.mark.unit
def test_memory_pattern_matching(memory_service):
    """Test that memory extraction patterns work correctly."""
    test_cases = [
        # Personal info patterns
        ("I work as a software engineer", "personal_info"),
        ("My name is John Smith", "personal_info"),
        ("I live in New York", "personal_info"),
        
        # Relationship patterns  
        ("My wife Sarah is amazing", "relationships"),
        ("I have a brother named Mike", "relationships"),
        ("My best friend loves hiking", "relationships"),
        
        # Interest patterns
        ("I love playing tennis", "interests"),
        ("I enjoy reading books", "interests"),
        ("Photography is my passion", "interests"),
        
        # Challenge patterns
        ("I struggle with depression", "challenges"),
        ("Anxiety is a daily battle", "challenges"),
        ("I'm having trouble sleeping", "challenges"),
        
        # Goal patterns
        ("I want to learn Spanish", "goals"),
        ("My goal is to run a marathon", "goals"),
        ("I hope to travel to Europe", "goals"),
        
        # Preference patterns
        ("I prefer tea over coffee", "preferences"),
        ("I'm a vegetarian", "preferences"),
        ("I like waking up early", "preferences")
    ]
    
    for text, expected_category in test_cases:
        memories = memory_service.extract_memory_from_conversation(text, 1)
        
        # Should extract at least one memory of the expected category
        categories = [m.category for m in memories]
        assert expected_category in categories, f"Expected {expected_category} for '{text}', got {categories}"


@pytest.mark.unit
def test_memory_confidence_scoring(memory_service):
    """Test that confidence scores are assigned appropriately."""
    # Strong, clear statements should have high confidence
    strong_text = "I am a software engineer at Microsoft and I have been programming for 10 years"
    strong_memories = memory_service.extract_memory_from_conversation(strong_text, 1)
    
    assert len(strong_memories) > 0
    assert all(m.confidence >= 0.7 for m in strong_memories)
    
    # Weaker, more ambiguous statements should have lower confidence
    weak_text = "I think maybe I might like programming sometimes"
    weak_memories = memory_service.extract_memory_from_conversation(weak_text, 1)
    
    if weak_memories:  # Might not extract anything from weak text
        assert all(m.confidence <= 0.6 for m in weak_memories)


@pytest.mark.integration 
def test_memory_deduplication(memory_service, db_session, test_user):
    """Test that duplicate memories are handled appropriately."""
    # Store similar memories
    similar_conversations = [
        "I love playing guitar",
        "I really enjoy playing the guitar",
        "Guitar is my favorite instrument to play"
    ]
    
    all_memories = []
    for conversation in similar_conversations:
        memories = memory_service.extract_memory_from_conversation(conversation, test_user.id)
        all_memories.extend(memories)
    
    # Store all memories
    memory_service.store_memories(all_memories, db_session)
    
    # Retrieve memories - should handle similarity appropriately
    stored_memories = db_session.query(UserMemory).filter(UserMemory.user_id == test_user.id).all()
    
    # Check guitar-related memories for deduplication
    guitar_memories = [m for m in stored_memories if "guitar" in m.memory_value.lower()]
    
    # Verify we don't have excessive duplication - should be significantly less than original extraction
    assert len(guitar_memories) <= 4  # Should not create too many duplicates (was 7+ before deduplication)
    
    # Verify no exact duplicates exist
    memory_values = [m.memory_value for m in guitar_memories]
    assert len(memory_values) == len(set(memory_values))  # All values should be unique


@pytest.mark.integration
def test_memory_service_full_workflow(memory_service, db_session, test_user, sample_conversations):
    """Test complete memory service workflow."""
    all_extracted_memories = []
    
    # Step 1: Extract memories from all conversations
    for conversation in sample_conversations:
        memories = memory_service.extract_memory_from_conversation(conversation, test_user.id)
        all_extracted_memories.extend(memories)
    
    # Step 2: Store all memories
    stored_memories = memory_service.store_memories(all_extracted_memories, db_session)
    assert len(stored_memories) > 0
    
    # Step 3: Create snapshot
    snapshot = memory_service.create_memory_snapshot(test_user.id, db_session)
    assert snapshot is not None
    
    # Step 4: Retrieve relevant memories for different contexts
    contexts = ["work and career", "hobbies and interests", "relationships and family", "health and challenges"]
    
    for context in contexts:
        relevant_memories = memory_service.get_relevant_memories(test_user.id, context, db_session)
        # Should get some memories for each context based on sample conversations
        if context == "work and career":
            assert any("engineer" in m.content.lower() for m in relevant_memories)
        elif context == "hobbies and interests":
            assert any("guitar" in m.content.lower() for m in relevant_memories)
        elif context == "relationships and family":
            assert any("sarah" in m.content.lower() or "girlfriend" in m.content.lower() for m in relevant_memories)
    
    # Step 5: Verify database state
    final_db_memories = db_session.query(UserMemory).filter(UserMemory.user_id == test_user.id).all()
    categories = {m.category for m in final_db_memories}
    
    # Should have extracted multiple categories
    assert len(categories) >= 4
    expected_categories = {"personal_info", "relationships", "interests", "challenges", "goals", "preferences"}
    assert categories.intersection(expected_categories) == categories