#!/usr/bin/env python3
"""Script to delete the problematic diary entry"""

import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

from database import SessionLocal
from models import User, DiaryEntry
from sqlalchemy.orm import Session

def delete_problematic_entry():
    """Delete the problematic diary entry with ID 1"""
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Find and delete the problematic entry
        entry = db.query(DiaryEntry).filter(DiaryEntry.id == 1).first()
        
        if entry:
            print(f"Found problematic entry:")
            print(f"ID: {entry.id}")
            print(f"Date: {entry.created_at}")
            print(f"Content preview: {entry.content[:100]}...")
            
            db.delete(entry)
            db.commit()
            print("✅ Problematic entry deleted successfully!")
            return True
        else:
            print("Entry not found.")
            return False
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    delete_problematic_entry()