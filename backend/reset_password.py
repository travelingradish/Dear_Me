#!/usr/bin/env python3
"""
Simple password reset script for daily check-in app
Usage: python3 reset_password.py
"""

from database import SessionLocal
from models import User
from auth import get_password_hash

def reset_user_password():
    db = SessionLocal()
    
    try:
        # Show available users
        users = db.query(User).all()
        print("Available users:")
        for user in users:
            print(f"  {user.id}: {user.username} ({user.email})")
        
        # Get user selection
        while True:
            try:
                user_id = int(input("\nEnter user ID to reset password: "))
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    break
                else:
                    print("User not found. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get new password
        new_password = input(f"\nEnter new password for {user.username}: ")
        confirm_password = input("Confirm password: ")
        
        if new_password != confirm_password:
            print("Passwords don't match!")
            return
        
        if len(new_password) < 6:
            print("Password must be at least 6 characters long!")
            return
        
        # Update password
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        db.commit()
        
        print(f"\n✅ Password updated successfully for {user.username}!")
        print("You can now log in with your new password.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_user_password()