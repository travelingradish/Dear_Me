#!/usr/bin/env python3
"""
Debug database session handling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from main import get_db
from app.models.models import DiarySession, User, ConversationMessage
from app.services.diary_flow_controller import DiaryFlowController
from app.core.auth import create_access_token, get_password_hash
import json

def test_db_session():
    """Test database session handling directly"""
    print("🔍 Testing Database Session Handling...")
    
    # Get a database session
    db = next(get_db())
    
    try:
        # Find our test user
        user = db.query(User).filter(User.email == "calendar_test@example.com").first()
        if not user:
            print("❌ Test user not found")
            return False
        
        print(f"✅ Found test user: {user.username}")
        
        # Create flow controller
        flow_controller = DiaryFlowController(db)
        
        # Get recent session
        recent_session = db.query(DiarySession).filter(
            DiarySession.user_id == user.id
        ).order_by(DiarySession.created_at.desc()).first()
        
        if not recent_session:
            print("❌ No recent session found")
            return False
        
        print(f"✅ Found recent session {recent_session.id}")
        print(f"   Created: {recent_session.created_at}")
        print(f"   Phase: {recent_session.current_phase}")
        print(f"   Intent: {recent_session.current_intent}")
        print(f"   Complete: {recent_session.is_complete}")
        print(f"   Structured data: {recent_session.structured_data}")
        
        # Test updating the session directly
        print(f"\n🔧 Testing direct session update...")
        
        # Update structured data
        test_data = {
            "mood": "Test mood data",
            "activities": "Test activities data"
        }
        
        recent_session.structured_data = test_data
        recent_session.current_phase = "guide"
        recent_session.current_intent = "ASK_MOOD"
        
        print(f"   Before commit - structured_data: {recent_session.structured_data}")
        
        # Commit
        db.commit()
        
        print(f"   After commit - structured_data: {recent_session.structured_data}")
        
        # Refresh from database
        db.refresh(recent_session)
        print(f"   After refresh - structured_data: {recent_session.structured_data}")
        
        # Test retrieving in new session
        print(f"\n🔍 Testing retrieval in new database session...")
        db2 = next(get_db())
        session_from_db = db2.query(DiarySession).filter(
            DiarySession.id == recent_session.id
        ).first()
        
        if session_from_db:
            print(f"   Retrieved session {session_from_db.id}")
            print(f"   Phase: {session_from_db.current_phase}")
            print(f"   Intent: {session_from_db.current_intent}")
            print(f"   Structured data: {session_from_db.structured_data}")
        else:
            print("   ❌ Could not retrieve session from new database session")
        
        db2.close()
        
        # Test the flow controller process
        print(f"\n🔄 Testing flow controller process...")
        
        # Reset to clean state
        recent_session.structured_data = {}
        recent_session.current_phase = "guide"
        recent_session.current_intent = "ASK_MOOD"
        db.commit()
        
        # Process a message
        test_message = "I'm feeling excited but nervous about my trip."
        print(f"   Processing message: {test_message}")
        
        response, is_complete = flow_controller.process_user_message(
            recent_session, test_message, "llama3.1:8b"
        )
        
        print(f"   Response: {response[:100]}...")
        print(f"   Complete: {is_complete}")
        print(f"   Session phase: {recent_session.current_phase}")
        print(f"   Session intent: {recent_session.current_intent}")
        print(f"   Session structured_data: {recent_session.structured_data}")
        
        # Check if it's actually in the database
        db.refresh(recent_session)
        print(f"   After refresh - structured_data: {recent_session.structured_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_db_session()