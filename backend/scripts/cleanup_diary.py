#!/usr/bin/env python3
"""Script to clean up problematic diary entries and show current entries"""

import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

from database import SessionLocal
from models import User, DiaryEntry
from sqlalchemy.orm import Session

def cleanup_and_show_diaries():
    """Clean up problematic entries and show current diary entries"""
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get the test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("Test user not found.")
            return False
            
        # Get all diary entries for this user
        entries = db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).all()
        
        print(f"Found {len(entries)} diary entries for user:")
        
        for entry in entries:
            print(f"\n=== Entry ID: {entry.id} ===")
            print(f"Date: {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"Language: {entry.language}")
            print(f"Content preview: {entry.content[:100]}...")
            
            # Check if this entry contains problematic content
            if "July" in entry.content or "Nova" in entry.content or len(entry.content) > 500:
                print("🚨 PROBLEMATIC ENTRY DETECTED!")
                print(f"Full content: {entry.content}")
                
                response = input("Delete this entry? (y/n): ")
                if response.lower() == 'y':
                    db.delete(entry)
                    print("✅ Entry deleted.")
        
        db.commit()
        
        print("\n=== CLEANUP COMPLETE ===")
        
        # Show remaining entries
        remaining = db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).all()
        print(f"Remaining entries: {len(remaining)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_and_show_diaries()