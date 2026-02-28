from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timezone
from typing import Optional
import uvicorn
import logging

from app.core.database import SessionLocal, engine, Base
from app.models.models import User, Conversation, DiaryEntry, DiarySession, ConversationMessage, UserMemory, MemorySnapshot
from app.schemas.schemas import UserCreate, UserLogin, ConversationCreate, DiaryCreate, GuidedChatMessage, DiaryEditRequest, GuidedSessionStart, CharacterNameUpdate
from app.core.auth import create_access_token, verify_token, get_password_hash, verify_password
from app.services.llm_service import OllamaLLMService
from app.services.diary_flow_controller import DiaryFlowController
from app.services.memory_service import MemoryService

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daily Check-in API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # Local dev + mobile WiFi access
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize services
llm_service = OllamaLLMService()
memory_service = MemoryService()

# Security
security = HTTPBearer()

# Helper function to get user age (returns None if not provided)
def get_user_age(user: User) -> Optional[int]:
    return user.age

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

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user exists (explicit checks before database operations)
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            age=user_data.age,
            hashed_password=hashed_password,
            ai_character_name="AI Assistant"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "age": user.age, "ai_character_name": user.ai_character_name}
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (our validation errors)
        raise
    except IntegrityError as e:
        # Handle database constraint violations
        db.rollback()
        error_msg = str(e.orig).lower()
        if "username" in error_msg:
            raise HTTPException(status_code=400, detail="Username already taken")
        else:
            raise HTTPException(status_code=400, detail="Registration failed due to duplicate data")
    except SQLAlchemyError as e:
        # Handle other database errors
        db.rollback()
        logging.error(f"Database error during registration: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        logging.error(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.options("/auth/login")
async def options_login():
    return {"message": "OK"}

@app.post("/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "age": user.age, "ai_character_name": user.ai_character_name}
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    print(f"AUTH/ME: Current user is {current_user.id} ({current_user.username}, age {current_user.age})")
    return {
        "id": current_user.id, 
        "username": current_user.username, 
        "age": current_user.age,
        "ai_character_name": current_user.ai_character_name,
        "email": getattr(current_user, 'email', f"{current_user.username}@example.com")  # Add email field for test compatibility
    }

@app.put("/auth/character-name")
async def update_character_name(
    character_update: CharacterNameUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        current_user.ai_character_name = character_update.character_name
        db.commit()
        db.refresh(current_user)
        return {
            "message": "Character name updated successfully",
            "character_name": current_user.ai_character_name
        }
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating character name: {e}")
        raise HTTPException(status_code=500, detail="Failed to update character name")

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
        # Get relevant memories for context with time awareness
        current_time = datetime.now(timezone.utc)  # Use timezone-aware UTC
        user_memories = memory_service.get_relevant_memories(
            current_user.id, conversation_data.message, db,
            current_time=current_time, conversation_type="current"
        )

        # Debug logging for memories
        print(f"MEMORY DEBUG: User query: {conversation_data.message}")
        print(f"MEMORY DEBUG: Found {len(user_memories)} memories:")
        for i, memory in enumerate(user_memories, 1):
            print(f"  {i}. [{memory.category}] {memory.memory_value}")

        # Generate LLM response with memory context
        character_name = current_user.ai_character_name or "AI Assistant"

        # Debug log the LLM call
        print(f"LLM DEBUG: Calling LLM with {len(user_memories)} memories, character: {character_name}")

        # Convert memory objects to strings for LLM
        memory_strings = [memory.memory_value for memory in user_memories] if user_memories else None

        response = llm_service.generate_conversation_response(
            message=conversation_data.message,
            conversation_history=conversation_data.conversation_history,
            language=conversation_data.language,
            model_name=conversation_data.model,
            user_memories=memory_strings,
            character_name=character_name,
            user_age=get_user_age(current_user),
            current_time=current_time
        )

        # Debug log the LLM response
        print(f"LLM DEBUG: LLM responded with: {response[:200]}...")
        
        # Extract and store new memories from USER MESSAGE ONLY (not AI response)
        extracted_memories = memory_service.extract_memories_from_text(
            conversation_data.message, current_user.id, "conversation"
        )
        if extracted_memories:
            memory_service.store_memories_internal(db, current_user.id, extracted_memories)
        
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
        import traceback
        logging.error(f"Error in /llm/conversation: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diary/generate")
async def generate_diary(
    diary_data: DiaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Generate diary entry using existing LLM service
        diary_content = llm_service.generate_diary_entry(
            conversation_history=diary_data.conversation_history,
            language=diary_data.language,
            user_age=get_user_age(current_user),
            ai_character_name=current_user.ai_character_name or "AI Assistant"
        )
        
        # Save diary entry
        diary_entry = DiaryEntry(
            user_id=current_user.id,
            content=diary_content,
            answers=diary_data.answers,
            conversation_history=diary_data.conversation_history,
            language=diary_data.language,
            tone=diary_data.tone
        )
        db.add(diary_entry)
        db.commit()
        
        return {"success": True, "diary": diary_content, "entry_id": diary_entry.id}

    except Exception as e:
        import traceback
        error_details = f"Diary generation error: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(f"DIARY ERROR: {error_details}")
        logging.error(error_details)
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
        model = getattr(session_data, 'model', 'llama3.1:8b')
        session = flow_controller.start_diary_session(current_user, session_data.language, model)
        
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
        import traceback
        print(f"ERROR in start_guided_diary: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/guided-diary/{session_id}/message")
async def send_guided_message(
    session_id: int,
    message_data: GuidedChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in guided diary conversation with enhanced graph-based routing"""
    try:
        # Validate message is not empty
        if not message_data.message or message_data.message.strip() == "":
            raise HTTPException(status_code=422, detail="Message cannot be empty")

        flow_controller = DiaryFlowController(db)
        session = flow_controller.get_session_by_id(session_id, current_user.id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Integrate GraphConversationService for enhanced conversation routing
        try:
            from app.services.graph_conversation_service import GraphConversationService

            # Use hybrid approach: Graph service for routing, flow controller for session management
            graph_service = GraphConversationService(db)

            # Get graph-based insights and contextual memory analysis
            graph_result = graph_service.process_conversation(session_id, message_data.message)

            # Use graph insights to enhance the flow controller decision
            enhanced_context = {
                "graph_insights": graph_result.get("insights", {}),
                "memory_context": graph_result.get("metadata", {}),
                "emotional_state": graph_result.get("insights", {}).get("emotional_state", "neutral")
            }

            # Process through enhanced flow controller with graph context
            model = getattr(message_data, 'model', 'llama3.1:8b')
            try:
                # Try enhanced method if available
                if hasattr(flow_controller, 'process_user_message_with_context'):
                    result = flow_controller.process_user_message_with_context(
                        session.id, message_data.message, model, enhanced_context
                    )
                else:
                    result = flow_controller.process_user_message(
                        session.id, message_data.message, model
                    )
            except (AttributeError, TypeError):
                # Fallback to original method
                result = flow_controller.process_user_message(
                    session.id, message_data.message, model
                )

        except ImportError:
            # Fallback if GraphConversationService is not available
            model = getattr(message_data, 'model', 'llama3.1:8b')
            result = flow_controller.process_user_message(
                session.id, message_data.message, model
            )

        assistant_response = result["response"]
        is_complete = result["phase_complete"]

        # Refresh session object to get updated state after message processing
        db.refresh(session)
        
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
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 422) as-is
        raise
    except Exception as e:
        # Log the error and return 500 for unexpected exceptions
        import logging
        logging.error(f"Unexpected error in send_guided_message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
            "conversation_history": conversation_history,
            # Top-level fields for test compatibility
            "final_diary": session.final_diary,
            "is_complete": session.is_complete
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) as-is  
        raise
    except Exception as e:
        import logging
        logging.error(f"Unexpected error in get_guided_session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        flow_controller.update_final_diary(session, edit_request.content)
        
        return {
            "success": True,
            "message": "Diary entry updated successfully",
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

# Graph Conversation Service with Enhanced Memory Integration
@app.post("/graph-conversation/{session_id}/message")
async def process_graph_conversation_message(
    session_id: int,
    message: GuidedChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process message through the graph conversation system with contextual memory integration
    and dynamic follow-up question generation
    """
    try:
        from app.services.graph_conversation_service import GraphConversationService
        from app.services.contextual_memory_service import ContextualMemoryService

        # Verify session belongs to current user
        session = db.query(DiarySession).filter(
            DiarySession.id == session_id,
            DiarySession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Initialize graph conversation service
        graph_conversation = GraphConversationService(db)
        contextual_memory = ContextualMemoryService()

        # Get enhanced memory context
        memory_context = contextual_memory.get_contextual_memories_with_insights(
            user_id=current_user.id,
            current_message=message.content,
            db=db,
            conversation_history=None,  # We can add this later
            limit=10
        )

        # Process through graph conversation service
        result = graph_conversation.process_conversation(session_id, message.content)

        # Combine results
        return {
            "success": True,
            "response": result["response"],
            "insights": result["insights"],
            "memory_context": {
                "active_memories": memory_context["memories"],
                "insights": memory_context["insights"],
                "follow_up_questions": memory_context["follow_up_questions"],
                "memory_gaps": memory_context["memory_gaps"],
                "context_summary": memory_context["context_summary"]
            },
            "metadata": result["metadata"],
            "session_status": {
                "current_phase": session.current_phase,
                "is_complete": session.is_complete,
                "is_crisis": session.is_crisis
            }
        }

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Graph conversation service not available: {str(e)}"
        )
    except Exception as e:
        import logging
        logging.error(f"Error in graph conversation processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph conversation processing error: {str(e)}")

@app.post("/graph-conversation/analyze-memory-context")
async def analyze_memory_context(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze memory context for a given message without processing through full conversation flow
    Useful for testing memory integration
    """
    try:
        from app.services.contextual_memory_service import ContextualMemoryService

        contextual_memory = ContextualMemoryService()

        message_content = request.get("message", "")
        if not message_content:
            raise HTTPException(status_code=400, detail="Message content is required")

        # Get enhanced memory context
        memory_analysis = contextual_memory.get_contextual_memories_with_insights(
            user_id=current_user.id,
            current_message=message_content,
            db=db,
            limit=15
        )

        return {
            "success": True,
            "message_analyzed": message_content,
            "memory_analysis": memory_analysis,
            "summary": {
                "memories_found": len(memory_analysis["memories"]),
                "insights_generated": len(memory_analysis["insights"]),
                "follow_up_questions": len(memory_analysis["follow_up_questions"]),
                "memory_gaps": len(memory_analysis["memory_gaps"])
            }
        }

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contextual memory service not available: {str(e)}"
        )
    except Exception as e:
        import logging
        logging.error(f"Error in memory context analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Memory analysis error: {str(e)}")

# Memory Management Endpoints
@app.get("/memory/summary")
async def get_memory_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a summary of user's memories"""
    try:
        summary = memory_service.get_user_memory_summary(db, current_user.id)
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/list")
async def get_user_memories(
    category: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's memories, optionally filtered by category"""
    try:
        categories = [category] if category else None
        memories = memory_service.get_relevant_memories(db, current_user.id, "", categories, limit)
        
        memory_data = []
        for memory in memories:
            memory_data.append({
                "id": memory.id,
                "category": memory.category,
                "memory_key": memory.memory_key,
                "memory_value": memory.memory_value,
                "confidence_score": memory.confidence_score,
                "source_type": memory.source_type,
                "first_mentioned": memory.first_mentioned.isoformat(),
                "last_updated": memory.last_updated.isoformat(),
                "mention_count": memory.mention_count,
                "is_active": memory.is_active,
                "is_sensitive": memory.is_sensitive
            })
        
        return {"success": True, "memories": memory_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memory/{memory_id}")
async def update_memory(
    memory_id: int,
    memory_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific memory"""
    try:
        memory = db.query(UserMemory).filter(
            UserMemory.id == memory_id,
            UserMemory.user_id == current_user.id
        ).first()
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Update fields
        if "memory_value" in memory_data:
            memory.memory_value = memory_data["memory_value"]
        if "is_active" in memory_data:
            memory.is_active = memory_data["is_active"]
        if "is_sensitive" in memory_data:
            memory.is_sensitive = memory_data["is_sensitive"]
        
        memory.last_updated = datetime.utcnow()
        db.commit()
        
        return {"success": True, "message": "Memory updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific memory"""
    try:
        memory = db.query(UserMemory).filter(
            UserMemory.id == memory_id,
            UserMemory.user_id == current_user.id
        ).first()
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        db.delete(memory)
        db.commit()
        
        return {"success": True, "message": "Memory deleted"}
    except HTTPException:
        raise
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

# Unified diary endpoints - combining both guided and casual modes
@app.get("/unified-diary/dates")
async def get_unified_diary_dates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dates that have diary entries from both guided sessions and casual entries"""
    from app.services.unified_calendar_service import UnifiedCalendarService
    
    calendar_service = UnifiedCalendarService(db)
    dates = calendar_service.get_diary_dates(current_user.id)
    
    return {"success": True, "dates": dates}

@app.get("/unified-diary/by-date/{date}")
async def get_unified_diary_by_date(
    date: str,  # Format: YYYY-MM-DD
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all diary entries (both guided and casual) for a specific date"""
    try:
        from datetime import datetime
        
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        unified_entries = []
        
        # Get guided diary sessions for that date
        guided_sessions = db.query(DiarySession).filter(
            DiarySession.user_id == current_user.id,
            func.date(DiarySession.completed_at) == target_date,
            DiarySession.is_complete == True
        ).order_by(DiarySession.completed_at.desc()).all()
        
        for session in guided_sessions:
            unified_entries.append({
                "id": f"guided_{session.id}",
                "mode": "guided",
                "content": session.final_diary or session.composed_diary,
                "language": session.language,
                "created_at": session.completed_at.isoformat(),
                "is_crisis": session.is_crisis,
                "structured_data": session.structured_data
            })
        
        # Get casual diary entries for that date
        casual_entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == current_user.id,
            func.date(DiaryEntry.created_at) == target_date
        ).order_by(DiaryEntry.created_at.desc()).all()
        
        for entry in casual_entries:
            # Determine the actual mode based on the answers field
            entry_mode = "casual"  # default
            if entry.answers and isinstance(entry.answers, dict):
                if entry.answers.get("mode") == "free_entry":
                    entry_mode = "free_entry"
            
            unified_entries.append({
                "id": f"{entry_mode}_{entry.id}",
                "mode": entry_mode, 
                "content": entry.content,
                "language": entry.language,
                "created_at": entry.created_at.isoformat(),
                "answers": entry.answers,
                "tone": entry.tone
            })
        
        # Sort all entries by creation time (newest first)
        unified_entries.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"success": True, "entries": unified_entries, "date": date}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

# Edit and Delete endpoints for diary entries
@app.put("/diary/entry/{entry_id}")
async def edit_diary_entry(
    entry_id: int,
    edit_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit a casual diary entry"""
    try:
        entry = db.query(DiaryEntry).filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        ).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Diary entry not found")
        
        # Update the content
        if "content" in edit_data:
            entry.content = edit_data["content"]
        
        db.commit()
        db.refresh(entry)
        
        return {"success": True, "entry": entry}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/diary/entry/{entry_id}")
async def delete_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a casual diary entry"""
    try:
        entry = db.query(DiaryEntry).filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        ).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Diary entry not found")
        
        db.delete(entry)
        db.commit()
        
        return {"success": True, "message": "Diary entry deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/diary/entry/{entry_id}/conversation")
async def get_diary_conversation(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history for a casual diary entry"""
    try:
        entry = db.query(DiaryEntry).filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        ).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Diary entry not found")
        
        conversation_history = entry.conversation_history or []
        
        return {
            "success": True, 
            "conversation_history": conversation_history,
            "entry_id": entry.id,
            "created_at": entry.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/guided-diary/session/{session_id}/final-diary")
async def edit_guided_diary_final(
    session_id: int,
    edit_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit the final diary of a guided session"""
    try:
        session = db.query(DiarySession).filter(
            DiarySession.id == session_id,
            DiarySession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Guided diary session not found")
        
        if not session.is_complete:
            raise HTTPException(status_code=400, detail="Session not complete yet")
        
        # Update the final diary
        if "final_diary" in edit_data:
            session.final_diary = edit_data["final_diary"]
        
        db.commit()
        db.refresh(session)
        
        return {"success": True, "session": session}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/guided-diary/{session_id}/delete")
async def delete_guided_diary_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a guided diary session"""
    print(f"DELETE ENDPOINT HIT: session_id={session_id}", flush=True)
    try:
        session = db.query(DiarySession).filter(
            DiarySession.id == session_id,
            DiarySession.user_id == current_user.id
        ).first()
        
        print(f"Session found: {session is not None}, user_id: {current_user.id}", flush=True)
        
        if not session:
            print(f"Session {session_id} not found for user {current_user.id}", flush=True)
            raise HTTPException(status_code=404, detail="Guided diary session not found")
        
        # Delete associated conversation messages first
        db.query(ConversationMessage).filter(
            ConversationMessage.diary_session_id == session_id
        ).delete()
        
        # Delete the session
        db.delete(session)
        db.commit()
        
        return {"success": True, "message": "Guided diary session deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DELETE ERROR: {str(e)}", flush=True)
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))

# Free Entry Mode Endpoints
@app.post("/free-entry/correct-grammar")
async def correct_grammar(
    text_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Correct grammar errors in the provided text"""
    try:
        original_text = text_data.get("text", "")
        language = text_data.get("language", "en")
        if not original_text.strip():
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Use LLM to correct grammar
        corrected_text = llm_service.correct_grammar(
            text=original_text,
            language=language
        )
        
        return {
            "success": True,
            "original_text": original_text,
            "corrected_text": corrected_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/free-entry/improve-writing")
async def improve_writing(
    text_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Improve the writing quality of the provided text"""
    try:
        original_text = text_data.get("text", "")
        language = text_data.get("language", "en")
        improvement_type = text_data.get("improvement_type", "general")  # general, clarity, flow, vocabulary
        if not original_text.strip():
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Use LLM to improve writing
        improved_text = llm_service.improve_writing(
            text=original_text,
            language=language,
            improvement_type=improvement_type
        )
        
        return {
            "success": True,
            "original_text": original_text,
            "improved_text": improved_text,
            "improvement_type": improvement_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/free-entry/save")
async def save_free_entry(
    entry_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a free-form diary entry"""
    try:
        original_text = entry_data.get("original_text", "")
        final_text = entry_data.get("final_text", original_text)
        language = entry_data.get("language", "en")
        
        if not final_text.strip():
            raise HTTPException(status_code=400, detail="No text to save")
        
        # Save as a diary entry with free_entry mode indicator
        diary_entry = DiaryEntry(
            user_id=current_user.id,
            content=final_text,
            answers={"mode": "free_entry", "original_text": original_text if original_text != final_text else None},
            language=language,
            tone="free_form"
        )
        db.add(diary_entry)
        db.commit()
        
        return {
            "success": True,
            "entry_id": diary_entry.id,
            "message": "Free entry saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/free-entry/edit/{entry_id}")
async def edit_free_entry(
    entry_id: int,
    edit_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit a free-form diary entry"""
    try:
        # Find the entry
        entry = db.query(DiaryEntry).filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        ).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Diary entry not found")
        
        # Verify it's a free entry (has mode indicator in answers or is marked as free_form)
        is_free_entry = False
        if entry.answers and isinstance(entry.answers, dict):
            is_free_entry = entry.answers.get("mode") == "free_entry"
        elif entry.tone == "free_form":
            is_free_entry = True
        
        if not is_free_entry:
            raise HTTPException(status_code=400, detail="This endpoint is only for free entry diary entries")
        
        # Update the content
        if "content" in edit_data:
            new_content = edit_data["content"].strip()
            if not new_content:
                raise HTTPException(status_code=400, detail="Content cannot be empty")
            entry.content = new_content
        
        # Update the last modified timestamp
        from datetime import datetime
        entry.created_at = datetime.utcnow()  # This serves as "last modified"
        
        db.commit()
        db.refresh(entry)
        
        return {
            "success": True, 
            "entry": {
                "id": entry.id,
                "content": entry.content,
                "created_at": entry.created_at.isoformat()
            },
            "message": "Free entry updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)