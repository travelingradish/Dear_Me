from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

# Helper function for timezone-aware UTC timestamps
def utc_now():
    """Return timezone-aware UTC timestamp for database defaults"""
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)  # Optional age for age-appropriate conversations
    hashed_password = Column(String(128), nullable=False)
    ai_character_name = Column(String(100), default="AI Assistant", nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    # Relationships
    diary_sessions = relationship("DiarySession", back_populates="user")
    diary_entries = relationship("DiaryEntry", back_populates="user")  # Keep for backward compatibility
    memories = relationship("UserMemory", back_populates="user")
    memory_snapshots = relationship("MemorySnapshot", back_populates="user")

class DiarySession(Base):
    __tablename__ = "diary_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(10), default="en")
    current_phase = Column(String(20), default="guide")  # guide, compose, complete, crisis
    current_intent = Column(String(50), default="ASK_MOOD")  # ASK_MOOD, ASK_ACTIVITIES, etc.
    structured_data = Column(JSON, default=dict)  # The extracted slots: mood, activities, etc.
    composed_diary = Column(Text)  # Original composed diary from LLM
    final_diary = Column(Text)  # User-edited version (defaults to composed_diary)
    is_complete = Column(Boolean, default=False)
    is_crisis = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
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
    created_at = Column(DateTime, default=utc_now)
    
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
    created_at = Column(DateTime, default=utc_now)

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    answers = Column(JSON)  # Store conversation answers as JSON
    conversation_history = Column(JSON)  # Store full conversation history for viewing
    language = Column(String(10), default="en")
    tone = Column(String(20), default="reflective")
    created_at = Column(DateTime, default=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="diary_entries")

class UserMemory(Base):
    __tablename__ = "user_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)  # personal_info, preferences, relationships, goals, challenges, interests
    memory_key = Column(String(100), nullable=False)  # e.g., "pet_cat", "work_stress", "morning_routine"
    memory_value = Column(Text, nullable=False)  # The actual memory content
    confidence_score = Column(Float, default=1.0)  # 0.0 to 1.0, higher means more confident
    source_type = Column(String(20), default="conversation")  # conversation, diary, explicit
    first_mentioned = Column(DateTime, default=utc_now)
    last_updated = Column(DateTime, default=utc_now)
    mention_count = Column(Integer, default=1)  # How many times this memory was reinforced
    is_active = Column(Boolean, default=True)  # Can be deactivated without deletion
    is_sensitive = Column(Boolean, default=False)  # Mark sensitive information
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    @property
    def content(self):
        """Alias for memory_value for test compatibility"""
        return self.memory_value
    
    @property
    def confidence(self):
        """Alias for confidence_score for test compatibility"""
        return self.confidence_score

class MemorySnapshot(Base):
    __tablename__ = "memory_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    diary_session_id = Column(Integer, ForeignKey("diary_sessions.id"), nullable=True)  # Can be null for simple chat
    extracted_memories = Column(JSON)  # List of new/updated memories from this session
    memory_context = Column(JSON)  # Memories that were active/used in this session
    session_summary = Column(Text)  # Brief summary of the session for memory context
    created_at = Column(DateTime, default=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="memory_snapshots")
    diary_session = relationship("DiarySession")