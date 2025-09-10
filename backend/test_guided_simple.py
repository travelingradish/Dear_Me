#!/usr/bin/env python3
"""
Simple test to verify the guided mode conversation flow works correctly.
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
    test_username = "simple_guided_tester"
    
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

def test_simple_guided_flow():
    """Test the guided conversation flow without memory processing"""
    print("🧪 Testing Simple Guided Mode Flow")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user = create_test_user(db)
        flow_controller = DiaryFlowController(db)
        
        # Start a guided session
        print("📝 Starting guided session...")
        session = flow_controller.start_diary_session(user, "en")
        print(f"✅ Session started: ID={session.id}, Intent={session.current_intent}")
        
        # Test mood response
        print("\n💬 Testing mood collection...")
        result = flow_controller.process_user_message(session.id, "I'm feeling really good today, energetic and happy")
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Next intent: {result['next_intent']}")
        
        # Refresh to see changes
        db.refresh(session)
        print(f"   Updated intent: {session.current_intent}")
        print(f"   Structured data: {session.structured_data}")
        
        # Test activities if we advanced
        if session.current_intent == 'ASK_ACTIVITIES':
            print("\n🏃 Testing activities collection...")
            result = flow_controller.process_user_message(session.id, "I went for a run and had lunch with friends")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            
            db.refresh(session)
            print(f"   Updated intent: {session.current_intent}")
            print(f"   Structured data: {session.structured_data}")
        
        print("\n" + "=" * 50)
        if session.current_intent != 'ASK_MOOD':
            print("✅ Simple Guided Flow Test Passed! Intent progression working.")
        else:
            print("❌ Intent did not progress from ASK_MOOD")
        
        return session.current_intent != 'ASK_MOOD'
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_simple_guided_flow()
    
    if success:
        print("\n🎉 Simple test passed! Guided mode intent progression is working!")
    else:
        print("\n❌ Test failed. Please check the implementation.")
    
    sys.exit(0 if success else 1)