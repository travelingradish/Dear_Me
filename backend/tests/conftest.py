"""
Pytest configuration and fixtures for the Daily Check-in app tests.
This file provides database fixtures, test client setup, and user fixtures.
"""

import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from faker import Faker

# Add backend to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import Base, SessionLocal
from app.models.models import User, DiarySession, ConversationMessage, UserMemory
from app.core.auth import get_password_hash, create_access_token

# Import get_db and app from main
import sys
import os
main_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, main_path)

from main import app, get_db

fake = Faker()

@pytest.fixture(scope="session")
def test_db_url():
    """Create a temporary database file for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    yield f"sqlite:///{db_path}"
    # Clean up
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create a test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    return engine

@pytest.fixture(scope="session")
def test_sessionmaker(test_engine):
    """Create a test database session maker."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session(test_engine, test_sessionmaker):
    """
    Create a fresh database session for each test.
    This fixture creates all tables, yields a session, and cleans up after.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    session = test_sessionmaker()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a FastAPI test client with database dependency override.
    """
    def get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = get_test_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Generate test user data."""
    return {
        "username": fake.user_name(),
        "password": "TestPass123!",
        "age": fake.random_int(min=18, max=80),
        "ai_character_name": fake.first_name(),
        "email": fake.email()  # Add email for test compatibility
    }

@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    user = User(
        username=test_user_data["username"],
        age=test_user_data["age"],
        hashed_password=get_password_hash(test_user_data["password"]),
        ai_character_name=test_user_data["ai_character_name"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Add the plain password and email for testing
    user.plain_password = test_user_data["password"]
    user.email = test_user_data["email"]  # Add email attribute for test compatibility
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for API requests."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_diary_session(db_session, test_user):
    """Create a test diary session."""
    session = DiarySession(
        user_id=test_user.id,
        language="en",
        current_phase="guide",
        current_intent="ASK_MOOD",
        structured_data={},
        is_complete=False
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session

@pytest.fixture
def sample_conversation_messages():
    """Sample conversation data for testing."""
    return [
        {
            "role": "assistant",
            "content": "Hi, AI Assistant here. How are you feeling today?",
            "intent": "ASK_MOOD"
        },
        {
            "role": "user", 
            "content": "I'm feeling pretty good today, a bit excited!",
            "intent": None
        },
        {
            "role": "assistant",
            "content": "That's wonderful to hear! What activities did you do today?",
            "intent": "ASK_ACTIVITIES"
        }
    ]

@pytest.fixture
def mock_llm_response():
    """Mock LLM service response for testing."""
    return {
        "response": "That sounds like a great day! I'm glad you're feeling excited.",
        "next_intent": "ASK_ACTIVITIES",
        "slot_updates": {"mood": "good, excited"},
        "is_crisis": False,
        "phase_complete": False
    }

# Markers for test organization
pytest_plugins = []