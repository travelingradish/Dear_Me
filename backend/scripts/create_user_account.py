#!/usr/bin/env python3
"""
Create or reset user account
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import User
from app.core.auth import get_password_hash

def list_existing_users():
    """List all existing users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("📋 Existing users in database:")
        if not users:
            print("  No users found.")
        else:
            for user in users:
                print(f"  ID: {user.id}, Username: {user.username}, Email: {user.email}")
        return users
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []
    finally:
        db.close()

def create_or_reset_user(username, email, password):
    """Create new user or reset existing user password"""
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            # Reset password for existing user
            print(f"🔄 User {email} exists. Resetting password...")
            hashed_password = get_password_hash(password)
            existing_user.hashed_password = hashed_password
            db.commit()
            print(f"✅ Password reset successfully for {existing_user.username} ({existing_user.email})!")
            return existing_user
        else:
            # Create new user
            print(f"👤 Creating new user account for {email}...")
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                ai_character_name="AI Assistant"  # Default character name
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"✅ New user created successfully!")
            print(f"  ID: {new_user.id}")
            print(f"  Username: {new_user.username}")
            print(f"  Email: {new_user.email}")
            print(f"  AI Character: {new_user.ai_character_name}")
            return new_user
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 User Account Recovery/Creation Tool")
    print("=" * 50)
    
    # First, list existing users
    list_existing_users()
    
    # Create or reset the specific account
    print(f"\n🎯 Target Account Recovery:")
    email = "wen@example.com"
    username = "wen"
    password = "091283"
    
    user = create_or_reset_user(username, email, password)
    
    if user:
        print(f"\n🎉 Account recovery completed!")
        print(f"Login credentials:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Username: {user.username}")
        print(f"\nYou can now log in at: http://localhost:3000")
    else:
        print(f"\n💔 Account recovery failed!")