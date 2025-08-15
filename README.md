# Daily Check-in v2 🌟

A sophisticated, AI-powered daily journaling application that provides guided reflection through conversational AI. Built with modern web technologies and designed to help users develop meaningful self-reflection habits.

![Daily Check-in v2](https://img.shields.io/badge/version-2.0.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![React](https://img.shields.io/badge/React-19.1.1-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-Latest-blue)

## ✨ Features

### 🤖 **AI-Powered Guided Conversations**
- Intelligent conversation flow that adapts to user responses
- Mood-adaptive prompting for personalized experiences
- Multi-phase guided reflection (mood, activities, challenges, gratitude, hope)
- Natural language processing for structured data extraction

### 🌍 **Multi-Language Support**
- **English**: Powered by Gemma 3 (4B) model
- **中文 (Chinese)**: Powered by Qwen 3 (8B) model
- Language-specific prompting and conversation styles

### 🛡️ **Mental Health Awareness**
- Automatic crisis detection during conversations
- Supportive responses and resource guidance
- Safe space for emotional expression

### 📅 **Calendar-Based Journal Management**
- Visual calendar interface for browsing entries
- Date-based filtering and organization
- Historical diary viewing and editing

### 🔐 **Secure User Management**
- JWT-based authentication
- Bcrypt password hashing
- Protected routes and API endpoints

### 📱 **Modern User Experience**
- Responsive React TypeScript frontend
- Real-time conversation interface
- Intuitive navigation and clean design
- Mobile-friendly responsive layout

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── main.py                    # FastAPI application entry point
├── models.py                  # SQLAlchemy database models
├── database.py               # Database configuration
├── auth.py                   # JWT authentication utilities
├── llm_service.py            # Direct LLM integration
├── guided_llm_service.py     # Guided conversation LLM service
├── diary_flow_controller.py  # Conversation state machine
├── schemas.py                # Pydantic request/response models
└── requirements.txt          # Python dependencies
```

### Frontend (React TypeScript)
```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── Home.tsx         # Landing page
│   │   ├── GuidedChat.tsx   # Main conversation interface
│   │   ├── SimpleChat.tsx   # Casual chat mode
│   │   ├── Login.tsx        # Authentication
│   │   └── SimpleCalendar.tsx # Calendar component
│   ├── contexts/            # React contexts
│   │   └── AuthContext.tsx  # Authentication state
│   ├── utils/               # Utilities
│   │   └── api.ts          # API client with interceptors
│   ├── types/               # TypeScript definitions
│   └── App.tsx             # Main application router
├── package.json             # Dependencies and scripts
└── public/                  # Static assets
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **Node.js 16+**
- **Ollama** (for local LLM inference)

### 1. Setup Ollama Models
```bash
# Install and start Ollama
ollama pull gemma3:4b
ollama pull qwen3:8b
ollama serve
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python3 main.py
```
🚀 Backend runs on: http://localhost:8001

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```
🎨 Frontend runs on: http://localhost:3000

### 4. Access the Application
- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs
- **API Health Check**: http://localhost:8001

## 📊 Database Schema

### Core Models

**User Model**
- Basic authentication (username, email, hashed_password)
- Relationships to diary sessions and entries

**DiarySession Model**
- Guided conversation sessions with state tracking
- Multi-phase conversation management (guide → compose → complete)
- Crisis detection and structured data extraction

**ConversationMessage Model**
- Individual messages within guided sessions
- Role tracking (user/assistant/system)
- Intent and slot update metadata

**Legacy Models** (Backward Compatibility)
- DiaryEntry: Traditional diary entries
- Conversation: Direct LLM conversations

## 🔄 Conversation Flow

The guided diary system uses a sophisticated state machine:

```
ASK_MOOD → ASK_ACTIVITIES → ASK_CHALLENGES_WINS → ASK_GRATITUDE → ASK_HOPE → ASK_EXTRA → COMPOSE → COMPLETE
```

### Conversation Phases
1. **Guide Phase**: Structured reflection questions
2. **Compose Phase**: AI generates diary entry from conversation
3. **Complete Phase**: User can edit and finalize entry

### Crisis Handling
- Automatic detection of distress signals
- Immediate transition to crisis support mode
- Resource guidance and supportive messaging

## 🛠️ API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Guided Diary
- `POST /guided-diary/start` - Start new guided session
- `POST /guided-diary/{session_id}/message` - Send message in session
- `GET /guided-diary/{session_id}` - Get session details
- `POST /guided-diary/{session_id}/edit` - Edit diary entry

### Calendar & History
- `GET /guided-diary-calendar/dates` - Get diary dates
- `GET /guided-diary-calendar/by-date/{date}` - Get entries by date

### LLM Integration
- `GET /llm/models/{language}` - Get available models
- `POST /llm/conversation` - Direct LLM conversation

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend Configuration
DATABASE_URL=sqlite:///./daily_checkin.db
SECRET_KEY=your-secret-key-here
OLLAMA_URL=http://127.0.0.1:11434

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8001
```

### Model Configuration
Models are configured in `backend/llm_service.py` and `backend/guided_llm_service.py`:
- **English**: `gemma3:4b` (default)
- **Chinese**: `qwen3:8b` (default)

## 🎨 UI Features

### Beautiful Design Elements
- **Gradient Backgrounds**: Modern purple-blue gradients
- **Floating Animations**: Subtle ambient elements
- **Responsive Layout**: Mobile-first design approach
- **Intuitive Navigation**: Clean, user-friendly interface

### Conversation Interface
- **Real-time Messaging**: Instant AI responses
- **Typing Indicators**: Visual feedback during processing
- **Message History**: Complete conversation tracking
- **Edit Capabilities**: Diary entry editing with live preview

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Security**: Bcrypt hashing with salt
- **CORS Protection**: Configured for local development
- **Input Validation**: Pydantic schema validation
- **Error Handling**: Comprehensive exception management

## 📈 Performance Features

- **Background Processing**: Non-blocking LLM calls
- **Efficient State Management**: Optimized React state updates
- **Database Optimization**: SQLAlchemy ORM with indexing
- **Caching Strategy**: Local storage for auth tokens

## 🔮 Advanced Features

### Mood-Adaptive AI
The AI adapts its conversation style based on detected user mood:
- **Positive/Happy**: Bright, energetic responses
- **Calm/Neutral**: Peaceful, balanced tone
- **Reflective/Thoughtful**: Deeper, more contemplative
- **Sad/Down**: Gentle, supportive approach
- **Stressed/Anxious**: Calming, grounding language

### Structured Data Extraction
The system intelligently extracts structured information:
```json
{
  "mood": "User's emotional state",
  "activities": "Daily activities and events",
  "challenges": "Difficulties encountered",
  "gratitude": "Things user is grateful for",
  "hope": "Future aspirations and hopes",
  "extra_notes": "Additional reflections"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for local LLM inference capabilities
- **FastAPI** for the robust backend framework
- **React** for the dynamic frontend experience
- **SQLAlchemy** for elegant database management
- **Tailwind CSS** for beautiful styling utilities

## 🆘 Support

For support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for mindful self-reflection and personal growth**