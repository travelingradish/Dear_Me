#!/usr/bin/env python3
"""
Development setup script to manage database and testing without affecting production data.
"""

import sys
import os
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import User
from auth import get_password_hash

def backup_database():
    """Backup the current database"""
    if os.path.exists("dear_me.db"):
        backup_name = f"dear_me_backup_{int(__import__('time').time())}.db"
        shutil.copy2("dear_me.db", backup_name)
        print(f"✅ Database backed up to: {backup_name}")
        return backup_name
    return None

def create_test_database():
    """Create a separate test database"""
    # Use a different database for testing
    os.environ['DATABASE_URL'] = 'sqlite:///test_dear_me.db'
    
    # Create test tables
    Base.metadata.create_all(bind=engine)
    print("✅ Test database created: test_dear_me.db")

def ensure_production_user():
    """Ensure the production user exists"""
    db = SessionLocal()
    try:
        # Check if Wen's account exists
        user = db.query(User).filter(User.username == "Wen").first()
        if not user:
            # Create the user
            user = User(
                username="Wen",
                email="wen@example.com",
                hashed_password=get_password_hash("091283")
            )
            db.add(user)
            db.commit()
            print("✅ Created production user: Wen")
        else:
            print("✅ Production user exists: Wen")
    finally:
        db.close()

def setup_development_environment():
    """Set up development environment with proper data separation"""
    print("🛠️ Setting up development environment...")
    
    # Backup current database
    backup_file = backup_database()
    
    # Ensure production user exists
    ensure_production_user()
    
    # Create gitignore entries for database files
    gitignore_content = """
# Database files
dear_me.db
dear_me_backup_*.db
test_dear_me.db

# Test files
test_memory_*.py
create_memory_tables.py
"""
    
    with open(".gitignore", "a") as f:
        f.write(gitignore_content)
    
    print("✅ Development environment configured")
    print("📝 Recommendations:")
    print("  - Use test_dear_me.db for testing")
    print("  - Production data preserved in dear_me.db")
    print("  - Database backups created automatically")
    
    return backup_file

if __name__ == "__main__":
    setup_development_environment()