from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
import uvicorn

from database import SessionLocal, engine, Base
from models import User, Conversation, DiaryEntry, DiarySession, ConversationMessage
from schemas import UserCreate, UserLogin, ConversationCreate, DiaryCreate, GuidedChatMessage, DiaryEditRequest, GuidedSessionStart
from auth import create_access_token, verify_token, get_password_hash, verify_password
from llm_service import OllamaLLMService
from diary_flow_controller import DiaryFlowController

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daily Check-in API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize LLM service
llm_service = OllamaLLMService()

# Security
security = HTTPBearer()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@app.get("/")
async def root():
    return {"message": "Daily Check-in API v2.0", "status": "running"}

@app.options("/auth/register")
async def options_register():
    return {"message": "OK"}

@app.post("/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

@app.options("/auth/login")
async def options_login():
    return {"message": "OK"}

@app.post("/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}

@app.get("/llm/models/{language}")
async def get_models(language: str):
    models = llm_service.get_available_models(language)
    return {"success": True, "models": models}

@app.post("/llm/conversation")
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Generate LLM response
        response = llm_service.generate_conversation_response(
            message=conversation_data.message,
            conversation_history=conversation_data.conversation_history,
            language=conversation_data.language,
            model_name=conversation_data.model
        )
        
        # Save conversation to database
        conversation = Conversation(
            user_id=current_user.id,
            message=conversation_data.message,
            response=response,
            language=conversation_data.language
        )
        db.add(conversation)
        db.commit()
        
        return {"success": True, "response": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diary/generate")
async def generate_diary(
    diary_data: DiaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Generate diary entry
        diary_content = llm_service.generate_diary_entry(
            answers=diary_data.answers,
            conversation_history=diary_data.conversation_history,
            language=diary_data.language,
            tone=diary_data.tone
        )
        
        # Save diary entry
        diary_entry = DiaryEntry(
            user_id=current_user.id,
            content=diary_content,
            answers=diary_data.answers,
            language=diary_data.language,
            tone=diary_data.tone
        )
        db.add(diary_entry)
        db.commit()
        
        return {"success": True, "diary": diary_content, "entry_id": diary_entry.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).limit(50).all()
    
    return {"success": True, "conversations": conversations}

@app.get("/diary/entries")
async def get_diary_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == current_user.id
    ).order_by(DiaryEntry.created_at.desc()).limit(20).all()
    
    return {"success": True, "entries": entries}

@app.get("/diary/dates")
async def get_diary_dates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dates that have diary entries for calendar display"""
    
    dates = db.query(
        func.date(DiaryEntry.created_at).label('date')
    ).filter(
        DiaryEntry.user_id == current_user.id
    ).distinct().all()
    
    # Convert to list of date strings
    date_strings = [str(date.date) for date in dates]
    
    return {"success": True, "dates": date_strings}

@app.get("/diary/by-date/{date}")
async def get_diary_by_date(
    date: str,  # Format: YYYY-MM-DD
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get diary entries for a specific date"""
    try:
        from datetime import datetime
        
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get entries for that date
        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == current_user.id,
            func.date(DiaryEntry.created_at) == target_date
        ).order_by(DiaryEntry.created_at.desc()).all()
        
        return {"success": True, "entries": entries, "date": date}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

# Guided Diary Conversation Endpoints

@app.post("/guided-diary/start")
async def start_guided_diary(
    session_data: GuidedSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new guided diary conversation session"""
    try:
        flow_controller = DiaryFlowController(db)
        session = flow_controller.start_diary_session(current_user, session_data.language, session_data.model)
        
        # Get the initial greeting message
        conversation_history = flow_controller.get_conversation_history(session)
        initial_message = conversation_history[-1] if conversation_history else None
        
        return {
            "success": True,
            "session_id": session.id,
            "initial_message": initial_message['content'] if initial_message else "Hello! Let's reflect on your day.",
            "language": session.language,
            "current_intent": session.current_intent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/guided-diary/{session_id}/message")
async def send_guided_message(
    session_id: int,
    message_data: GuidedChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in guided diary conversation"""
    try:
        flow_controller = DiaryFlowController(db)
        session = flow_controller.get_session_by_id(session_id, current_user.id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Process the user message
        assistant_response, is_complete = flow_controller.process_user_message(
            session, message_data.message, message_data.model
        )
        
        return {
            "success": True,
            "response": assistant_response,
            "is_complete": is_complete,
            "is_crisis": session.is_crisis,
            "current_phase": session.current_phase,
            "current_intent": session.current_intent,
            "structured_data": session.structured_data,
            "composed_diary": session.composed_diary,
            "final_diary": session.final_diary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/guided-diary/{session_id}")
async def get_guided_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get guided diary session details"""
    try:
        flow_controller = DiaryFlowController(db)
        session = flow_controller.get_session_by_id(session_id, current_user.id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        conversation_history = flow_controller.get_conversation_history(session)
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "language": session.language,
                "current_phase": session.current_phase,
                "current_intent": session.current_intent,
                "structured_data": session.structured_data,
                "composed_diary": session.composed_diary,
                "final_diary": session.final_diary,
                "is_complete": session.is_complete,
                "is_crisis": session.is_crisis,
                "created_at": session.created_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            },
            "conversation_history": conversation_history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/guided-diary/{session_id}/edit")
async def edit_diary_entry(
    session_id: int,
    edit_request: DiaryEditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit the final diary entry"""
    try:
        flow_controller = DiaryFlowController(db)
        session = flow_controller.get_session_by_id(session_id, current_user.id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session.is_complete:
            raise HTTPException(status_code=400, detail="Session not complete yet")
        
        # Update the final diary
        flow_controller.update_final_diary(session, edit_request.edited_content)
        
        return {
            "success": True,
            "final_diary": session.final_diary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/guided-diary-session/active")
async def get_active_guided_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active guided diary session for current user"""
    try:
        flow_controller = DiaryFlowController(db)
        session = flow_controller.get_active_session(current_user.id)
        
        if not session:
            return {"success": True, "session": None}
        
        conversation_history = flow_controller.get_conversation_history(session)
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "language": session.language,
                "current_phase": session.current_phase,
                "current_intent": session.current_intent,
                "structured_data": session.structured_data,
                "composed_diary": session.composed_diary,
                "final_diary": session.final_diary,
                "is_complete": session.is_complete,
                "is_crisis": session.is_crisis,
                "created_at": session.created_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            },
            "conversation_history": conversation_history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced diary dates endpoint for guided sessions
@app.get("/guided-diary-calendar/dates")
async def get_guided_diary_dates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dates that have completed guided diary sessions for calendar display"""
    
    dates = db.query(
        func.date(DiarySession.completed_at).label('date')
    ).filter(
        DiarySession.user_id == current_user.id,
        DiarySession.is_complete == True,
        DiarySession.completed_at.isnot(None)
    ).distinct().all()
    
    # Convert to list of date strings
    date_strings = [str(date.date) for date in dates]
    
    return {"success": True, "dates": date_strings}

@app.get("/guided-diary-calendar/by-date/{date}")
async def get_guided_diary_by_date(
    date: str,  # Format: YYYY-MM-DD
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get guided diary sessions for a specific date"""
    try:
        from datetime import datetime
        
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get sessions for that date
        sessions = db.query(DiarySession).filter(
            DiarySession.user_id == current_user.id,
            func.date(DiarySession.completed_at) == target_date,
            DiarySession.is_complete == True
        ).order_by(DiarySession.completed_at.desc()).all()
        
        session_data = []
        for session in sessions:
            session_data.append({
                "id": session.id,
                "language": session.language,
                "structured_data": session.structured_data,
                "composed_diary": session.composed_diary,
                "final_diary": session.final_diary,
                "is_crisis": session.is_crisis,
                "completed_at": session.completed_at.isoformat()
            })
        
        return {"success": True, "sessions": session_data, "date": date}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)