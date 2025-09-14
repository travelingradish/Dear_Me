#!/usr/bin/env python3
"""
Test Chinese diary composition to ensure no technical field exposure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import User, DiarySession, ConversationMessage
from app.services.diary_flow_controller import DiaryFlowController
from app.core.auth import get_password_hash

def create_test_user(db: Session) -> User:
    """Create test user for Chinese diary composition"""
    test_username = "chinese_diary_tester"
    
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
        ai_character_name="露美"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_chinese_diary_composition():
    """Test Chinese diary composition for clean output"""
    print("🧪 Testing Chinese Diary Composition")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user = create_test_user(db)
        flow_controller = DiaryFlowController(db)
        
        # Start Chinese session
        session = flow_controller.start_diary_session(user, "zh")
        
        # Go through guided flow quickly
        responses = [
            "我今天感觉很好，很开心很有活力",
            "我今天跑步了，还和朋友一起吃午饭",
            "工作上的演讲很成功，虽然早上有点紧张",
            "我很感恩有这么好的朋友和健康的身体",
            "我希望明天能够平静而有收获",
            "我想生成我的日记了"
        ]
        
        for message in responses:
            flow_controller.process_user_message(session.id, message)
            db.refresh(session)
            if session.is_complete:
                break
        
        # Check diary composition
        print(f"Session complete: {session.is_complete}")
        print(f"Generated diary:")
        print("=" * 50)
        print(session.composed_diary)
        print("=" * 50)
        
        # Check for technical field exposure
        technical_terms = ['mood', 'activities', 'challenges', 'gratitude', 'hope', 'extra_notes']
        has_technical_exposure = any(term in session.composed_diary.lower() for term in technical_terms)
        
        print(f"\nTechnical field exposure check: {'❌ FAILED' if has_technical_exposure else '✅ PASSED'}")
        
        if has_technical_exposure:
            print("Found technical terms in diary:")
            for term in technical_terms:
                if term in session.composed_diary.lower():
                    print(f"  - {term}")
        
        return session.is_complete and not has_technical_exposure
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_chinese_diary_composition()
    
    if success:
        print("\n🎉 Chinese diary composition test passed! No technical field exposure.")
    else:
        print("\n❌ Chinese diary composition test failed.")
    
    sys.exit(0 if success else 1)