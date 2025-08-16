# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack daily check-in application with guided diary conversation functionality. The application consists of:

- **Backend**: FastAPI (Python) with SQLAlchemy ORM, SQLite database, and Ollama LLM integration
- **Frontend**: React TypeScript application with Tailwind CSS styling

## Development Commands

### Prerequisites
- **Python 3.9+** and **Node.js 16+**
- **Ollama** with models: `ollama pull gemma3:4b` and `ollama pull qwen3:8b`
- Start Ollama service: `ollama serve`

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python main.py                    # Start development server on http://localhost:8001
python test_guided_diary.py       # Run integration tests
python test_memory_system.py      # Test memory system functionality
python test_calendar.py           # Test calendar functionality
python test_improved_diary.py     # Test diary improvements
```

### Frontend (React)
```bash
cd frontend
npm install
npm start                        # Start development server on http://localhost:3000
npm test                         # Run Jest tests
npm run build                    # Build for production
```

### Full Application Setup
1. Start Ollama service first: `ollama serve`
2. Start backend: `cd backend && python main.py`
3. Start frontend: `cd frontend && npm start`
4. Access application at http://localhost:3000

## Architecture

### Backend Structure
- **main.py**: FastAPI application entry point with all API endpoints
- **models.py**: SQLAlchemy database models (User, DiarySession, ConversationMessage, etc.)
- **database.py**: Database configuration and session management
- **auth.py**: JWT authentication utilities
- **llm_service.py**: Ollama LLM integration for conversations
- **guided_llm_service.py**: Specialized LLM service for guided diary flow
- **diary_flow_controller.py**: Manages guided diary conversation state machine
- **memory_service.py**: User memory extraction, storage, and retrieval system
- **prompt_manager.py**: Centralized prompt management with caching and language support
- **schemas.py**: Pydantic models for request/response validation

### Frontend Structure
- **src/App.tsx**: Main application router and authentication wrapper
- **src/components/**: React components for UI (Login, Chat, Home, etc.)
- **src/contexts/AuthContext.tsx**: Authentication context provider
- **src/utils/api.ts**: Axios-based API client with auth interceptors
- **src/types/index.ts**: TypeScript type definitions

### Key Features
1. **User Authentication**: JWT-based auth with registration/login
2. **Simple Chat**: Direct LLM conversation interface
3. **Guided Diary**: Multi-phase conversation flow for diary generation
4. **Calendar View**: Browse diary entries by date
5. **Crisis Detection**: Special handling for mental health concerns
6. **Memory System**: Automatic extraction and storage of user information for personalization

### Database Models
- **User**: Basic user authentication and profile
- **DiarySession**: Guided diary conversation sessions with state tracking
- **ConversationMessage**: Individual messages within diary sessions
- **UserMemory**: Extracted user information for personalization
- **MemorySnapshot**: Periodic snapshots of user memory state
- **DiaryEntry**: Legacy diary entries (backward compatibility)
- **Conversation**: Legacy conversation storage

### API Endpoints Structure
- `/auth/*`: Authentication (register, login, me)
- `/llm/*`: Direct LLM interaction
- `/diary/*`: Legacy diary functionality
- `/guided-diary/*`: New guided diary sessions
- `/guided-diary-calendar/*`: Calendar view for guided diaries
- `/memory/*`: User memory management endpoints

## Development Notes

### LLM Integration
The application uses Ollama for local LLM inference. Default model is `gemma3:4b`. The system supports multiple languages (en, zh, etc.) with language-specific prompting.

**Prompt Management System**: Prompts are organized in `backend/prompts/` directory:
- `conversation/`: Prompts for casual chat mode  
- `diary/`: Prompts for diary generation
- `guided/`: Prompts for guided diary flow (guide_*.txt and composer_*.txt)
- Language-specific files: `en.txt`, `zh.txt`
- Managed by `PromptManager` class with caching and error handling

### Database Schema Evolution
The codebase maintains backward compatibility with legacy models while introducing new guided diary functionality through DiarySession and ConversationMessage models.

### State Management
Guided diary sessions use a state machine approach with phases (guide, compose, complete, crisis) and intents managed by DiaryFlowController:

**Intent Flow**: ASK_MOOD → ASK_ACTIVITIES → ASK_CHALLENGES_WINS → ASK_GRATITUDE → ASK_HOPE → ASK_EXTRA → COMPOSE → COMPLETE

**Crisis Handling**: Automatic detection transitions sessions to crisis support mode with specialized responses and resource guidance.

### Memory System
The memory service automatically extracts and stores user information during conversations:
- **Categories**: Personal info, preferences, relationships, goals, health, routines, etc.
- **Pattern Matching**: Uses regex and keyword detection for memory extraction
- **Snapshots**: Periodic memory snapshots for data integrity and historical tracking
- **Integration**: Memory context is provided to LLM for personalized responses

### API Configuration
Backend runs on port 8001, frontend on port 3000. CORS is configured for localhost development. API base URL is configured in frontend as `http://localhost:8001`.

## Testing Strategy

### Backend Testing
- **Integration Tests**: `backend/test_guided_diary.py` - Full flow testing with actual API calls
- **Memory System Tests**: `backend/test_memory_system.py` - Memory extraction and storage testing
- **Component Tests**: Individual test files like `test_calendar.py`, `test_improved_diary.py`
- **Live Testing**: Scripts like `test_slot_extraction_live.py` for real-time testing with Ollama

### Frontend Testing
- **Jest Tests**: `frontend/src/components/__tests__/` - Component testing with React Testing Library
- **Test Commands**: `npm test` for interactive testing, `npm test -- --coverage` for coverage reports

### Common Issues and Debugging
- **Ollama Connection**: Ensure Ollama service is running on port 11434
- **Database Issues**: SQLite database is created automatically; check `backend/daily_checkin.db`
- **CORS Errors**: Verify backend is running on port 8001 and CORS settings in `main.py`
- **LLM Model Errors**: Confirm required models are pulled: `ollama list`

## Key Dependencies and Versions
- **Backend**: FastAPI 0.104.1, SQLAlchemy 2.0.23, Pydantic 2.5.0
- **Frontend**: React 19.1.1, TypeScript, Tailwind CSS 4.1.11, React Router 7.8.0
- **Testing**: Jest (frontend), pytest (backend), React Testing Library
- **LLM**: Ollama with gemma3:4b (English) and qwen3:8b (Chinese)