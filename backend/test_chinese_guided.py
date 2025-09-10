#!/usr/bin/env python3
"""
Test Chinese guided mode conversation flow.
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
    """Create test user for Chinese flow"""
    test_username = "chinese_guided_tester"
    
    # Clean up existing user
    existing_user = db.query(User).filter(User.username == test_username).first()
    if existing_user:
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
    
    user = User(
        username=test_username,
        hashed_password=get_password_hash("testpass123"),
        ai_character_name="露美"  # Chinese name for Lumi
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_chinese_guided_flow():
    """Test Chinese guided conversation flow"""
    print("🧪 Testing Chinese Guided Mode Flow")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user = create_test_user(db)
        flow_controller = DiaryFlowController(db)
        
        # Start Chinese session
        print("📝 Starting Chinese guided session...")
        session = flow_controller.start_diary_session(user, "zh")
        print(f"✅ Session started: ID={session.id}, Intent={session.current_intent}")
        
        # Test mood in Chinese
        print("\n💬 Testing Chinese mood collection...")
        result = flow_controller.process_user_message(session.id, "我今天感觉很好，精力充沛，很开心")
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Next intent: {result['next_intent']}")
        
        db.refresh(session)
        print(f"   Updated intent: {session.current_intent}")
        print(f"   Structured data mood: {session.structured_data.get('mood', '')}")
        
        # Test activities in Chinese
        if session.current_intent == 'ASK_ACTIVITIES':
            print("\n🏃 Testing Chinese activities collection...")
            result = flow_controller.process_user_message(session.id, "我今天跑步了，还和朋友一起吃午饭")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Next intent: {result['next_intent']}")
            
            db.refresh(session)
            print(f"   Updated intent: {session.current_intent}")
            print(f"   Structured data activities: {session.structured_data.get('activities', '')}")
        
        print("\n" + "=" * 50)
        success = session.current_intent in ['ASK_ACTIVITIES', 'ASK_CHALLENGES_WINS']
        if success:
            print("✅ Chinese Guided Flow Test Passed!")
        else:
            print("❌ Chinese intent progression failed")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_chinese_guided_flow()
    
    if success:
        print("\n🎉 Chinese test passed! Guided mode works in Chinese!")
    else:
        print("\n❌ Chinese test failed.")
    
    sys.exit(0 if success else 1)