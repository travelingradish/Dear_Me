from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    diary_sessions = relationship("DiarySession", back_populates="user")
    diary_entries = relationship("DiaryEntry", back_populates="user")  # Keep for backward compatibility

class DiarySession(Base):
    __tablename__ = "diary_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(10), default="en")
    current_phase = Column(String(20), default="guide")  # guide, compose, complete, crisis
    current_intent = Column(String(50), default="ASK_MOOD")  # ASK_MOOD, ASK_ACTIVITIES, etc.
    structured_data = Column(JSON)  # The extracted slots: mood, activities, etc.
    composed_diary = Column(Text)  # Original composed diary from LLM
    final_diary = Column(Text)  # User-edited version (defaults to composed_diary)
    is_complete = Column(Boolean, default=False)
    is_crisis = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="diary_sessions")
    conversation_messages = relationship("ConversationMessage", back_populates="diary_session")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    diary_session_id = Column(Integer, ForeignKey("diary_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    intent = Column(String(50))  # What the assistant was trying to accomplish
    slot_updates = Column(JSON)  # What slots were updated by this message
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    diary_session = relationship("DiarySession", back_populates="conversation_messages")

# Legacy models (keep for backward compatibility)
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    answers = Column(JSON)  # Store conversation answers as JSON
    language = Column(String(10), default="en")
    tone = Column(String(20), default="reflective")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="diary_entries")