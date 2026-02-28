#!/usr/bin/env python3
"""
Test script for the new Graph Conversation Service with Enhanced Memory Integration

This script tests the contextual memory retrieval and follow-up question generation
without requiring the full LLM integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import User, UserMemory, DiarySession
from app.services.contextual_memory_service import ContextualMemoryService
from app.services.memory_service import MemoryService
from datetime import datetime
import json

def create_test_user(db: Session) -> User:
    """Create a test user with some memories"""

    # Check if test user already exists
    existing_user = db.query(User).filter(User.username == "graphconv_test").first()
    if existing_user:
        return existing_user

    # Create new test user
    user = User(
        username="graphconv_test",
        hashed_password="test_hash",
        ai_character_name="Graph Assistant"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def create_test_memories(db: Session, user: User) -> None:
    """Create test memories for the user"""

    # Check if memories already exist
    existing_count = db.query(UserMemory).filter(UserMemory.user_id == user.id).count()
    if existing_count > 0:
        print(f"Found {existing_count} existing memories for test user")
        return

    # Create various types of memories
    memory_service = MemoryService()

    test_conversations = [
        "I love playing guitar and writing music in my free time",
        "I work as a software engineer at a tech startup",
        "I struggle with anxiety, especially before big presentations at work",
        "My goal is to learn Spanish fluently by the end of the year",
        "I have a cat named Whiskers who always sits on my keyboard",
        "I prefer waking up early around 6 AM to have quiet morning time",
        "My best friend Sarah and I go hiking every weekend",
        "I want to start a side project building mobile apps",
        "I hate eating spicy food, it always makes me feel sick",
        "I usually drink coffee in the morning but switch to tea in the afternoon"
    ]

    for conversation in test_conversations:
        # Extract memories from each conversation
        extracted_memories = memory_service.extract_memories_from_text(
            conversation, user.id, "test_conversation"
        )

        # Store memories
        if extracted_memories:
            memory_service.store_memories_internal(db, user.id, extracted_memories)

    print(f"Created memories for test user {user.username}")

def test_contextual_memory_analysis():
    """Test the contextual memory analysis functionality"""

    print("=== Testing Graph Conversation Service Contextual Memory Integration ===\n")

    # Create database session
    db = SessionLocal()

    try:
        # Create test user and memories
        user = create_test_user(db)
        create_test_memories(db, user)

        # Initialize contextual memory service
        contextual_memory = ContextualMemoryService()

        # Test scenarios
        test_scenarios = [
            {
                "name": "Work Stress Scenario",
                "message": "I have a big presentation at work tomorrow and I'm feeling really anxious about it",
                "expected_insights": ["challenges", "anxiety patterns"]
            },
            {
                "name": "Weekend Plans Scenario",
                "message": "I'm thinking about what to do this weekend, maybe something outdoors",
                "expected_insights": ["interests", "relationships"]
            },
            {
                "name": "Learning Progress Scenario",
                "message": "I've been practicing Spanish every day and it's getting easier",
                "expected_insights": ["goals", "evolution"]
            },
            {
                "name": "Pet Interaction Scenario",
                "message": "My cat is being extra clingy today and won't let me work",
                "expected_insights": ["relationships", "work context"]
            },
            {
                "name": "Evening Routine Scenario",
                "message": "I'm having trouble sleeping lately, maybe too much coffee",
                "expected_insights": ["preferences", "health patterns"]
            }
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"--- Test {i}: {scenario['name']} ---")
            print(f"User message: \"{scenario['message']}\"")

            # Analyze memory context
            result = contextual_memory.get_contextual_memories_with_insights(
                user_id=user.id,
                current_message=scenario['message'],
                db=db,
                limit=10
            )

            # Display results
            print(f"\n📊 Analysis Results:")
            print(f"   • Memories found: {len(result['memories'])}")
            print(f"   • Insights generated: {len(result['insights'])}")
            print(f"   • Follow-up questions: {len(result['follow_up_questions'])}")
            print(f"   • Memory gaps identified: {len(result['memory_gaps'])}")

            # Show relevant memories
            if result['memories']:
                print(f"\n💭 Top Relevant Memories:")
                for j, memory in enumerate(result['memories'][:3], 1):
                    print(f"   {j}. [{memory['category']}] {memory['content'][:60]}...")
                    if memory['related_insights']:
                        print(f"      → Insight: {memory['related_insights'][0]['content']}")

            # Show insights
            if result['insights']:
                print(f"\n🔍 Key Insights:")
                for insight in result['insights'][:2]:
                    print(f"   • {insight['type']}: {insight['content']}")
                    if insight['follow_up_question']:
                        print(f"     ❓ {insight['follow_up_question']}")

            # Show follow-up questions
            if result['follow_up_questions']:
                print(f"\n❓ Suggested Follow-up Questions:")
                for question in result['follow_up_questions'][:2]:
                    print(f"   • {question}")

            # Show memory gaps
            if result['memory_gaps']:
                print(f"\n🔍 Memory Gaps (conversation opportunities):")
                for gap in result['memory_gaps'][:2]:
                    print(f"   • Missing {gap['category']}: {gap['suggested_question']}")

            print(f"\n📝 Context Summary: {result['context_summary']}")
            print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

def test_memory_pattern_analysis():
    """Test specific memory pattern analysis features"""

    print("=== Testing Memory Pattern Analysis ===\n")

    db = SessionLocal()

    try:
        user = create_test_user(db)
        contextual_memory = ContextualMemoryService()

        # Test pattern detection with more complex scenarios
        pattern_tests = [
            {
                "name": "Goal Progress Pattern",
                "setup_messages": [
                    "I want to learn guitar this year",
                    "I've been practicing guitar for 30 minutes every day",
                    "Guitar practice is getting easier, I can play 3 chords now"
                ],
                "test_message": "I played my first song on guitar today!"
            },
            {
                "name": "Challenge Evolution Pattern",
                "setup_messages": [
                    "I really struggle with public speaking at work",
                    "I'm getting better at presentations, did one last week",
                    "Public speaking is still hard but I'm more confident"
                ],
                "test_message": "I have another presentation next week"
            }
        ]

        memory_service = MemoryService()

        for test in pattern_tests:
            print(f"--- {test['name']} ---")

            # Add setup memories
            for msg in test['setup_messages']:
                extracted = memory_service.extract_memories_from_text(msg, user.id, "pattern_test")
                if extracted:
                    memory_service.store_memories_internal(db, user.id, extracted)

            # Analyze pattern
            result = contextual_memory.get_contextual_memories_with_insights(
                user_id=user.id,
                current_message=test['test_message'],
                db=db,
                limit=10
            )

            print(f"Test message: \"{test['test_message']}\"")
            print(f"Patterns detected: {len(result['insights'])} insights")

            for insight in result['insights']:
                if insight['type'] in ['evolution', 'pattern']:
                    print(f"   ✨ {insight['type']}: {insight['content']}")
                    if insight['follow_up_question']:
                        print(f"   ❓ {insight['follow_up_question']}")

            print()

    except Exception as e:
        print(f"❌ Pattern analysis test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)

    print("🚀 Starting Graph Conversation Service Memory Integration Tests...\n")

    # Run tests
    test_contextual_memory_analysis()
    test_memory_pattern_analysis()

    print("✅ Graph Conversation Service testing completed!")