# Dear Me - Platform Installation Guide

## Overview

Dear Me provides professional, one-click installers for both macOS and Windows, with completely organized and documented codebases for each platform.

---

## 🍎 macOS Installation

### For End Users

**Download**: [Dear_Me_1.0.0_macOS.dmg](https://github.com/travelingradish/Dear_Me/releases/download/v1.0.0-beta/Dear_Me_1.0.0_macOS.dmg)

**Installation Steps**:
1. Download and double-click the DMG
2. Drag "Dear Me.app" to Applications
3. Double-click `install_dependencies.sh` to install Python, Node.js, Ollama
4. Open Dear Me from Applications
5. Create account and start journaling!

**First Launch**: ~2-3 minutes  
**Subsequent Launches**: ~30 seconds

**Troubleshooting**: See `macos/README_macOS.txt`

### For macOS Developers

**Location**: `macos/` directory

**Key Files**:
- `setup.sh` - Daily launcher (called by app bundle)
- `build_dmg.sh` - Builds the .dmg installer
- `README_macOS.txt` - User guide
- `DEVELOPER_GUIDE.md` - Complete developer documentation

**Build the DMG**:
```bash
cd macos
chmod +x build_dmg.sh
./build_dmg.sh
# Output: Dear_Me_1.0.0_macOS.dmg
```

**Tech Stack**:
- Bash for scripting
- Homebrew for package management (Python, Node.js, Ollama)
- DMG for distribution
- Ready for code signing with Apple Developer certificate

---

## 🪟 Windows Installation

### For End Users

**Download**: [Dear_Me_1.0.0_Windows.exe](https://github.com/travelingradish/Dear_Me/releases/download/v1.0.0-beta/Dear_Me_1.0.0_Windows.exe)

**Installation Steps**:
1. Download and run the .exe installer
2. If SmartScreen appears: click "More info" → "Run anyway"
3. Installer automatically installs Python, Node.js, Ollama
4. Click "Dear Me" shortcut on Desktop to launch
5. Create account and start journaling!

**First Launch**: ~30 seconds  
**Subsequent Launches**: ~30 seconds

**Troubleshooting**: See `windows/README_Windows.txt`

### For Windows Developers

**Location**: `windows/` directory

**Key Files**:
- `setup_windows.bat` - Daily launcher (double-click to run)
- `build_installer.ps1` - Builds the .exe installer
- `build_installer.nsi` - NSIS installer script
- `install_dependencies.ps1` - First-time setup script
- `README_Windows.txt` - User guide
- `DEVELOPER_GUIDE.md` - Complete developer documentation

**Build the EXE**:
```powershell
cd windows
powershell -ExecutionPolicy Bypass -File build_installer.ps1
# Output: Dear_Me_1.0.0_Windows.exe
```

**Tech Stack**:
- PowerShell for scripting
- Batch for daily launcher
- NSIS for installer building
- winget for package management (Python, Node.js, Ollama)
- Ready for code signing with EV certificate

---

## 📊 Platform Comparison

| Feature | macOS | Windows |
|---------|-------|---------|
| **Download Format** | DMG (34 MB) | EXE (80-100 MB) |
| **First Install** | 15-20 minutes | 15-20 minutes |
| **Daily Launch** | ~30 seconds | ~30 seconds |
| **Package Manager** | Homebrew | winget |
| **Scripting** | Bash | Batch + PowerShell |
| **Installer** | DMG native | NSIS |
| **Code Signing** | Ready (Apple cert) | Ready (EV cert) |
| **SmartScreen** | No warning | Warning (unsigned) |
| **Supported OS** | macOS 10.13+ | Windows 10+ |

---

## 🔄 Installation Flow Comparison

### macOS Flow
```
User downloads DMG
    ↓
Double-click to mount
    ↓
Drag app to Applications
    ↓
Run install_dependencies.sh
    ↓
Homebrew checks/installs: Python, Node.js, Ollama
    ↓
pip install requirements
    ↓
Ready to use!
    ↓
Daily: Double-click app in Applications
```

### Windows Flow
```
User downloads EXE
    ↓
Run installer
    ↓
(SmartScreen: More info → Run anyway)
    ↓
Installer runs install_dependencies.ps1
    ↓
winget checks/installs: Python, Node.js, Ollama
    ↓
pip install requirements
    ↓
Desktop shortcut created
    ↓
Ready to use!
    ↓
Daily: Double-click "Dear Me" on Desktop
```

---

## 🎯 Key Technical Differences

### Frontend Serving

**macOS**:
- Uses `npm start` (CRA dev server)
- Slower startup (~45 seconds) but allows hot-reload during development
- Designed for developer flexibility

**Windows**:
- Uses `python -m http.server` with pre-built `frontend/build/`
- Faster startup (~instant) 
- Designed for user experience priority
- Eliminates Node.js runtime requirement at launch

### Dependency Management

**macOS**:
- Homebrew handles most dependencies
- No Windows-specific gotchas
- Clean uninstall with `brew uninstall`

**Windows**:
- winget handles most dependencies
- Must handle MSVC C++ build tools for `chromadb`
- Must set `HF_HOME` environment variable (path length limits)
- Batch file handles port detection differently

### Port Conflict Resolution

**macOS**:
```bash
lsof -ti:8001 | xargs kill -9
```

**Windows**:
```powershell
Get-NetTCPConnection -LocalPort 8001 -State Listen | Stop-Process -Force
```

---

## 📋 Choosing Which Installer to Use

### Use macOS Installer If:
- You're on a Mac (Intel or Apple Silicon)
- You prefer a native Mac experience
- You want future code signing capability

### Use Windows Installer If:
- You're on Windows 10 or later
- You want instant startup times
- You want automatic dependency installation

### Use Terminal Setup (`./setup.sh`) If:
- You're a developer contributing to the project
- You want to run the latest code from git
- You need to debug or modify components

---

## 🛠️ Developer Quick Reference

### macOS Developers

```bash
# Daily development
cd macos && ./setup.sh

# Build DMG for distribution
cd macos && ./build_dmg.sh

# See full guide
cat macos/DEVELOPER_GUIDE.md
```

### Windows Developers

```powershell
# Daily development
cd windows && .\setup_windows.bat

# Build EXE for distribution
cd windows && powershell -ExecutionPolicy Bypass -File build_installer.ps1

# See full guide
Get-Content windows\DEVELOPER_GUIDE.md
```

### Both Platforms (Backend/Frontend Development)

```bash
# See CLAUDE.md for full development setup
cat CLAUDE.md

# Backend development (from backend/)
uv run main.py

# Frontend development (from frontend/)
npm start
```

---

## 📦 Distribution & Release

### Preparing a Release

1. **Build both installers** (on respective platforms):
   ```bash
   # On Mac
   cd macos && ./build_dmg.sh
   
   # On Windows
   cd windows && powershell -ExecutionPolicy Bypass -File build_installer.ps1
   ```

2. **Upload to GitHub Releases**:
   ```bash
   gh release create v1.0.0-beta \
     --files Dear_Me_1.0.0_macOS.dmg \
     --files Dear_Me_1.0.0_Windows.exe
   ```

3. **Update README.md** with download links

4. **Announce on channels** (GitHub Discussions, social media, etc.)

### CI/CD Automation (Future)

Can be automated with GitHub Actions:
- macOS build on `ubuntu-latest` + Homebrew
- Windows build on `windows-latest` + winget
- Auto-upload to releases
- Code signing integration

---

## ❓ Common Questions

**Q: Can I use the macOS DMG on Windows?**  
A: No, they're platform-specific. Download the Windows EXE instead.

**Q: Do I need to be a developer to use Dear Me?**  
A: No! Just download the appropriate installer for your OS. See "For End Users" above.

**Q: How do I report bugs?**  
A: Please open an issue on [GitHub Issues](https://github.com/travelingradish/Dear_Me/issues).

**Q: Can I help build installers for Linux?**  
A: Yes! The directory structure supports `linux/` directory. Get in touch on GitHub.

**Q: What if the installer fails?**  
A: See the platform-specific guide:
- `macos/README_macOS.txt` for macOS
- `windows/README_Windows.txt` for Windows

**Q: Is my journal data safe?**  
A: Yes! Your journal stays on your computer in `dear_me.db`. Never sent to external servers. See privacy section in platform guides.

---

## 📚 Additional Resources

- **User Guides**: `macos/README_macOS.txt`, `windows/README_Windows.txt`
- **Developer Guides**: `macos/DEVELOPER_GUIDE.md`, `windows/DEVELOPER_GUIDE.md`
- **Full Project Guide**: `CLAUDE.md`
- **Bug Reports**: [GitHub Issues](https://github.com/travelingradish/Dear_Me/issues)
- **Source Code**: [GitHub Repository](https://github.com/travelingradish/Dear_Me)

---

**Version**: 1.0.0-beta  
**Last Updated**: March 2026
