#!/usr/bin/env python3
"""Script to create test diary entries for calendar functionality testing"""

import sys
import os
from datetime import datetime, timedelta
import requests

# Add the backend directory to Python path
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

from app.core.database import SessionLocal
from app.models.models import User, DiaryEntry
from sqlalchemy.orm import Session

def create_test_diaries():
    """Create test diary entries for different dates"""
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get the test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("Test user not found. Please register first.")
            return False
            
        # Create diary entries for the last few days
        test_diaries = [
            {
                "date": datetime.now() - timedelta(days=2),
                "content": "Today was an amazing day! I learned so much about React and FastAPI. The weather was beautiful and I took a long walk in the park. I'm grateful for the opportunity to work on interesting projects and expand my skills.",
                "language": "en"
            },
            {
                "date": datetime.now() - timedelta(days=1),
                "content": "Had a productive day working on the daily check-in application. Implemented the LLM integration and spent time with friends in the evening. Feeling accomplished and happy about the progress made.",
                "language": "en"
            },
            {
                "date": datetime.now(),
                "content": "Today I focused on adding calendar functionality to the application. It's exciting to see all the features coming together. I'm looking forward to testing everything and making sure it works perfectly for users.",
                "language": "en"
            }
        ]
        
        for diary_data in test_diaries:
            # Create diary entry
            diary_entry = DiaryEntry(
                user_id=user.id,
                content=diary_data["content"],
                answers={"test_response": "This is a test diary entry"},
                language=diary_data["language"],
                tone="reflective",
                created_at=diary_data["date"]
            )
            db.add(diary_entry)
        
        db.commit()
        print(f"Successfully created {len(test_diaries)} test diary entries!")
        
        # List all diary entries for this user
        entries = db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).all()
        print(f"\nTotal diary entries for user: {len(entries)}")
        for entry in entries:
            print(f"- {entry.created_at.strftime('%Y-%m-%d')}: {entry.content[:50]}...")
            
        return True
        
    except Exception as e:
        print(f"Error creating test diaries: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = create_test_diaries()
    if success:
        print("\n✅ Test diary entries created successfully!")
        print("Now you can test the calendar functionality at http://localhost:3000")
    else:
        print("❌ Failed to create test diary entries")