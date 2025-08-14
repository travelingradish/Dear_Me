#!/usr/bin/env python3
"""Script to find all diary entries in database"""

import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

from database import SessionLocal
from models import User, DiaryEntry
from sqlalchemy.orm import Session

def find_all_diaries():
    """Find all diary entries in the database"""
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        print(f"Found {len(users)} users in database")
        
        for user in users:
            print(f"\n=== USER: {user.username} ({user.email}) ===")
            
            # Get all diary entries for this user
            entries = db.query(DiaryEntry).filter(DiaryEntry.user_id == user.id).all()
            print(f"Diary entries: {len(entries)}")
            
            for entry in entries:
                print(f"\n--- Entry ID: {entry.id} ---")
                print(f"Date: {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"Language: {entry.language}")
                
                # Check for problematic content
                if "July" in entry.content or "Nova" in entry.content:
                    print("🚨 CONTAINS JULY/NOVA CONTENT!")
                    print(f"FULL CONTENT:\n{entry.content}")
                    
                    response = input("Delete this entry? (y/n): ")
                    if response.lower() == 'y':
                        db.delete(entry)
                        db.commit()
                        print("✅ Deleted!")
                        continue
                
                print(f"Content: {entry.content[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    find_all_diaries()