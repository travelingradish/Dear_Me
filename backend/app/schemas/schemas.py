from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# User schemas
class UserCreate(BaseModel):
    username: str
    age: Optional[int] = None
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username cannot exceed 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None:
            if v < 8:
                raise ValueError('Age must be at least 8 years old')
            if v > 120:
                raise ValueError('Age must be realistic (under 120)')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password cannot exceed 128 characters')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    age: Optional[int]
    ai_character_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CharacterNameUpdate(BaseModel):
    character_name: str
    
    @validator('character_name')
    def validate_character_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Character name cannot be empty')
        v = v.strip()
        if len(v) > 100:
            raise ValueError('Character name cannot exceed 100 characters')
        return v

# Conversation schemas
class ConversationCreate(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []
    language: str = "en"

class ConversationResponse(BaseModel):
    id: int
    message: str
    response: str
    language: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Diary schemas
class DiaryCreate(BaseModel):
    answers: Dict[str, Any]
    conversation_history: List[Dict[str, Any]] = []
    language: str = "en"
    tone: str = "reflective"

class DiaryResponse(BaseModel):
    id: int
    content: str
    answers: Dict[str, Any]
    language: str
    tone: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Guided conversation schemas
class GuidedChatMessage(BaseModel):
    message: str
    language: str = "en"

class GuidedSessionStart(BaseModel):
    language: str = "en"

class DiaryEditRequest(BaseModel):
    content: str

class DiarySessionResponse(BaseModel):
    id: int
    language: str
    current_phase: str
    current_intent: str
    structured_data: Optional[Dict[str, Any]]
    composed_diary: Optional[str]
    final_diary: Optional[str]
    is_complete: bool
    is_crisis: bool
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True