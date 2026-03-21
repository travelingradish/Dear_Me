# Windows Installer - Comprehensive Test Plan

**Purpose**: Ensure the Windows one-click installer works correctly on clean Windows systems

**Test Environment**: Windows 10 or Windows 11 (clean VM recommended)

---

## 📋 Test Categories

### 1. **PowerShell Installation Script Tests** (`install_dependencies.ps1`)

#### Test 1.1: Admin Elevation
- [ ] Run script without admin privileges
- [ ] Verify script prompts for elevation
- [ ] Verify script re-launches as admin after elevation
- [ ] Confirm user sees progress messages during elevation

#### Test 1.2: Python Installation
- [ ] Verify Python 3.13 installs via winget
- [ ] Confirm python.exe is in PATH
- [ ] Test: `python --version` returns 3.13.x
- [ ] Test: `pip --version` works from command prompt
- [ ] Fallback: If winget fails, verify error message with python.org URL

#### Test 1.3: Node.js Installation
- [ ] Verify Node.js LTS installs via winget
- [ ] Confirm node.exe is in PATH
- [ ] Test: `node --version` returns correct LTS version
- [ ] Test: `npm --version` works from command prompt
- [ ] Verify npm can install packages (from frontend directory)

#### Test 1.4: Ollama Installation
- [ ] Verify Ollama installs via winget
- [ ] Confirm ollama.exe is available
- [ ] Verify Ollama service starts automatically
- [ ] Test: `ollama list` shows available models
- [ ] Verify HTTP endpoint: `curl http://localhost:11434/` responds

#### Test 1.5: Virtual Environment Setup
- [ ] Verify venv directory created at `backend/venv/`
- [ ] Confirm venv has proper structure (Scripts/, Lib/, etc.)
- [ ] Test: `venv\Scripts\pip.exe --version` works
- [ ] Test: `venv\Scripts\python.exe --version` works

#### Test 1.6: Requirements Installation
- [ ] Verify all Python packages install without errors
- [ ] Watch for MSVC C++ build tools warning (if not installed)
- [ ] If MSVC error appears:
  - [ ] Verify error message is clear
  - [ ] Verify URL to Visual C++ Build Tools is provided
  - [ ] User can see the error in the output

#### Test 1.7: Environment Variables
- [ ] Verify `HF_HOME` set to `%LOCALAPPDATA%\DearMe\model_cache`
- [ ] Test: `echo %HF_HOME%` shows correct path
- [ ] Verify path persists after script ends
- [ ] Confirm path survives system restart

#### Test 1.8: Model Download (Optional)
- [ ] When user selects "Y" for model download:
  - [ ] Verify `ollama pull llama3.1:8b` starts
  - [ ] Watch download progress (~4.7GB)
  - [ ] Confirm download completes or user can cancel
- [ ] When user selects "N":
  - [ ] Script continues without downloading
  - [ ] User sees message: "Model download skipped"
  - [ ] User gets instructions for manual download later

#### Test 1.9: Error Handling
- [ ] Network failure during winget install → Clear error message
- [ ] Disk full during pip install → Clear error message
- [ ] Interrupted by user (Ctrl+C) → Graceful exit message
- [ ] Script run twice → Detects existing installations, doesn't duplicate

---

### 2. **Batch File Launcher Tests** (`setup_windows.bat`)

#### Test 2.1: Virtual Environment Verification
- [ ] Run setup_windows.bat on system without venv
- [ ] Verify it shows: "Virtual environment not found!"
- [ ] Verify it instructs user to run install_dependencies.ps1
- [ ] Confirm batch file exits with error code 1

#### Test 2.2: Port Conflict Detection
- [ ] Start another process on port 8001
- [ ] Run setup_windows.bat
- [ ] Verify batch file detects port 8001 in use
- [ ] Verify batch file kills the conflicting process
- [ ] Confirm ports are freed and available

#### Test 2.3: Port Conflict Detection (Port 3000)
- [ ] Start another process on port 3000
- [ ] Run setup_windows.bat
- [ ] Verify batch file detects and frees port 3000

#### Test 2.4: Ollama Service Check
- [ ] Run setup_windows.bat when Ollama is running
- [ ] Verify script detects HTTP response from `http://localhost:11434/`
- [ ] Confirm it shows "✓ Ollama service is running"

#### Test 2.5: Ollama Service Not Running
- [ ] Run setup_windows.bat when Ollama service is stopped
- [ ] Verify script attempts to poll Ollama multiple times
- [ ] If Ollama doesn't respond after 15 attempts:
  - [ ] Shows clear error: "✗ Ollama service not responding"
  - [ ] Provides installation link: https://ollama.ai
  - [ ] Exits gracefully

#### Test 2.6: Model Verification
- [ ] With model downloaded: Shows "✓ Model is downloaded"
- [ ] Without model: Shows "⚠ Model not found"
- [ ] If model missing: Shows download in progress
- [ ] Wait for model download or user cancels

#### Test 2.7: Backend Startup
- [ ] Run setup_windows.bat with venv and ports free
- [ ] Verify backend window opens with title "DearMe-Backend"
- [ ] Verify backend window is minimized
- [ ] Verify script polls `http://localhost:8001/` up to 60 times
- [ ] After backend responds: Shows "✓ Backend ready at http://localhost:8001"

#### Test 2.8: Backend Startup Failure
- [ ] If backend crashes during startup:
  - [ ] Shows error: "✗ Backend failed to start"
  - [ ] Cleanup triggers (closes backend window)
  - [ ] Batch file exits cleanly

#### Test 2.9: Frontend Startup
- [ ] Verify frontend window opens with title "DearMe-Frontend"
- [ ] Verify frontend window is minimized
- [ ] Verify script polls `http://localhost:3000` up to 15 times
- [ ] After frontend responds: Shows "✓ Frontend ready"

#### Test 2.10: Frontend Startup Failure
- [ ] If frontend doesn't respond after 15 attempts:
  - [ ] Shows error: "✗ Frontend failed to start"
  - [ ] Cleanup triggers
  - [ ] Batch file exits cleanly

#### Test 2.11: Success Banner
- [ ] After both services ready, shows:
  - [ ] "================================"
  - [ ] "Dear Me is running!"
  - [ ] "Desktop: http://localhost:3000"
  - [ ] "API Docs: http://localhost:8001/docs"
- [ ] If WiFi IP detected: Shows "Phone: http/192.168.x.x:3000"
- [ ] Shows: "Press Ctrl+C or close this window to stop all services"

#### Test 2.12: Browser Open
- [ ] After success banner, browser opens to `http://localhost:3000`
- [ ] Verify journal app loads in browser
- [ ] Verify no errors in browser console

#### Test 2.13: Monitor Loop
- [ ] While running, every 10 seconds script checks backend health
- [ ] If backend crashes mid-session:
  - [ ] Script detects it: "✗ Backend crashed"
  - [ ] Cleanup triggers
  - [ ] Batch file exits
- [ ] If frontend crashes:
  - [ ] Script detects it: "✗ Frontend crashed"
  - [ ] Cleanup triggers
  - [ ] Batch file exits

#### Test 2.14: Cleanup on Exit
- [ ] Press Ctrl+C during execution
- [ ] Verify script shows: "Shutting down Dear Me..."
- [ ] Verify backend window closes
- [ ] Verify frontend window closes
- [ ] Verify processes are killed: `tasklist | findstr python`
- [ ] Confirm batch window closes cleanly

#### Test 2.15: Cleanup on Window Close
- [ ] Run setup_windows.bat
- [ ] After services start, close the batch window (X button)
- [ ] Verify cleanup label triggers
- [ ] Verify backend and frontend processes are killed
- [ ] Confirm ports are freed

#### Test 2.16: Multiple Runs
- [ ] Run setup_windows.bat
- [ ] Wait for success
- [ ] Close (Ctrl+C)
- [ ] Immediately run setup_windows.bat again
- [ ] Verify second run successfully kills old processes and starts fresh

---

### 3. **NSIS Installer Tests** (`build_installer.nsi`)

#### Test 3.1: Installer Execution
- [ ] Run `Dear_Me_1.0.0_Windows.exe` on clean Windows
- [ ] Verify installer wizard appears
- [ ] Verify Welcome page displays
- [ ] Verify License page shows LICENSE file
- [ ] Verify Directory page allows changing install location
- [ ] Verify files are copied to `%LOCALAPPDATA%\DearMe\`

#### Test 3.2: File Placement
- [ ] After install, verify directory structure:
  - [ ] `%LOCALAPPDATA%\DearMe\backend\` exists with all Python files
  - [ ] `%LOCALAPPDATA%\DearMe\frontend\build\` exists
  - [ ] `%LOCALAPPDATA%\DearMe\windows\` exists with all scripts
  - [ ] `%LOCALAPPDATA%\DearMe\Uninstall_DearMe.exe` exists

#### Test 3.3: Shortcuts Creation
- [ ] Desktop shortcut "Dear Me" exists
- [ ] Shortcut icon is correct (if icon was created)
- [ ] Shortcut points to: `cmd.exe /c "$INSTDIR\windows\setup_windows.bat"`
- [ ] Double-clicking shortcut launches setup_windows.bat
- [ ] Start Menu folder created: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Dear Me\`
- [ ] Start Menu shortcuts point to correct locations

#### Test 3.4: Registry Entries
- [ ] App appears in Add/Remove Programs:
  - [ ] Settings → Apps → Apps & features
  - [ ] "Dear Me" shown in list
  - [ ] Version shows "1.0.0"
  - [ ] Clicking "Uninstall" starts uninstaller
- [ ] Registry key exists: `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe`
- [ ] Registry contains correct metadata

#### Test 3.5: First-Time Installation Script Runs
- [ ] During install, prerequisites section executes
- [ ] PowerShell runs `install_dependencies.ps1`
- [ ] Installation proceeds (may ask for elevation)
- [ ] Python/Node/Ollama installation happens
- [ ] Requirements are installed
- [ ] Installation completes without errors (or shows warnings)

#### Test 3.6: Admin Elevation During Install
- [ ] When prerequisites run with non-admin user:
  - [ ] PowerShell prompts for elevation
  - [ ] User can accept or cancel
  - [ ] If accepted: installation continues
  - [ ] If cancelled: installer continues (user warned about later issues)

#### Test 3.7: Uninstaller
- [ ] From Add/Remove Programs: Click "Uninstall"
- [ ] Confirmation dialog appears: "Are you sure?"
- [ ] Click "Yes" proceeds with uninstall
- [ ] Click "No" cancels uninstall
- [ ] After uninstall:
  - [ ] Installation directory removed
  - [ ] Desktop shortcut removed
  - [ ] Start Menu folder removed
  - [ ] App removed from Add/Remove Programs
  - [ ] Registry key deleted

#### Test 3.8: Database Preservation
- [ ] After install, create journal entry in Dear Me
- [ ] Data saved to `%LOCALAPPDATA%\DearMe\backend\dear_me.db`
- [ ] Uninstall the app
- [ ] Backup `dear_me.db` was mentioned in uninstall message
- [ ] Database file still exists at installation path

#### Test 3.9: Reinstall Over Existing
- [ ] Install Dear Me
- [ ] Run and create journal entries
- [ ] Run installer again (same version)
- [ ] Choose to uninstall old version, then install new
- [ ] Verify old shortcuts removed
- [ ] Verify database preserved
- [ ] New installation works correctly

---

### 4. **Build Script Tests** (`build_installer.ps1`)

#### Test 4.1: NSIS Detection
- [ ] Run build script on system WITH NSIS installed
- [ ] Verify it detects makensis.exe
- [ ] Confirm build proceeds to NSIS compilation
- [ ] Run build script on system WITHOUT NSIS
- [ ] Verify it shows error: "NSIS not found!"
- [ ] Verify it provides installation URL

#### Test 4.2: Frontend Build
- [ ] Run build script when `frontend/build/` exists
- [ ] Verify it skips frontend build
- [ ] Run with `-BuildFrontend` flag
- [ ] Verify it runs `npm ci && npm run build`
- [ ] Confirm build completes successfully
- [ ] Verify output EXE file is created

#### Test 4.3: Icon Handling
- [ ] Run build script when ImageMagick is installed
- [ ] Verify it attempts: `magick convert logo192.png dear_me.ico`
- [ ] Confirm icon is created successfully
- [ ] Run without ImageMagick
- [ ] Verify it shows warning about manual icon creation
- [ ] Confirm build continues with default icon

#### Test 4.4: NSIS Compilation
- [ ] Verify makensis runs with `/DAPP_VERSION=1.0.0`
- [ ] Confirm build script waits for completion
- [ ] Watch for any compilation errors
- [ ] Verify output file path is correct

#### Test 4.5: Output File Verification
- [ ] After build completes, verify EXE exists:
  - [ ] File path: `Dear_Me_1.0.0_Windows.exe` at project root
  - [ ] File size: 80-100 MB (reasonable)
  - [ ] File is executable (Windows recognizes it)
- [ ] File properties show correct version if signed

#### Test 4.6: Error Handling
- [ ] If NSIS fails: Show error message
- [ ] If frontend build fails: Show error message and exit
- [ ] If ImageMagick unavailable: Warning but continue
- [ ] If output file already exists: Overwrite with new build

---

### 5. **End-to-End User Workflow Tests**

#### Test 5.1: Complete First-Time Installation (Clean Windows)
- [ ] Start with Windows 10/11 VM with NO Python, Node, or Ollama
- [ ] Download `Dear_Me_1.0.0_Windows.exe`
- [ ] Run installer
- [ ] Follow all prompts
- [ ] When asked for model download:
  - [ ] Test scenario A: User selects "Y" → Wait 20+ minutes for download
  - [ ] Test scenario B: User selects "N" → Skip to testing
- [ ] Complete installation successfully
- [ ] Verify "Dear Me" shortcut appears on Desktop
- [ ] Double-click shortcut
- [ ] Verify browser opens to `http://localhost:3000`
- [ ] Journal app loads
- [ ] Create test account
- [ ] Create test journal entry
- [ ] Close the batch window
- [ ] Verify processes stop cleanly

#### Test 5.2: Daily Use Workflow
- [ ] System has completed first-time installation
- [ ] Close everything
- [ ] Restart Windows to clear all memory
- [ ] Double-click "Dear Me" on Desktop
- [ ] Batch window opens
- [ ] Services start within 30 seconds
- [ ] Browser opens to journal
- [ ] Login and use app
- [ ] Create new entry
- [ ] Close batch window
- [ ] Verify all processes stop

#### Test 5.3: SmartScreen Bypass Workflow
- [ ] Download EXE from GitHub (not local file)
- [ ] Windows Defender SmartScreen may warn
- [ ] If warning appears:
  - [ ] Click on file in browser
  - [ ] "SmartScreen prevented an unrecognized app from starting"
  - [ ] Click "More info"
  - [ ] Click "Run anyway"
  - [ ] Installer proceeds
- [ ] If no warning: Still test manual bypass process

#### Test 5.4: Port Already In Use
- [ ] Start a process on port 8001 (or 3000)
- [ ] Double-click "Dear Me"
- [ ] Verify batch file detects and kills the process
- [ ] Verify Dear Me starts successfully

#### Test 5.5: Ollama Not Available
- [ ] Uninstall Ollama before testing
- [ ] Double-click "Dear Me"
- [ ] Batch script detects Ollama not responding
- [ ] Shows clear error message
- [ ] Instructs user to install from https://ollama.ai
- [ ] Exit with error

#### Test 5.6: Multi-Device Access (WiFi)
- [ ] Start Dear Me on Windows PC (primary device)
- [ ] Look in batch window for: "Phone (same WiFi): http/192.168.x.x:3000"
- [ ] On phone/tablet on same WiFi:
  - [ ] Open browser
  - [ ] Navigate to the IP shown
  - [ ] Verify journal app loads
  - [ ] Verify can create entries from phone

---

### 6. **Performance Tests**

#### Test 6.1: First Installation Time
- [ ] Clean Windows VM
- [ ] Run installer with "N" for model download (skips 20-min model DL)
- [ ] Time from click to "Dear Me ready" message
- [ ] Should be ~15 minutes (includes Python/Node/Ollama/pip install)
- [ ] Record actual time taken

#### Test 6.2: Daily Launch Time
- [ ] Already installed system
- [ ] Click "Dear Me" shortcut
- [ ] Time from click to browser opening
- [ ] Should be ~30 seconds
- [ ] Record actual time taken

#### Test 6.3: Browser Load Time
- [ ] After app opens in browser
- [ ] Time from seeing URL to journal interface interactive
- [ ] Should be < 5 seconds
- [ ] Record actual time

#### Test 6.4: Model Download Time
- [ ] If user downloads model during install
- [ ] Time for ~4.7GB download
- [ ] Should be 15-20 minutes on typical internet
- [ ] Verify download completes without corruption

---

### 7. **Error Scenario Tests**

#### Test 7.1: MSVC Build Tools Missing
- [ ] System without Visual C++ Build Tools
- [ ] Run installer
- [ ] Watch pip install output carefully
- [ ] When chromadb tries to compile:
  - [ ] Verify clear error: "MSBuild.exe not found"
  - [ ] Verify URL provided: Visual C++ Build Tools
  - [ ] User can follow URL and install
  - [ ] Run installer again after installing tools

#### Test 7.2: Network Failure During Installation
- [ ] Disconnect internet during winget install
- [ ] Verify clear error message
- [ ] Can reconnect and try again

#### Test 7.3: Interrupted Installation
- [ ] During pip install, press Ctrl+C
- [ ] Verify script exits cleanly
- [ ] No partial files left behind
- [ ] Can rerun installer successfully

#### Test 7.4: Disk Full During Installation
- [ ] Fill disk to < 500MB available
- [ ] Run installer
- [ ] Verify clear error when disk space insufficient
- [ ] Free up space and try again

#### Test 7.5: Permission Errors
- [ ] Try to install to read-only location
- [ ] Verify clear error message
- [ ] Installer aborts gracefully

---

### 8. **User Experience Tests**

#### Test 8.1: Error Messages Clarity
- [ ] Run installer scenarios that fail
- [ ] Verify each error message is:
  - [ ] Clear and understandable to non-technical user
  - [ ] Provides actionable next steps
  - [ ] Includes URLs for help (if applicable)

#### Test 8.2: Progress Feedback
- [ ] During setup, verify user gets feedback:
  - [ ] Status of Python installation
  - [ ] Status of Node installation
  - [ ] Status of Ollama installation
  - [ ] Status of pip install
  - [ ] Count of progress (e.g., "Installing dependencies (3/5)")

#### Test 8.3: Instructions Clarity
- [ ] Read README_Windows.txt for clarity
- [ ] Follow instructions as non-technical user
- [ ] Verify instructions cover:
  - [ ] What to download
  - [ ] Where to download from
  - [ ] How to run installer
  - [ ] What to do when SmartScreen appears
  - [ ] What to expect during install
  - [ ] How to use daily

#### Test 8.4: Troubleshooting Guide Accuracy
- [ ] Encounter various issues
- [ ] Verify README_Windows.txt troubleshooting section covers them
- [ ] Verify provided solutions actually work

---

## 📊 Test Execution Checklist

### Pre-Testing
- [ ] Read this entire test plan
- [ ] Prepare Windows 10/11 VM or dedicated test machine
- [ ] Ensure internet connectivity
- [ ] Have ~100GB free disk space
- [ ] Test with clean system (no Python/Node/Ollama pre-installed)
- [ ] Test with system that has dependencies (second VM)

### During Testing
- [ ] Record any failures with:
  - [ ] Steps to reproduce
  - [ ] Expected vs actual behavior
  - [ ] Error messages (screenshots helpful)
  - [ ] System specs (Windows version, RAM, internet speed)

### After Testing
- [ ] Summarize results in TEST_RESULTS.md
- [ ] List any bugs found with severity (Critical/High/Medium/Low)
- [ ] Note any improvements for UX
- [ ] Verify fixes and retest

---

## 🎯 Test Success Criteria

✅ **Critical** (Must Pass):
- Installer runs without crashes
- Python/Node/Ollama install successfully
- Backend and frontend start cleanly
- Browser opens to journal app
- Can create and save entries
- Daily launch works in ~30 seconds
- Uninstaller works and preserves database

⚠️ **Important** (Should Pass):
- SmartScreen warning handled gracefully
- Error messages are clear and actionable
- Performance meets expectations
- Multi-device WiFi access works
- Model download works (if attempted)

📝 **Nice to Have** (Can Pass in Future):
- Code signing (no SmartScreen warning)
- Auto-update framework
- Desktop integration improvements

---

## 📝 Reporting Results

Create `TEST_RESULTS.md` with:

```markdown
# Windows Installer Test Results

**Test Date**: [Date]
**Tester**: [Name]
**Windows Version**: [e.g., Windows 11 Build 22621]
**System Specs**: [CPU, RAM, Disk]
**Internet Speed**: [Mbps]

## Results Summary
- Total Tests: [number]
- Passed: [number]
- Failed: [number]
- Blocked: [number]

## Detailed Results
### Test 1.1: Admin Elevation
- Status: ✅ PASS / ❌ FAIL / ⏸️ BLOCKED
- Notes: [any observations]

...

## Bugs Found
1. **[Severity]**: [Description]
   - Steps to reproduce: [...]
   - Expected: [...]
   - Actual: [...]

## Improvements Suggested
- [Improvement 1]
- [Improvement 2]

## Recommendations
[Overall assessment and next steps]
```

---

**End of Test Plan**
