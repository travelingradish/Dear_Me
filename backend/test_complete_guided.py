#!/usr/bin/env python3
"""
Test complete guided mode flow through to diary composition.
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
    """Create test user"""
    test_username = "complete_guided_tester"
    
    # Clean up
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
        ai_character_name="Lumi"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_complete_guided_flow():
    """Test complete guided conversation flow to diary"""
    print("🧪 Testing Complete Guided Mode Flow")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        user = create_test_user(db)
        flow_controller = DiaryFlowController(db)
        
        # Start session
        session = flow_controller.start_diary_session(user, "en")
        print(f"✅ Session started: {session.current_intent}")
        
        # Go through each intent with realistic responses
        responses = [
            ("ASK_MOOD", "I'm feeling really good today, energetic and happy"),
            ("ASK_ACTIVITIES", "I went for a morning run and had lunch with close friends"),
            ("ASK_CHALLENGES_WINS", "The presentation at work went really well, though the morning was stressful"),
            ("ASK_GRATITUDE", "I'm grateful for my supportive friends and good health"),
            ("ASK_HOPE", "I'm hoping tomorrow will be peaceful and productive"),
            ("ASK_EXTRA", "I want to create my diary entry now")
        ]
        
        for expected_intent, message in responses:
            db.refresh(session)
            if session.current_intent != expected_intent:
                break
                
            print(f"\n📝 {expected_intent}: Processing '{message[:50]}...'")
            result = flow_controller.process_user_message(session.id, message)
            
            db.refresh(session)
            print(f"   → Next intent: {session.current_intent}")
            
            if session.current_phase == 'complete':
                print(f"   → Session completed with diary!")
                break
        
        # Check final state
        db.refresh(session)
        print(f"\n" + "=" * 60)
        print(f"Final phase: {session.current_phase}")
        print(f"Final intent: {session.current_intent}")
        print(f"Is complete: {session.is_complete}")
        print(f"Structured data keys: {list(session.structured_data.keys())}")
        
        # Show structured data
        print(f"\nStructured Data:")
        for key, value in session.structured_data.items():
            if value:
                print(f"  {key}: {value[:100]}{'...' if len(str(value)) > 100 else ''}")
        
        # Show diary if generated
        if session.composed_diary:
            print(f"\nGenerated Diary (first 200 chars):")
            print(f"{session.composed_diary[:200]}...")
            
        success = session.is_complete and session.composed_diary
        
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Complete guided flow test")
        return success
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_complete_guided_flow()
    
    if success:
        print("\n🎉 Complete guided flow test passed!")
    else:
        print("\n❌ Complete guided flow test failed.")
    
    sys.exit(0 if success else 1)