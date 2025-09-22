# Dear Me ❤️

## ⚠️ Important Notes

**Age Recommendation:** At this stage, Dear Me is only recommended for adults. While I've started building age-appropriateness controls, they are still experimental. Please do not use this with children or adolescents.

**Mental Health Disclaimer:** This app is not a replacement for professional mental health care. It is simply a companion to help us unwind, reflect, and capture our feelings in a private space. If you are struggling, please seek support from a qualified psychologist, psychiatrist, or healthcare provider.

---

*Be Here, Be Now, Be You -- in a space you call your own*

A gentle, AI-powered journaling companion offering guided reflection, casual conversations, and free-form writing. Created to support mindfulness and mental well-being, it invites you to slow down, unwind, and nurture meaningful self-reflection in a space that is entirely your own.

![Dear Me](https://img.shields.io/badge/version-1.0.1--beta-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![React](https://img.shields.io/badge/React-19.1.1-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-Latest-blue)

## ✨ Features

### 🎯 **Three Journaling Modes**
- **🤖 Guided Mode**: AI-led structured conversations for deep reflection
- **💬 Casual Mode**: Free-form chat with AI-generated diary entries  
- **✍️ Free Entry Mode**: Direct writing with grammar correction and improvement tools

### 🤖 **Smart AI Companion**
- **Personalized Identity**: Name your AI friend for a more intimate experience
- **Adaptive Memory**: Learns and remembers your details across all conversations
- **Crisis Detection**: Supportive responses and mental health awareness

### ✍️ **Writing Enhancement**
- Grammar correction and advanced writing improvements
- Smart reset to always return to your original text
- Side-by-side comparison of original vs. improved versions

### 🌍 **Multi-Language Support** 
- **English & 中文 (Chinese)**: Powered by Llama 3.1 model
- One-click language switching with persistent preferences

### 📅 **Unified Journal Management**
- Visual calendar interface for all your entries
- Edit and delete entries directly from any mode
- Color-coded mode indicators for easy navigation

### 🔐 **Privacy-First Design**
- No email required for registration
- Secure JWT authentication with encrypted passwords
- Optional data sharing with full user control

## 🏗️ Architecture

**Dear Me** is a full-stack web application built with modern technologies:

- **Backend**: FastAPI (Python) with SQLAlchemy ORM and SQLite database
- **Frontend**: React TypeScript with responsive design and unified interface
- **AI Integration**: Local Ollama models for natural language processing
- **Authentication**: JWT-based security with bcrypt password hashing
- **Data Flow**: RESTful APIs connecting React frontend to FastAPI backend

## 🚀 Quick Start

### Prerequisites
Install these three tools first:
- **Python 3.10+**: [Download here](https://www.python.org/downloads/) ⚠️ Windows: Check "Add Python to PATH"
- **Node.js 16+**: [Download here](https://nodejs.org/)
- **Ollama**: [Download here](https://ollama.ai/) or `brew install ollama` (macOS)

#### 🤖 Download AI Model (Required - ~20 minutes)
After installing Ollama, you need to download the AI model:

1. **Open Terminal/Command Prompt**
   - **Windows**: Press `Win + R`, type `cmd`, press Enter
   - **macOS**: Press `Cmd + Space`, type "terminal", press Enter  
   - **Linux**: Press `Ctrl + Alt + T`

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```
   ⚠️ **Keep this terminal open** - you'll see "Ollama is running" message

3. **Open a new Terminal window** and download the model:
   ```bash
   ollama pull llama3.1:8b
   ```
   ⏳ **This takes ~20 minutes** and downloads ~4.7GB. The model supports both English and Chinese.

4. **Verify installation**:
   ```bash
   ollama list
   ```
   You should see `llama3.1:8b` in the list.

### ⚡ One-Click Setup

**Choose your operating system:**

#### Windows
1. Double-click `setup.bat`
2. Wait for setup to complete
3. Your app opens at http://localhost:3000

#### macOS/Linux
1. Open Terminal in the project folder
2. Run: `./setup.sh`
3. Your app opens at http://localhost:3000

#### Python (All Platforms)
1. Run: `python setup.py`
2. Your app opens at http://localhost:3000

**That's it!** The script handles everything: downloading AI models, installing dependencies, and starting all services.

### 🔄 Daily Use
After the first setup, just run the same command:
- **Windows**: Double-click `setup.bat`
- **macOS/Linux**: `./setup.sh`  
- **Python**: `python setup.py`

### 🎨 Get Started
1. **Create your account** - just username and password, no email required
2. **Name your AI companion** - this personalizes your entire experience!
3. **Choose your journaling style**:
   - 🤖 **Guided**: AI-led structured conversations
   - 💬 **Casual**: Free-form chat with diary generation  
   - ✍️ **Free Entry**: Direct writing with AI assistance

**✨ No Configuration Required**: Dear Me works out of the box with sensible defaults!

## 🤖 How It Works

**Dear Me** creates a personalized journaling experience through three simple steps:

1. **Choose Your Mode**: Select guided conversations, casual chat, or free writing
2. **Reflect & Share**: Express your thoughts naturally with your AI companion
3. **Review & Grow**: Access all your entries through the unified calendar interface

The AI adapts to your communication style and remembers important details about your life, creating meaningful conversations that evolve over time.

## 🎨 UI Features

### Beautiful Design Elements
- **Gradient Backgrounds**: Modern purple-blue gradients
- **Floating Animations**: Subtle ambient elements
- **Responsive Layout**: Clean, adaptive web design
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

## 📈 Performance & Quality Features

### Performance Optimizations
- **Background Processing**: Non-blocking LLM calls
- **Efficient State Management**: Optimized React state updates
- **Database Optimization**: SQLAlchemy ORM with indexing
- **Caching Strategy**: Local storage for auth tokens

### Quality Assurance
- **Comprehensive Testing**: Robust testing across backend and frontend
- **Error Handling**: Graceful error management and user feedback
- **Input Validation**: Secure data validation and sanitization
- **Code Quality**: Clean, maintainable codebase with consistent standards
- **Performance Monitoring**: Optimized response times and efficient operation

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
- **Claude Code** for development assistance and code quality improvements

---

**Dear Me** — *Your gentle companion, built with ❤️  for unpacking, reflection, and growth in your own sacred space*

