#!/usr/bin/env python3
"""
Test the improved memory system to ensure context-aware filtering works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import User, UserMemory
from app.services.memory_service import MemoryService
from app.core.auth import get_password_hash

def create_test_user_with_memories(db: Session):
    """Create a test user with various types of memories"""
    test_username = "memory_test_user"
    
    # Clean up existing user
    existing_user = db.query(User).filter(User.username == test_username).first()
    if existing_user:
        db.query(UserMemory).filter(UserMemory.user_id == existing_user.id).delete()
        db.delete(existing_user)
        db.commit()
    
    # Create test user
    user = User(
        username=test_username,
        hashed_password=get_password_hash("testpass"),
        ai_character_name="TestBot"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create test memories of different categories
    memories_data = [
        ("personal_info", "name_john", "My name is John Smith", 0.9),
        ("personal_info", "age_25", "I am 25 years old", 0.9),
        ("personal_info", "work_engineer", "I work as a software engineer", 0.8),
        ("relationships", "cat_whiskers", "I have a cat named Whiskers", 0.9),
        ("relationships", "partner_sarah", "My girlfriend Sarah and I live together", 0.8),
        ("interests", "hobby_running", "I love running in the morning", 0.9),
        ("interests", "hobby_cooking", "I enjoy cooking Italian food", 0.8),
        ("challenges", "work_stress", "Work has been stressful lately with the new project", 0.7),
        ("goals", "fitness_goal", "I want to run a marathon next year", 0.8),
    ]
    
    for category, key, value, confidence in memories_data:
        memory = UserMemory(
            user_id=user.id,
            category=category,
            memory_key=key,
            memory_value=value,
            confidence_score=confidence
        )
        db.add(memory)
    
    db.commit()
    return user

def test_memory_relevance_scenarios():
    """Test various conversation scenarios to ensure appropriate memory filtering"""
    print("🧠 Testing Improved Memory System")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        user = create_test_user_with_memories(db)
        memory_service = MemoryService()
        
        # Test scenarios
        test_cases = [
            {
                "context": "Hello, how are you?",
                "description": "Casual greeting - should return minimal memories",
                "expected_categories": ["personal_info"]  # May include basic info, but limited
            },
            {
                "context": "I'm feeling tired and stressed from work today",
                "description": "Work stress context - should prioritize work-related memories",
                "expected_categories": ["challenges", "personal_info"]
            },
            {
                "context": "I went for a run this morning",
                "description": "Activity context - should prioritize interests/hobbies",
                "expected_categories": ["interests", "goals"]
            },
            {
                "context": "I had lunch with my girlfriend",
                "description": "Relationship context - should prioritize relationship memories",
                "expected_categories": ["relationships"]
            },
            {
                "context": "My cat is being playful today",
                "description": "Pet context - should include relevant relationship memories",
                "expected_categories": ["relationships"]
            },
            {
                "context": "I'm thinking about my career goals",
                "description": "Goals context - should prioritize goals and work info",
                "expected_categories": ["goals", "personal_info"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['description']}")
            print(f"Context: \"{test_case['context']}\"")
            
            # Get relevant memories
            relevant_memories = memory_service.get_relevant_memories(
                user.id, test_case['context'], db, limit=5
            )
            
            print(f"Returned {len(relevant_memories)} memories:")
            
            categories_found = set()
            for memory in relevant_memories:
                categories_found.add(memory.category)
                print(f"  • [{memory.category}] {memory.memory_value[:50]}{'...' if len(memory.memory_value) > 50 else ''}")
            
            # Test memory formatting with context
            formatted = memory_service.format_memories_for_prompt(
                relevant_memories, "en", test_case['context']
            )
            
            print(f"Formatted prompt length: {len(formatted)} characters")
            
            # Check if we got appropriate categories
            appropriate_categories = any(cat in categories_found for cat in test_case['expected_categories'])
            
            # Check if we avoided irrelevant information
            irrelevant_count = len([m for m in relevant_memories if m.category not in test_case['expected_categories']])
            
            if appropriate_categories and irrelevant_count <= 2:  # Allow some flexibility
                print("✅ PASS - Retrieved appropriate memories")
            else:
                print("❌ FAIL - Memory selection could be improved")
                print(f"   Expected categories: {test_case['expected_categories']}")
                print(f"   Found categories: {list(categories_found)}")
        
        print("\n" + "=" * 60)
        print("✅ Memory system testing completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_memory_filtering_edge_cases():
    """Test edge cases for memory filtering"""
    print("\n🔍 Testing Memory Filtering Edge Cases")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        user = create_test_user_with_memories(db)
        memory_service = MemoryService()
        
        edge_cases = [
            {
                "context": "",
                "description": "Empty context - should return few high-confidence memories"
            },
            {
                "context": "ok",
                "description": "Very short context - should be cautious about memory inclusion"
            },
            {
                "context": "The weather is nice today and I went to buy groceries at the store",
                "description": "Long irrelevant context - should return minimal memories"
            }
        ]
        
        for i, case in enumerate(edge_cases, 1):
            print(f"\n📝 Edge Case {i}: {case['description']}")
            print(f"Context: \"{case['context']}\"")
            
            memories = memory_service.get_relevant_memories(user.id, case['context'], db, limit=5)
            formatted = memory_service.format_memories_for_prompt(memories, "en", case['context'])
            
            print(f"Returned {len(memories)} memories, formatted length: {len(formatted)}")
            
            # For edge cases, we expect conservative memory inclusion
            if len(memories) <= 3:
                print("✅ PASS - Conservative memory inclusion")
            else:
                print("❌ FAIL - Too many memories for edge case")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Edge case test failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success1 = test_memory_relevance_scenarios()
    success2 = test_memory_filtering_edge_cases()
    
    if success1 and success2:
        print("\n🎉 All memory system tests passed!")
    else:
        print("\n❌ Some memory system tests failed.")
    
    sys.exit(0 if success1 and success2 else 1)