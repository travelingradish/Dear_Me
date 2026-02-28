# Mobile Access Mechanism: How Your Phone Uses the Desktop App

## Table of Contents
1. [Overview](#overview)
2. [Network Architecture](#network-architecture)
3. [How It Works](#how-it-works)
4. [Technical Deep Dive](#technical-deep-dive)
5. [Security & CORS](#security--cors)
6. [Startup Order](#startup-order)
7. [Troubleshooting](#troubleshooting)

---

## Overview

"Dear Me" is designed to run on your **laptop as a local web server** that your **Android phone can access over WiFi**. This document explains the technical mechanism that makes this possible.

### The Simple Version

Your laptop runs three services:
- **React App** (port 3000) - User interface
- **FastAPI Backend** (port 8001) - Server logic
- **Ollama LLM** (port 11434) - AI engine

Your phone connects to the same WiFi and opens the React app in a browser, just like accessing any website.

---

## Network Architecture

### Physical Setup

```
Your Home WiFi Network (e.g., 192.168.2.0/24)
│
├─ 📱 Android Phone (192.168.2.141)
│  └─ Chrome Browser
│     └─ http://192.168.2.112:3000  ← User enters this
│
└─ 💻 Laptop (192.168.2.112)
   ├─ React Dev Server (port 3000)
   │  ├─ Serves HTML/CSS/JavaScript
   │  ├─ Auto-detects API host → 192.168.2.112:8001
   │  └─ Listens on: http://0.0.0.0:3000
   │
   ├─ FastAPI Backend (port 8001)
   │  ├─ Processes requests
   │  ├─ Talks to SQLite database
   │  ├─ Calls Ollama LLM
   │  └─ Listens on: http://0.0.0.0:8001
   │
   ├─ Ollama LLM (port 11434)
   │  └─ Runs AI models (llama3.1:8b)
   │
   └─ SQLite Database (dear_me.db)
      └─ Stores all user data
```

### Port Layout

| Service | Port | Purpose | Accessible From |
|---------|------|---------|-----------------|
| **React Dev Server** | 3000 | User interface | Phone + Desktop |
| **FastAPI Backend** | 8001 | API requests | Phone + Desktop |
| **Ollama LLM** | 11434 | AI responses | Desktop only |
| **SQLite DB** | N/A | Data storage | Backend only |

---

## How It Works

### User Perspective: Step-by-Step

#### 1. User Opens App on Phone

```
Phone Browser Address Bar:
┌────────────────────────────────────┐
│ http://192.168.2.112:3000          │
└────────────────────────────────────┘
         ↓
    WiFi connects to laptop's React server
         ↓
    React app downloads to phone
         ↓
    JavaScript starts running in browser
```

#### 2. User Types a Message

```
Phone Screen:
┌────────────────────────────────────┐
│ What's on your mind?               │
│ ┌──────────────────────────────┐   │
│ │ Hello! How are you today?    │   │ ← User types
│ └──────────────────────────────┘   │
│ ┌──────────────────────────────┐   │
│ │        [Send Button]         │   │
│ └──────────────────────────────┘   │
└────────────────────────────────────┘
         ↓
    JavaScript event fires
         ↓
    Creates HTTP POST request with message
         ↓
    Sends to: http://192.168.2.112:8001/llm/conversation
```

#### 3. Message Travels Over Network

```
Phone (192.168.2.141)
    ↓
WiFi Router (192.168.2.1)
    ↓
Laptop (192.168.2.112)
    ↓
FastAPI Backend (port 8001)
```

#### 4. Backend Processes Request

```
FastAPI Backend:
┌─────────────────────────────────────┐
│ 1. Receive HTTP POST request        │
│ 2. Parse JSON body                  │
│ 3. Verify JWT token (auth)          │
│ 4. Load user from database          │
│ 5. Get user memories from DB        │
│ 6. Create LLM prompt with context   │
│ 7. Send to Ollama LLM              │
│ 8. Receive AI response              │
│ 9. Create JSON response             │
│ 10. Send back to phone              │
└─────────────────────────────────────┘
```

#### 5. Phone Receives Response

```
HTTP 200 OK Response:
{
  "success": true,
  "response": "Hello! I'm doing great, thank you for asking!",
  "language": "en"
}
    ↓
JavaScript parses response
    ↓
Updates DOM with new message
    ↓
Phone screen updates instantly
```

---

## Technical Deep Dive

### 1. Dynamic Hostname Detection

**File**: `frontend/src/utils/api.ts`

#### Code
```typescript
// Get the hostname from the current URL
const hostname = window.location.hostname;

// Build API URL based on hostname
const API_BASE_URL = (hostname === 'localhost' || hostname === '127.0.0.1')
  ? 'http://localhost:8001'           // Desktop: use localhost
  : `http://${hostname}:8001`;         // Mobile: use IP address
```

#### How It Works

**On Desktop** (user opens `http://localhost:3000`):
```
window.location.hostname = "localhost"
    ↓
Condition true: hostname === 'localhost'
    ↓
API_BASE_URL = "http://localhost:8001"
    ↓
API calls go to: http://localhost:8001
```

**On Phone** (user opens `http://192.168.2.112:3000`):
```
window.location.hostname = "192.168.2.112"
    ↓
Condition false: hostname !== 'localhost'
    ↓
API_BASE_URL = "http://192.168.2.112:8001"
    ↓
API calls go to: http://192.168.2.112:8001
```

#### Why This Works

The browser automatically provides the hostname from the URL bar. The React app just uses it to construct API URLs. **Zero configuration needed**!

### 2. CORS (Cross-Origin Resource Sharing)

**File**: `backend/main.py`

#### Without CORS Fix

```
Phone Browser:
  Origin: http://192.168.2.141:3000

Backend (different IP):
  Server: http://192.168.2.112:8001

Browser Security Policy:
  "These are different origins! BLOCKED!"

Result: 🚫 Request fails silently
         No error message, data just doesn't come back
         User sees: "Something went wrong"
```

#### With CORS Fix

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Desktop
        "http://127.0.0.1:3000",      # Desktop alt
        "*"                            # Any origin (local WiFi only!)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

**What CORS does**:
- Browser: "Can I talk to this server?"
- Backend: "Yes! I allow requests from `*` (anyone)"
- Browser: "OK, here's your data" ✅

#### Security Note

Using `"*"` in CORS headers is normally dangerous (allows any website to access your data), but it's safe here because:

1. **Only on private WiFi** - Not exposed to internet
2. **Requires authentication** - Every request needs JWT token
3. **No sensitive data exposed** - All data is personal journal entries
4. **Development only** - Not production code
5. **No database credentials exposed** - Backend keeps them secret

### 3. Server Binding to All Interfaces

**Command**: `HOST=0.0.0.0 npm start`

#### Default Behavior (Without HOST=0.0.0.0)

```bash
npm start
# Starts on: http://127.0.0.1:3000
# Only accessible from: Same machine (localhost)
# Phone can access? ❌ NO
```

#### With HOST=0.0.0.0

```bash
HOST=0.0.0.0 npm start
# Starts on: http://0.0.0.0:3000 (all interfaces)
# Accessible from: Entire network
# Phone can access? ✅ YES
```

**What 0.0.0.0 means**:
- `127.0.0.1` = localhost only
- `192.168.2.112` = specific IP only
- `0.0.0.0` = all network interfaces (localhost + all IPs)

---

## Complete Request/Response Cycle

### Detailed Flow Diagram

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         COMPLETE MESSAGE FLOW                             ║
╚════════════════════════════════════════════════════════════════════════════╝

PHONE                          NETWORK                       LAPTOP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User types: "Hello"
    │
    ├─ JavaScript captures input event
    │
    ├─ Creates JSON:
    │  {
    │    "message": "Hello",
    │    "conversation_history": [],
    │    "language": "en"
    │  }
    │
    ├─ Creates HTTP POST request:
    │  POST /llm/conversation HTTP/1.1
    │  Host: 192.168.2.112:8001
    │  Authorization: Bearer {jwt_token}
    │  Content-Type: application/json
    │
    │                                 ───────→ WiFi ────→
    │
    │                                           FastAPI receives:
    │                                               ├─ Parse JSON body
    │                                               ├─ Extract message: "Hello"
    │                                               ├─ Verify JWT token ✓
    │                                               ├─ Load user from DB
    │                                               ├─ Query user memories
    │                                               ├─ Build LLM prompt:
    │                                               │  "User said: Hello
    │                                               │   Character: AI Assistant
    │                                               │   Context: [memories]
    │                                               │   Respond naturally"
    │                                               │
    │                                               ├─ Call Ollama LLM
    │                                               │  (port 11434)
    │                                               │
    │                                               ├─ Ollama processes
    │                                               │  (neural network inference)
    │                                               │  Returns: "Hi! How are you?"
    │                                               │
    │                                               ├─ Build response JSON:
    │                                               │  {
    │                                               │    "success": true,
    │                                               │    "response": "Hi!..."
    │                                               │  }
    │                                               │
    │    ←──────── WiFi ─────────────────────────
    │
    ├─ Receive HTTP 200 OK
    │
    ├─ JavaScript parses JSON
    │
    ├─ Extract: response = "Hi! How are you?"
    │
    ├─ Add to conversation_history
    │
    ├─ Update DOM with new message
    │
    └─ Phone screen updates instantly ✓
       User sees: "Hi! How are you?"

Total time: ~1-2 seconds (network + LLM inference)
```

### Data Structures Involved

```
Request (Phone → Backend):
{
  "message": "Hello",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hi there",
      "created_at": "2026-02-28T14:22:00"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help?",
      "created_at": "2026-02-28T14:22:05"
    }
  ],
  "language": "en"
}

Response (Backend → Phone):
{
  "success": true,
  "response": "Hi! How are you doing today?",
  "language": "en",
  "timestamp": "2026-02-28T14:22:10"
}
```

---

## Security & CORS

### JWT Authentication

Every API request requires a valid JWT (JSON Web Token):

```
Phone sends:
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Backend checks:
1. Token exists? ✓
2. Token not expired? ✓
3. Token valid signature? ✓
4. User ID from token exists? ✓
5. Yes to all? Process request
   No to any? Reject with 401 Unauthorized
```

### CORS Headers Explained

```python
# Request from phone (different origin):
Origin: http://192.168.2.141:3000

# Backend response includes:
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true

# Browser checks:
"Origin http://192.168.2.141:3000 matches * (yes)
 Methods include POST (yes)
 Credentials allowed (yes)
 Let this request through ✓"
```

### Why It's Safe Despite Allow-All CORS

| Risk | Mitigated By | Details |
|------|-------------|---------|
| **Any website accesses data** | JWT authentication | Must have valid token |
| **Unauthorized API calls** | Token verification | Token expires in 30 days |
| **Database credentials leaked** | Backend only | Phone never sees DB details |
| **Internet exposure** | Local WiFi only | Not accessible from internet |
| **Data tampering** | HTTPS ready | Can add SSL in production |

---

## Startup Order

### Why Order Matters

```
Timeline:
═════════════════════════════════════════════════════════════

1. ollama serve
   ├─ Starts Ollama service
   ├─ Loads AI models into memory
   └─ Ready on port 11434

2. uv run main.py  ← Waits for Ollama
   ├─ Imports OllamaLLMService
   ├─ Tries to connect to port 11434
   ├─ If Ollama not ready → Error
   └─ Starts API server on port 8001

3. HOST=0.0.0.0 npm start
   ├─ Builds React bundle
   ├─ Starts dev server on port 3000
   └─ Ready for browser access
```

### What Happens If You Skip Steps

```
Skip step 1 (ollama serve):
┌─────────────────────────────────┐
│ uv run main.py                  │
│ ConnectionError: Failed to       │
│ connect to Ollama at 11434      │
│ ERROR: Backend crashes          │
└─────────────────────────────────┘

Skip step 2 (uv run main.py):
┌─────────────────────────────────┐
│ Host=0.0.0.0 npm start          │
│ Frontend loads but all API      │
│ calls fail with 500 errors      │
│ Network connection refused      │
└─────────────────────────────────┘

Skip HOST=0.0.0.0:
┌─────────────────────────────────┐
│ npm start                       │
│ React only on localhost:3000    │
│ Phone opens 192.168.2.112:3000  │
│ Connection refused              │
└─────────────────────────────────┘
```

---

## Startup Commands Reference

### Full Command Sequence

**Terminal 1** (must start first):
```bash
ollama serve
# Output: Listening on 127.0.0.1:11434
```

**Terminal 2** (starts after Ollama):
```bash
cd /Users/wenjuanchen/Dear_Me/backend
uv run main.py
# Output: Uvicorn running on http://0.0.0.0:8001
```

**Terminal 3** (starts after backend):
```bash
cd /Users/wenjuanchen/Dear_Me/frontend
HOST=0.0.0.0 npm start
# Output: webpack compiled successfully
#         Compiled on http://0.0.0.0:3000
```

### Finding Your Laptop's IP

**macOS**:
```bash
ipconfig getifaddr en0
# Output: 192.168.2.112
```

**Linux**:
```bash
hostname -I
# Output: 192.168.2.112 127.0.0.1
```

**Windows**:
```bash
ipconfig
# Look for IPv4 Address under your WiFi connection
```

### Access URLs

| Device | URL |
|--------|-----|
| Desktop | `http://localhost:3000` |
| Phone | `http://<your-laptop-ip>:3000` |
| API Docs | `http://localhost:8001/docs` |

---

## Troubleshooting

### Problem: Phone Can't Connect to App

**Symptoms**: `Connection refused`, `Unable to reach server`

**Checklist**:
1. ✅ Both on same WiFi network?
2. ✅ Laptop IP correct? (`ipconfig getifaddr en0`)
3. ✅ Started with `HOST=0.0.0.0 npm start`?
4. ✅ All three services running?

**Solution**:
```bash
# Terminal 1
ollama serve

# Terminal 2
cd backend && uv run main.py

# Terminal 3
cd frontend && HOST=0.0.0.0 npm start
```

### Problem: "Sorry, something went wrong"

**Symptoms**: App loads but messages fail with error

**Likely causes**:
1. Backend not running → Start `uv run main.py`
2. Ollama not running → Start `ollama serve`
3. CORS issue → Check backend logs
4. JWT expired → Log out and log back in

**Check backend logs**:
```bash
# Look for error messages in Terminal 2
# Should see "INFO: {ip} - POST /llm/conversation HTTP/1.1 200 OK"
```

### Problem: "Network Error" on Login

**Symptoms**: Can't register or log in

**Likely causes**:
1. Authentication service down → Check backend
2. Database locked → Restart backend
3. Argon2 missing → Run `pip install argon2-cffi`

**Debug**:
```bash
# Test API directly
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}'
```

### Problem: LLM Takes Forever / No Response

**Symptoms**: Message sent but no response for 30+ seconds

**Likely causes**:
1. Ollama model loading → First request is slow
2. Model not downloaded → Check `ollama list`
3. LLM out of memory → Restart Ollama

**Check Ollama**:
```bash
ollama list
# Should show: llama3.1:8b or qwen3:8b

# If missing:
ollama pull llama3.1:8b
```

### Problem: Phone Gets Blank Screen

**Symptoms**: App opens but nothing loads

**Likely causes**:
1. Wrong IP address → Double-check `ipconfig getifaddr en0`
2. Port conflict → Check if 3000 is in use
3. React build failed → Check npm terminal for errors

**Solution**:
```bash
# Restart frontend with correct host
cd frontend
HOST=0.0.0.0 npm start
```

---

## Advanced Topics

### Modifying API Host at Runtime

If you need to change the API host without restarting:

```typescript
// frontend/src/utils/api.ts
export const setAPIBaseURL = (newURL: string) => {
  api.defaults.baseURL = newURL;
};

// Usage:
setAPIBaseURL('http://192.168.1.50:8001');
```

### Adding HTTPS (Production)

For production, add SSL certificates:

```python
# Use Uvicorn with SSL
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8001 \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem
```

### Load Balancing Multiple Phones

To serve multiple phones simultaneously, no changes needed! FastAPI handles concurrent requests automatically.

### Exposing to Internet (Security Warning ⚠️)

**DO NOT expose this to the internet without:**
1. HTTPS/SSL encryption
2. Strong authentication (2FA)
3. Rate limiting
4. Security audit
5. Database backups

---

## Summary

### The Mechanism in One Sentence

Your laptop runs three web services (React, FastAPI, Ollama) on `0.0.0.0` (all network interfaces), your phone connects to the same WiFi and opens the React app using your laptop's IP address, the JavaScript app auto-detects the API server location and makes requests, the backend has CORS configured to allow cross-origin requests, and all data flows over your private WiFi network.

### Key Takeaways

| Concept | Key Point |
|---------|-----------|
| **Hostname Detection** | Frontend automatically finds backend using browser's `window.location.hostname` |
| **CORS** | Backend explicitly allows requests from any origin (safe on private WiFi) |
| **Port Binding** | `HOST=0.0.0.0` makes React accessible from network |
| **Startup Order** | Ollama → Backend → Frontend |
| **Security** | JWT tokens authenticate every request, no credentials exposed |
| **Network** | All communication over private WiFi, zero internet exposure |

### Architecture is Production-Ready For

✅ Single user journaling
✅ Local WiFi access
✅ No internet needed
✅ Complete data privacy
✅ Personal AI assistant

### Not Recommended For

❌ Multiple users from internet
❌ Mobile app (would need native app)
❌ Cloud deployment (use cloud provider)
❌ Sharing with strangers

---

## Additional Resources

- **CORS Explained**: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- **JWT Authentication**: https://jwt.io/introduction
- **FastAPI CORS**: https://fastapi.tiangolo.com/tutorial/cors/
- **React Environment Variables**: https://create-react-app.dev/docs/advanced-configuration/

---

**Last Updated**: February 28, 2026
**Version**: 1.0
**Part of**: Phase 1.1 Mobile Responsive Layout Implementation
