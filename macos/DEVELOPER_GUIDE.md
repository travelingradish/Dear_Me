# macOS Installer - Developer Guide

## Overview

The macOS installer system provides a professional one-click experience using native Apple tooling:
- **Bash** for scripting (`setup.sh`)
- **DMG (Disk Image)** for distribution (equivalent to Windows `.exe`)
- **Homebrew** for dependency management
- **Code signing** ready (can be added later with Apple Developer certificate)

## File Structure

```
macos/
├── setup.sh                        # Daily launcher (runs from app bundle)
├── build_dmg.sh                    # DMG builder (creates .dmg installer)
├── Dear Me.command                 # Desktop shortcut template
├── test_install_dependencies.command  # Optional test script
├── dmg_build/                      # DMG resources and configuration
├── DEVELOPER_GUIDE.md              # This file
└── README_macOS.txt                # User guide (optional, can be in .dmg)
```

## Building the Installer (For Developers)

### Prerequisites
Install on your **macOS development machine**:

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Xcode Command Line Tools (required for DMG signing/building)
xcode-select --install

# Install dmg builder tools
brew install create-dmg
```

### Build Steps

```bash
cd macos
chmod +x build_dmg.sh
./build_dmg.sh
```

**Result**: `Dear_Me_1.0.0_macOS.dmg` at project root (~34 MB)

### Build Output

- **Signed DMG** (optional with Apple Developer certificate)
- **Professional appearance**: Finder window with app icon + Applications folder
- **Automatic mounting**: DMG opens in Finder on download
- **License file**: Shown during installation

## How It Works

### Installation Flow (First Time)

```
User downloads Dear_Me_1.0.0_macOS.dmg
         ↓
    [Double-click to mount]
         ↓
   Finder window opens showing:
   - "Dear Me.app" (the application)
   - "Applications" folder (drag-to-install target)
         ↓
   User drags Dear Me.app to Applications
         ↓
   User runs install_dependencies.sh (or setup.sh)
         ↓
   ✓ Check/install Homebrew
   ✓ Install Python 3.13 (via brew)
   ✓ Install Node.js (via brew)
   ✓ Install Ollama (via brew)
   ✓ Create Python venv
   ✓ pip install -r requirements.txt
   ✓ Optional: ollama pull llama3.1:8b
         ↓
   Copy setup.sh to Desktop (optional)
```

### Daily Launch Flow (After Installation)

```
User opens Applications → Double-click "Dear Me.app"
         ↓
    [setup.sh executes]
         ↓
   [0/6] Check and install Homebrew if needed
   [1/6] Check prerequisites (node, npm, ollama, curl)
   [2/6] Clean up port conflicts (ports 8001, 3000)
   [3/6] Start Ollama (or reuse existing instance)
   [4/6] Start backend (python main.py)
   [5/6] Start frontend (npm start in CRA dev server)
         ↓
   Poll localhost:8001 and :3000 until both respond
         ↓
   Print success banner with local + WiFi IP
         ↓
   Open browser to http://localhost:3000
         ↓
   Monitor loop every 10s → restart backend if crashed
         ↓
   Cleanup on Ctrl+C (kill background processes)
```

## Key Technical Decisions

### Why Homebrew?

- ✅ Native macOS package manager
- ✅ Simple, one-line installation for users
- ✅ Automatic dependency resolution
- ✅ Easy uninstall (brew uninstall python node ollama)
- ⚠️ Requires internet connection during first install

### Why DMG Instead of Installer.app?

- ✅ Familiar to macOS users (drag-and-drop)
- ✅ No special installer UI needed
- ✅ Users see what they're installing (app icon visible)
- ✅ Smaller download than full installer package
- ⚠️ User manually drags (one extra step vs. automatic install)

### Why npm start Instead of http.server?

**Difference from Windows:**
- **macOS setup.sh**: Uses `npm start` (CRA dev server) with `BROWSER=none`
  - ✅ Hot-reload capability during development
  - ✅ Better error messages
  - ⚠️ Takes 30-45 seconds to start

- **Windows setup_windows.bat**: Uses `python -m http.server` (pre-built frontend)
  - ✅ Instant startup
  - ⚠️ No hot-reload

**Why the difference?**
- macOS `setup.sh` is designed for developers (hot-reload useful)
- Windows batch is for non-technical users (startup speed priority)
- Could be unified in future by adding pre-built frontend option

## Handling macOS-Specific Gotchas

### Gotcha 1: M1/M2 (Apple Silicon) Architecture

**Problem**: Some packages have different binaries for Intel vs. Apple Silicon

**Solution**: Homebrew handles this automatically
- `arch_preferred=arm64` for native M-series performance
- Falls back to Intel if needed (Rosetta 2 translation)

**Verification**:
```bash
arch  # Should show arm64 on M1/M2, i386 on Intel
```

### Gotcha 2: Python Installation Path

**Problem**: Homebrew installs Python in different locations depending on Mac version

**Solution**: `setup.sh` uses `command -v python3` to find it, not hardcoded paths

**Current path in setup.sh**:
```bash
UV_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin/uv"
```

### Gotcha 3: Ollama Service Management

**Problem**: Unlike Windows (background service), macOS Ollama is a background process

**Solution**: `setup.sh` checks if running via `curl http://localhost:11434/`:
- If running → reuse
- If not → start with `ollama serve` in background

### Gotcha 4: Port Conflicts

**Solution**: `setup.sh` uses `lsof -Pi ":8001"` to find processes using ports, then `kill -9`

### Gotcha 5: npm start Slow on Some Macs

**Problem**: React dev server can take 30-45 seconds to start

**Workaround**: Could switch to pre-built frontend like Windows, but haven't implemented

## DMG Building Process

The `build_dmg.sh` script:

1. **Builds frontend**: Runs `npm ci && npm run build`
2. **Creates app bundle**: Uses `create-dmg` to generate `.dmg`
3. **Configures appearance**:
   - App icon positioned
   - Applications folder symlink visible
   - Custom background (if provided in dmg_build/)
4. **Adds signing** (optional): Can be enabled with Apple Developer cert
5. **Output**: `Dear_Me_1.0.0_macOS.dmg` ready for distribution

## Testing the Installer

### On a Clean macOS VM

1. **Test setup.sh launcher**:
   ```bash
   cd macos
   ./setup.sh
   ```
   Verify: Services start, browser opens to http://localhost:3000

2. **Test DMG**:
   - Download and double-click
   - Drag app to Applications
   - Run installer script
   - Launch from Applications → verify app works

3. **Test uninstall**:
   ```bash
   brew uninstall python node ollama
   rm -rf ~/Library/Frameworks/Python.framework
   ```

## Distribution

### GitHub Releases

Upload to releases:
```bash
gh release create v1.0.0-beta --files Dear_Me_1.0.0_macOS.dmg
```

### Code Signing (Optional, For Production)

With Apple Developer certificate:
```bash
# Sign the app before DMG creation
codesign -s "Developer ID Application: Your Name" Dear\ Me.app

# Sign the DMG
codesign -s "Developer ID Application: Your Name" Dear_Me_1.0.0_macOS.dmg
```

### Notarization (Optional, Apple's Gatekeeper)

For apps distributed outside the App Store:
```bash
xcrun notarytool submit Dear_Me_1.0.0_macOS.dmg \
  --apple-id "your-email@example.com" \
  --team-id "XXXXXXXXXX" \
  --password "app-specific-password"
```

This prevents "cannot be opened because Apple cannot check it for malware" warning.

## Performance Notes

| Operation | Time | Notes |
|-----------|------|-------|
| First install | 15-20 min | Homebrew downloads + pip install |
| npm start first time | 45-90 sec | CRA bundling |
| Subsequent launch | 2-3 min | npm start + bundling |
| Uninstall | < 1 min | brew uninstall |

Note: `npm start` time varies greatly by Mac spec and disk speed.

## Future Improvements

1. **Pre-built frontend**: Add `--prebuild` flag to use http.server like Windows (instant startup)
2. **Code signing**: Automate with CI/CD pipeline
3. **Notarization**: Auto-notarize on release
4. **Auto-update**: Implement with Sparkle framework
5. **dmg_build customization**: Custom background image with app mockup

## Troubleshooting Checklist

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| "Cannot open DMG" | Corrupted download | Re-download from GitHub |
| "App cannot be opened" | Gatekeeper blocking unsigned app | Right-click → Open → Open anyway |
| "Homebrew not found" | Not installed | Run `/bin/bash -c "$(curl...)"` |
| "Port 8001 in use" | Another app using port | `lsof -ti:8001 \| xargs kill -9` |
| "npm not found" | Node not installed | Run setup.sh to install |
| "Model not downloading" | Network issue | Try again later or manual: `ollama pull` |
| "npm start hangs" | Slow machine or disk | Wait longer or use pre-built frontend |

## File Locations After Installation

After user completes setup:

```
~/Applications/
└── Dear Me.app               # The bundled application
    └── Contents/
        ├── MacOS/            # Binary/scripts
        │   └── setup.sh      # Main launcher
        └── Resources/        # Assets

~/projects/dear_me/           # Project code (if git cloned)
├── backend/
│   ├── venv/                 # Virtual environment
│   └── dear_me.db            # SQLite database (user journal)
├── frontend/
│   └── build/                # Built React app
└── macos/                    # This directory
```

---

**Last updated**: March 2026
