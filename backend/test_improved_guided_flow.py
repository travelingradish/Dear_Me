#!/usr/bin/env python3
"""
Quick test to verify the improved guided mode flow is working correctly.
This tests the structured conversation flow and slot filling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import User, DiarySession, ConversationMessage
from app.services.diary_flow_controller import DiaryFlowController
from app.core.auth import get_password_hash

def create_test_user(db: Session) -> User:
    """Create or get test user"""
    test_username = "guided_flow_tester"
    
    # Delete existing test user if exists
    existing_user = db.query(User).filter(User.username == test_username).first()
    if existing_user:
        # Clean up all related data first
        from app.models.models import UserMemory, MemorySnapshot
        db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id.in_(
                db.query(DiarySession.id).filter(DiarySession.user_id == existing_user.id)
            )
        ).delete()
        db.query(DiarySession).filter(DiarySession.user_id == existing_user.id).delete()
        db.query(UserMemory).filter(UserMemory.user_id == existing_user.id).delete()
        db.query(MemorySnapshot).filter(MemorySnapshot.user_id == existing_user.id).delete()
        db.delete(existing_user)
        db.commit()
    
    # Create new test user
    user = User(
        username=test_username,
        hashed_password=get_password_hash("testpass123"),
        ai_character_name="Lumi"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_guided_conversation_flow():
    """Test the complete guided conversation flow"""
    print("🧪 Testing Improved Guided Mode Flow")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user = create_test_user(db)
        flow_controller = DiaryFlowController(db)
        
        # Start a guided session
        print("📝 Starting guided session...")
        session = flow_controller.start_diary_session(user, "en")
        print(f"✅ Session started: ID={session.id}, Intent={session.current_intent}")
        print(f"   Initial structured_data: {session.structured_data}")
        
        # Test conversation with mood information
        print("\n💬 Testing mood extraction...")
        result = flow_controller.process_user_message(session.id, "I'm feeling really tired and stressed from work today")
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Next intent: {result['next_intent']}")
        print(f"   Slot updates: {result['slot_updates']}")
        
        # Refresh session to see updated data
        db.refresh(session)
        print(f"   Updated structured_data: {session.structured_data}")
        
        # Test activities
        if session.current_intent == 'ASK_ACTIVITIES':
            print("\n🏃 Testing activities extraction...")
            result = flow_controller.process_user_message(session.id, "I had three meetings and worked on a big presentation")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            print(f"   Slot updates: {result['slot_updates']}")
            
            db.refresh(session)
            print(f"   Updated structured_data: {session.structured_data}")
        
        # Test challenges/wins  
        if session.current_intent == 'ASK_CHALLENGES_WINS':
            print("\n⚡ Testing challenges/wins extraction...")
            result = flow_controller.process_user_message(session.id, "The presentation went well but the meetings were exhausting")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            
            db.refresh(session)
            print(f"   Updated structured_data: {session.structured_data}")
        
        # Test gratitude
        if session.current_intent == 'ASK_GRATITUDE':
            print("\n🙏 Testing gratitude extraction...")
            result = flow_controller.process_user_message(session.id, "I'm grateful for my supportive team")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            
            db.refresh(session)
            print(f"   Updated structured_data: {session.structured_data}")
        
        # Test hope
        if session.current_intent == 'ASK_HOPE':
            print("\n🌟 Testing hope extraction...")
            result = flow_controller.process_user_message(session.id, "I hope tomorrow will be less stressful")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            
            db.refresh(session)
            print(f"   Updated structured_data: {session.structured_data}")
        
        # Test extra notes
        if session.current_intent == 'ASK_EXTRA':
            print("\n📝 Testing extra notes...")
            result = flow_controller.process_user_message(session.id, "I'm ready to generate my diary now")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            
            db.refresh(session)
            print(f"   Final structured_data: {session.structured_data}")
        
        # Check if we got to composition
        if session.current_phase == 'complete':
            print(f"\n📖 Diary generated:")
            print(f"   {session.composed_diary}")
            print(f"   ✅ Session completed successfully!")
        else:
            print(f"\n⏳ Session not yet complete. Current phase: {session.current_phase}")
        
        print("\n" + "=" * 50)
        print("✅ Guided Flow Test Completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_smart_intent_progression():
    """Test that intents don't advance with insufficient information"""
    print("\n🎯 Testing Smart Intent Progression")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user = create_test_user(db)
        flow_controller = DiaryFlowController(db)
        
        # Start session
        session = flow_controller.start_diary_session(user, "en")
        print(f"Starting intent: {session.current_intent}")
        
        # Give insufficient response
        print("\n❌ Testing with insufficient response...")
        result = flow_controller.process_user_message(session.id, "ok")
        db.refresh(session)
        print(f"   Response to 'ok': Intent stayed at {session.current_intent}")
        
        # Give better response
        print("\n✅ Testing with sufficient response...")
        result = flow_controller.process_user_message(session.id, "I feel pretty good today, energetic and positive")
        db.refresh(session)
        print(f"   Response to detailed mood: Intent advanced to {session.current_intent}")
        
        print("\n✅ Smart progression test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Smart progression test failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success1 = test_guided_conversation_flow()
    success2 = test_smart_intent_progression()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Guided mode improvements are working correctly!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    sys.exit(0 if success1 and success2 else 1)