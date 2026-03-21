# Windows Installer - Developer Guide

## Overview

The Windows installer system replicates the macOS DMG experience using native Windows tools:
- **PowerShell** for scripting
- **NSIS 3.0+** for building the `.exe` installer
- **`python -m http.server`** for serving the pre-built React frontend (eliminates npm startup overhead)

## File Structure

```
windows/
├── install_dependencies.ps1    # First-time installer (runs inside NSIS)
├── setup_windows.bat           # Daily launcher (double-click to run)
├── build_installer.ps1         # Build orchestrator (dev machine only)
├── build_installer.nsi         # NSIS installer script (macOS equivalent: build_dmg.sh)
├── assets/
│   ├── dear_me.ico            # App icon (auto-generated from logo192.png)
│   └── installer_banner.bmp   # Optional NSIS header image
├── README_Windows.txt          # User guide bundled in installer
├── DEVELOPER_GUIDE.md         # This file
└── ASSETS_README.md           # Icon/asset instructions
```

## Building the Installer (For Developers)

### Prerequisites
Install on your **Windows development machine** (not needed for end users):

```powershell
# Install NSIS
winget install NSIS.NSIS

# Install Node.js (if you need to rebuild frontend)
winget install OpenJS.NodeJS.LTS
```

### Build Steps

1. **Ensure frontend is built** (pre-built `frontend/build/` already exists):
```powershell
cd windows
powershell -ExecutionPolicy Bypass -File build_installer.ps1
```

2. **Result**: `Dear_Me_1.0.0_Windows.exe` at project root

3. **Optional: Force rebuild frontend**:
```powershell
powershell -ExecutionPolicy Bypass -File build_installer.ps1 -BuildFrontend
```

### Build Output

- **Unsigned executable** (~80-100 MB) - normal for early-stage projects
- **SmartScreen warning on first run** - expected, document "More info → Run anyway"
- **Optional code signing** (add later with EV certificate from trusted provider)

## How It Works

### Installation Flow (First Time)

```
User runs Dear_Me_1.0.0_Windows.exe
         ↓
    [NSIS Installer]
         ↓
   Copy files to %LOCALAPPDATA%\DearMe\
         ↓
   Run install_dependencies.ps1 (with elevation)
         ↓
   ✓ Install Python 3.13 (via winget)
   ✓ Install Node.js LTS (via winget)
   ✓ Install Ollama (via winget)
   ✓ Create Python venv
   ✓ pip install -r requirements.txt
   ✓ Optional: ollama pull llama3.1:8b
         ↓
   Create Desktop shortcut + Start Menu shortcuts
         ↓
   Show README_Windows.txt guide
```

### Daily Launch Flow (After Installation)

```
User double-clicks "Dear Me" on Desktop
         ↓
    [setup_windows.bat]
         ↓
   [1] Verify venv exists → error if missing
   [2] Free ports 8001, 3000 (kill existing processes)
   [3] Verify Ollama service → start if needed
   [4] Poll http://localhost:11434/ → wait for model
   [5] Start backend: venv\Scripts\python main.py
   [6] Start frontend: python -m http.server 3000 --directory ../frontend/build
         ↓
   Poll localhost:8001 and :3000 until both respond
         ↓
   Print success banner with local + WiFi IPs
         ↓
   Open browser to http://localhost:3000
         ↓
   Monitor loop every 10s → restart backend if crashed
         ↓
   Cleanup on window close (taskkill -FI "WINDOWTITLE eq ...")
```

## Key Technical Decisions

### Why `python -m http.server` for Frontend?

**Problem**: macOS uses `npm start` (CRA dev server) → 30-45 second startup on every launch

**Solution**: Use pre-built `frontend/build/` with `python -m http.server 3000`:
- ✅ Instant startup (~1 second)
- ✅ No Node.js runtime needed at launch
- ✅ CORS configured in FastAPI allows `*` origin
- ✅ Reduces perceived startup time from 45s to ~30s total

**Trade-off**: Can't hot-reload during daily use (acceptable for production experience)

### Why Batch File + PowerShell Instead of Unified Script?

**Batch file** (`setup_windows.bat`):
- ✅ Double-click friendly (no policy bypass needed)
- ✅ Can check venv existence simply
- ✅ Works in Command Prompt
- ⚠️ Limited features (no JSON parsing, weak string handling)

**PowerShell** (`install_dependencies.ps1`):
- ✅ Self-elevation to Administrator
- ✅ Sophisticated installation logic (winget, pip error handling)
- ✅ Environment variable management
- ⚠️ Requires ExecutionPolicy bypass

**Solution**: Batch for daily use, PowerShell for first-time setup (users accept complexity once)

### Why Not Use Chocolatey or Direct Python Download?

1. **winget** is built into Windows 11 (official, minimal overhead)
2. **Fallback URL** provided if winget fails (direct python.org download)
3. **Consistent with macOS** (brew → python.org fallback pattern)

### Why NSIS Over WiX or Inno Setup?

1. **Lightweight** (~2 MB tool, simple scripting)
2. **Widely used** (transparent community, many examples)
3. **Simple configuration** (one .nsi file vs. complex .wxs XML)
4. **Fast installer** (~15 MB output size)

## Handling Windows-Specific Gotchas

### Gotcha 1: MSVC C++ Build Tools Required

**Problem**: `chromadb` and `sentence-transformers` require C++ compilation on Windows

**Detection**: Catch pip install error containing "MSBuild.exe not found"

**Solution** (in `install_dependencies.ps1`):
```powershell
if ($pipOutput -match "error: Microsoft Visual C\+\+ 14\.0") {
    Print-Error "Missing C++ build tools"
    Print-Warning "Visit: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
}
```

**User workaround**: Install Visual C++ Build Tools, then re-run installer

### Gotcha 2: Long Path Limit (260 chars)

**Problem**: `sentence-transformers` cache creates deeply nested paths

**Solution**: Set `HF_HOME` early:
```powershell
[Environment]::SetEnvironmentVariable("HF_HOME", "$env:LOCALAPPDATA\DearMe\model_cache", "User")
```

This keeps cache paths short:
- ✅ `%LOCALAPPDATA%\DearMe\model_cache\...` (short)
- ❌ `%LOCALAPPDATA%\huggingface\hub\models\...` (can exceed 260 chars)

### Gotcha 3: PowerShell Execution Policy

**Problem**: Scripts can't run without changing execution policy

**Solution**: Run with `-ExecutionPolicy Bypass`:
```powershell
powershell -ExecutionPolicy Bypass -File install_dependencies.ps1
```

This applies only to that process, doesn't change system policy.

### Gotcha 4: Ollama Service vs. Process

**macOS**: `ollama serve` is a foreground process you manage

**Windows**: `ollama` runs as background service (auto-installed by winget)

**Solution**: Only poll HTTP endpoint, don't try to start process:
```batch
powershell -Command "Invoke-WebRequest http://localhost:11434/ -TimeoutSec 1"
```

### Gotcha 5: Port Detection in Batch Files

**Problem**: `netstat | findstr` is slow and fragile across Windows versions

**Solution**: Use PowerShell inside batch for more reliable detection:
```batch
powershell -Command "Get-NetTCPConnection -LocalPort 8001 -State Listen"
```

## Testing the Installer

### On a Clean Windows VM

1. **Test install_dependencies.ps1 standalone**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File install_dependencies.ps1
   ```
   Verify: Python 3.13, Node.js, Ollama, venv created, requirements installed

2. **Test setup_windows.bat**:
   ```batch
   cd backend
   ..\windows\setup_windows.bat
   ```
   Verify: Services start, browser opens to http://localhost:3000, journal loads

3. **Test full installer .exe**:
   - Download from GitHub release
   - Run on clean Windows VM (no Python/Node/Ollama)
   - Verify shortcuts created, app launches
   - Check Add/Remove Programs shows correct metadata

### SmartScreen Behavior

First download: Windows Defender SmartScreen blocks `.exe`
- User clicks "More info"
- Clicks "Run anyway"
- **Key**: Don't sign with paid certificate; cost isn't justified for early beta

## Distribution

### GitHub Releases

Upload to releases:
```bash
# After building
gh release create v1.0.0-beta --files Dear_Me_1.0.0_Windows.exe
```

### Size Management

- **Current**: ~80-100 MB unsigned executable (reasonable)
- **Compressed**: Could reduce ~30% with UPX, not recommended (breaks SmartScreen reputation)
- **Backend included**: All Python code + venv takes ~200 MB (one-time)
- **Frontend**: Only `build/` dir, no node_modules (~5 MB)

## Future Improvements

1. **Signing**: With EV code signing certificate (for production)
2. **Auto-update**: NSIS has update framework (defer for v1.1)
3. **Installer customization**: Custom banner, Welcome page text
4. **Linux AppImage**: Similar structure to Windows, but `./AppRun` instead of batch

## Troubleshooting Checklist

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| installer won't run | SmartScreen | "More info" → "Run anyway" |
| Python install fails | Network/winget down | Manual install from python.org |
| pip install fails | Missing MSVC | Install Visual C++ Build Tools |
| Ollama not found | Service not running | Start Ollama from Windows Services |
| Port in use | Another app using 8001/3000 | Kill with taskkill or restart |
| "venv not found" | installer didn't run | Re-run install_dependencies.ps1 |
| frontend blank | wrong PORT or build/ missing | Verify frontend/build/index.html exists |
| slow startup first time | model downloading | Wait for `ollama pull` to complete |

## Performance Notes

| Operation | Time | Notes |
|-----------|------|-------|
| First install | 10-15 min | Downloads + installs + model (~4.7GB) |
| Subsequent launch | 30 sec | venv activation + service startup |
| Model first use | 30s overhead | embedding generation cached by chromadb |
| Uninstall | < 1 min | Preserves dear_me.db |

---

**Last updated**: March 2026
