# Dear Me ❤️

## ⚠️ Important Notes

**Pre-Release Status:** This is v1.0.0-beta, an early access release. Everything works great, but we're actively gathering feedback. Please [report issues](https://github.com/travelingradish/Dear_Me/issues) to help us improve!

**Age Recommendation:** At this stage, Dear Me is only recommended for adults. While I've started building age-appropriateness controls, they are still experimental. Please do not use this with children or adolescents.

**Mental Health Disclaimer:** This app is not a replacement for professional mental health care. It is simply a companion to help us unwind, reflect, and capture our feelings in a private space. If you are struggling, please seek support from a qualified psychologist, psychiatrist, or healthcare provider.

---

*Be Here, Be Now, Be You -- in a space you call your own*

A gentle, AI-powered journaling companion offering guided reflection, casual conversations, and free-form writing. Created to support mindfulness and mental well-being, it invites you to slow down, unwind, and nurture meaningful self-reflection in a space that is entirely your own.

![Dear Me](https://img.shields.io/badge/version-1.0.0--beta-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![React](https://img.shields.io/badge/React-19.1.1-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-Latest-blue)

## 📥 Download Now

### 🍎 **macOS Users - Easy One-Click Installation**

[**⬇️ Download Dear_Me_1.0.0_macOS.dmg**](https://github.com/travelingradish/Dear_Me/releases/download/v1.0.0-beta/Dear_Me_1.0.0_macOS.dmg)

**Installation takes ~15 minutes (first time), then just double-click to launch!**

1. Download the DMG file above
2. Open it and drag "Dear Me.app" to Applications
3. Run `install_dependencies.sh` (first time only)
4. Open Dear Me from Applications
5. Start journaling! 📝

⏱️ **Subsequent launches**: 30 seconds (everything cached)

---

### 🪟 **Windows Users - Professional Installer**

[**⬇️ Download Dear_Me_1.0.0_Windows.exe**](https://github.com/travelingradish/Dear_Me/releases/download/v1.0.0-beta/Dear_Me_1.0.0_Windows.exe)

**Installation takes ~15 minutes (first time), then just double-click to launch!**

1. Download the .exe file above
2. Run the installer (Windows may show a SmartScreen warning - click "More info" → "Run anyway")
3. The installer automatically installs Python, Node.js, and Ollama
4. Click the "Dear Me" shortcut on your Desktop
5. Start journaling! 📝

⏱️ **Subsequent launches**: 30 seconds (everything cached)

---

## 🌍 Platform Support

| Platform | Status | Version |
|----------|--------|---------|
| **macOS** | ✅ Available | v1.0.0 |
| **Windows** | ✅ Available | v1.0.0 |
| **Linux** | 📅 Planned | Future |

*Dear Me is available for macOS 10.13+ and Windows 10+. Linux support is planned for future releases.*

---

## 📁 Project Structure (For Developers & Interested Users)

Dear Me organizes platform-specific installation and deployment code in separate directories:

```
Dear_Me/
├── 🍎 macos/                   # macOS installer & launcher
│   ├── setup.sh               # Daily launcher (called by app bundle)
│   ├── build_dmg.sh          # Builds the .dmg installer
│   ├── Dear Me.command       # Desktop shortcut
│   ├── README_macOS.txt      # User installation guide
│   └── DEVELOPER_GUIDE.md    # Developer documentation
│
├── 🪟 windows/                 # Windows installer & launcher
│   ├── setup_windows.bat     # Daily launcher (double-click to run)
│   ├── build_installer.ps1   # Builds the .exe installer
│   ├── build_installer.nsi   # NSIS installer script
│   ├── install_dependencies.ps1  # First-time setup
│   ├── README_Windows.txt    # User installation guide
│   ├── DEVELOPER_GUIDE.md    # Developer documentation
│   └── assets/               # Icons and images
│
├── backend/                   # FastAPI Python backend
│   ├── app/                  # Application code
│   ├── main.py              # Entry point
│   └── requirements.txt      # Python dependencies
│
├── frontend/                  # React TypeScript frontend
│   ├── src/                 # Source code
│   ├── build/               # Pre-built production app (used by installers)
│   └── package.json         # NPM dependencies
│
└── README.md               # This file
```

### 🎯 For Different Audiences

**End Users:**
- Download installers from [Releases](https://github.com/travelingradish/Dear_Me/releases)
- Read `README_macOS.txt` or `README_Windows.txt` for installation help

**macOS Developers:**
- Platform code: `macos/setup.sh`, `macos/build_dmg.sh`
- Build guide: `macos/DEVELOPER_GUIDE.md`
- Build command: `cd macos && ./build_dmg.sh`

**Windows Developers:**
- Platform code: `windows/setup_windows.bat`, `windows/build_installer.ps1`
- Build guide: `windows/DEVELOPER_GUIDE.md`
- Build command: `cd windows && powershell -ExecutionPolicy Bypass -File build_installer.ps1`

**Full-Stack Developers:**
- Backend: `backend/main.py` (FastAPI), see `CLAUDE.md` for dev commands
- Frontend: `frontend/src/` (React TypeScript), see `CLAUDE.md` for dev commands

---

## ✨ Features

### 🎯 **Three Journaling Modes**
- **🤖 Guided Mode**: AI-led structured conversations for deep reflection
- **💬 Casual Mode**: Free-form chat with AI-generated diary entries  
- **✍️ Free Entry Mode**: Direct writing with grammar correction and improvement tools

### 🤖 **Smart AI Companion**
- **Personalized Identity**: Name your AI friend for a more intimate experience
- **Advanced Memory System**: Enhanced contextual memory with temporal awareness and pattern recognition
- **Intelligent Retrieval**: Sophisticated memory filtering to distinguish current vs. historical information
- **Memory Insights**: Automatic pattern detection, evolution tracking, and relationship analysis
- **Crisis Detection**: Supportive responses and mental health awareness

### ✍️ **Writing Enhancement**
- Grammar correction and advanced writing improvements
- Smart reset to always return to your original text
- Side-by-side comparison of original vs. improved versions

### 🌍 **Multi-Language Support**
- **Universal Language Support**: Powered by unified Llama 3.1:8b model for all languages
- **Seamless Language Switching**: Natural conversation in English, Chinese, and other languages
- **Simplified Architecture**: Single model reduces complexity while maintaining quality

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
- **AI Integration**: Local Ollama with universal Llama 3.1:8b model for all languages
- **Memory System**: Advanced contextual memory with temporal awareness and pattern recognition
- **Authentication**: JWT-based security with bcrypt password hashing
- **Data Flow**: RESTful APIs connecting React frontend to FastAPI backend
- **Testing**: Comprehensive pytest suite with unit, integration, and live testing capabilities

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
   ⏳ **This takes ~20 minutes** and downloads ~4.7GB. This universal model supports all languages including English and Chinese.

4. **Verify installation**:
   ```bash
   ollama list
   ```
   You should see `llama3.1:8b` in the list.

⚠️ **Important**: Keep the first terminal with `ollama serve` running while using Dear Me.

### ⚡ One-Click Setup - Non-Technical Users

#### 🍎 macOS (Recommended - Professional Installer)

**For non-technical users, we provide a professional macOS installer:**

1. **Download** `Dear_Me_1.0.0.dmg` from this repository
2. **Open the .dmg file** - Finder window appears
3. **Drag "Dear Me.app"** to the Applications folder
4. **Double-click `install_dependencies.sh`** - Terminal opens
   - Installs Ollama, Node.js, and Python 3.13 automatically
   - Takes ~10 minutes on first run
5. **Launch** - Open Applications → Double-click "Dear Me"
6. **Done!** Your browser opens to http://localhost:3000

✨ **Next time**, just double-click "Dear Me.app" in Applications - everything starts in ~30 seconds!

**Additional Options:**
- **Desktop Launcher**: Copy `Dear Me.command` to your Desktop for quick access
- **Phone Access**: Look in Terminal for the WiFi IP (e.g., `http://192.168.x.x:3000`)

---

#### 🖥️ Terminal Setup (For Developers)

If you prefer to use Terminal or are on Linux:

1. **Open Terminal** in the project folder
2. **Run**: `./setup.sh`
3. **Your app** opens at http://localhost:3000

The script handles everything automatically.

### 🔄 Daily Use

**macOS**: Double-click "Dear Me.app" in Applications (30 seconds)

**Windows**: Double-click "Dear Me" on your Desktop (30 seconds)

**Terminal**: Run `./setup.sh` (2-3 minutes)

### 🎨 Get Started
1. **Create your account** - just username and password, no email required
2. **Name your AI companion** - this personalizes your entire experience!
3. **Choose your journaling style**:
   - 🤖 **Guided**: AI-led structured conversations
   - 💬 **Casual**: Free-form chat with diary generation  
   - ✍️ **Free Entry**: Direct writing with AI assistance

**✨ No Configuration Required**: Dear Me works out of the box with sensible defaults!

---

## 💡 Installation Help & Troubleshooting

Running into issues? Check the platform-specific guides:

- **🍎 macOS Help**: See `macos/README_macOS.txt` for detailed troubleshooting
- **🪟 Windows Help**: See `windows/README_Windows.txt` for detailed troubleshooting
- **General Issues**: [GitHub Issues](https://github.com/travelingradish/Dear_Me/issues)

**Key Points:**
- First install takes ~15 minutes (downloads Python, Node.js, Ollama, AI model)
- Subsequent launches are ~30 seconds
- Requires stable internet for initial setup
- The AI model is ~4.7GB (optional to download on first launch, can be added later)

---

## 🤖 How It Works

**Dear Me** creates a personalized journaling experience through three simple steps:

1. **Choose Your Mode**: Select guided conversations, casual chat, or free writing
2. **Reflect & Share**: Express your thoughts naturally with your AI companion
3. **Review & Grow**: Access all your entries through the unified calendar interface

The AI adapts to your communication style and remembers important details about your life, creating meaningful conversations that evolve over time.

## 🧠 Advanced Memory System

**Dear Me** features a sophisticated memory system that creates truly personalized conversations:

### 🎯 **Contextual Memory Intelligence**
- **Temporal Awareness**: Distinguishes between current conversations and historical memories
- **Memory Type Classification**: Separates factual information (relationships, personal details) from temporal preferences (interests, goals)
- **Age-Based Relevance**: Automatically applies temporal penalties to outdated information
- **Real-Time Correction**: Instantly updates incorrect memories when corrected by users

### 🔍 **Smart Memory Retrieval**
- **Pattern Recognition**: Advanced regex and keyword-based memory extraction across 6 categories
- **Relevance Scoring**: Sophisticated algorithms to find the most contextually relevant memories
- **Memory Limits**: Intelligent filtering to prevent information overload (max 5 relevant memories per conversation)
- **Category Organization**: Organized memory storage across personal_info, relationships, interests, challenges, goals, and preferences

### 📊 **Memory Insights & Analysis**
- **Evolution Tracking**: Monitors how your thoughts, goals, and preferences change over time
- **Contradiction Detection**: Identifies conflicting information and suggests clarification
- **Pattern Analysis**: Recognizes recurring themes and important life patterns
- **Gap Identification**: Suggests conversation topics based on missing memory categories

This creates conversations that feel natural and personal, as if talking to a friend who truly knows and remembers you.

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
- **Comprehensive Testing**: Robust testing across backend and frontend with pytest suite
- **Memory System Validation**: Dedicated testing for memory retrieval, temporal filtering, and context accuracy
- **Error Handling**: Graceful error management and user feedback
- **Input Validation**: Secure data validation and sanitization
- **Code Quality**: Clean, maintainable codebase with consistent standards
- **Performance Monitoring**: Optimized response times and efficient operation

## 📋 Pre-Release Notes (v1.0.0-beta)

### What's Stable ✅
- **Core journaling functionality** - All three modes work reliably
- **AI conversations** - Memory system and responses are solid
- **Installation process** - One-click DMG installer works smoothly
- **Data persistence** - Your entries are saved and safe
- **Privacy** - Everything runs locally, no cloud sync

### What Might Change 🔧
- **UI/UX improvements** - Based on user feedback
- **Memory system refinements** - Performance and accuracy improvements
- **Feature additions** - Based on user requests
- **Performance optimizations** - Ongoing improvements

### How to Report Issues
Found something that doesn't work right? Please help us improve:
1. [Open a GitHub Issue](https://github.com/travelingradish/Dear_Me/issues)
2. Describe what happened
3. Include your macOS version and any error messages

Your feedback is invaluable! 🙏

---

## 🔧 Recent Improvements (September 2025)

### 🎯 **Major Memory System Overhaul**
- **Fixed Critical Memory Bug**: Resolved issue where memory objects weren't properly converted to strings for LLM processing
- **Enhanced Temporal Filtering**: Improved distinction between current conversations and historical memories
- **Real-Time Memory Correction**: Added ability to instantly update incorrect memories when users provide corrections
- **Memory Type Classification**: Implemented factual vs. temporal memory categories with appropriate aging policies

### 🧪 **Testing & Quality Improvements**
- **Comprehensive Test Suite**: Added extensive pytest coverage for memory system, API endpoints, and core functionality
- **Memory Validation Tests**: Created dedicated tests to verify memory retrieval accuracy and temporal filtering
- **Bug Detection**: Identified and resolved 25+ actual implementation issues through rigorous testing
- **Integration Testing**: Full-stack testing with actual Ollama LLM integration

### 🚀 **Performance & Reliability**
- **Improved Error Handling**: Enhanced debugging and error reporting throughout the application
- **Schema Validation**: Fixed API schema mismatches and improved data type consistency
- **Memory Efficiency**: Optimized memory retrieval to prevent information overload (5-memory limit)
- **Conversation Context**: Better handling of conversation state and session management

## 🤝 Contributing

Thank you for your interest in contributing to Dear Me!

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
