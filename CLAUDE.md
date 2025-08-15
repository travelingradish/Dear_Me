# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack daily check-in application with guided diary conversation functionality. The application consists of:

- **Backend**: FastAPI (Python) with SQLAlchemy ORM, SQLite database, and Ollama LLM integration
- **Frontend**: React TypeScript application with Tailwind CSS styling

## Development Commands

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python main.py                    # Start development server on http://localhost:8001
```

### Frontend (React)
```bash
cd frontend
npm install
npm start                        # Start development server on http://localhost:3000
npm test                         # Run tests
npm run build                    # Build for production
```

## Architecture

### Backend Structure
- **main.py**: FastAPI application entry point with all API endpoints
- **models.py**: SQLAlchemy database models (User, DiarySession, ConversationMessage, etc.)
- **database.py**: Database configuration and session management
- **auth.py**: JWT authentication utilities
- **llm_service.py**: Ollama LLM integration for conversations
- **guided_llm_service.py**: Specialized LLM service for guided diary flow
- **diary_flow_controller.py**: Manages guided diary conversation state machine
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

### Database Models
- **User**: Basic user authentication and profile
- **DiarySession**: Guided diary conversation sessions with state tracking
- **ConversationMessage**: Individual messages within diary sessions
- **DiaryEntry**: Legacy diary entries (backward compatibility)
- **Conversation**: Legacy conversation storage

### API Endpoints Structure
- `/auth/*`: Authentication (register, login, me)
- `/llm/*`: Direct LLM interaction
- `/diary/*`: Legacy diary functionality
- `/guided-diary/*`: New guided diary sessions
- `/guided-diary-calendar/*`: Calendar view for guided diaries

## Development Notes

### LLM Integration
The application uses Ollama for local LLM inference. Default model is `gemma3:4b`. The system supports multiple languages (en, zh, etc.) with language-specific prompting.

### Database Schema Evolution
The codebase maintains backward compatibility with legacy models while introducing new guided diary functionality through DiarySession and ConversationMessage models.

### State Management
Guided diary sessions use a state machine approach with phases (guide, compose, complete, crisis) and intents (ASK_MOOD, ASK_ACTIVITIES, etc.) managed by DiaryFlowController.

### API Configuration
Backend runs on port 8001, frontend on port 3000. CORS is configured for localhost development. API base URL is configured in frontend as `http://localhost:8001`.