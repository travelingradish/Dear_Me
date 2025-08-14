from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Conversation schemas
class ConversationCreate(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]] = []
    language: str = "en"
    model: str = "gemma3:4b"

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
    model: str = "gemma3:4b"

class GuidedSessionStart(BaseModel):
    language: str = "en"
    model: str = "gemma3:4b"

class DiaryEditRequest(BaseModel):
    edited_content: str

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