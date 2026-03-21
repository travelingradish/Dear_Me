# Windows Installer - Testing Guide

**Purpose**: Complete testing resources for the Windows installation system

**Status**: 3 testing documents + 1 automated test script provided

---

## 📚 Testing Resources Available

### 1. **TEST_PLAN.md** (This Directory)
- **Type**: Comprehensive manual test plan
- **Size**: ~200 test cases across 8 categories
- **Time Required**: 8-12 hours for full testing
- **Usage**: Reference during manual testing on Windows VM

**What it covers**:
- PowerShell installation script validation
- Batch file launcher validation
- NSIS installer validation
- Build script validation
- End-to-end user workflows
- Performance benchmarks
- Error scenarios
- User experience

### 2. **CODE_REVIEW.md** (This Directory)
- **Type**: Pre-testing code analysis
- **Issues Found**: 18 identified (5 critical, 3 high, 7 medium, 3 low)
- **Usage**: Understand known issues before testing

**What it covers**:
- Code strengths and weaknesses
- 18 potential issues with recommendations
- Testing priorities by severity
- Future improvement suggestions

### 3. **test_installation.ps1** (This Directory)
- **Type**: Automated validation script
- **Size**: ~350 lines of PowerShell
- **Time Required**: 2-3 minutes to run
- **Usage**: Run after installation to validate all components

**What it validates**:
```powershell
powershell -ExecutionPolicy Bypass -File test_installation.ps1

# Or with verbose output:
powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Verbose

# Or for full testing including port checks:
powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Full
```

**Test categories**:
- Installation files exist
- Python environment functional
- Required Python packages installed
- Node.js environment functional
- Ollama installed and accessible
- Shortcuts and registry entries
- Environment variables set
- Database location correct
- Backend connectivity (optional)

---

## 🎯 Quick Testing Checklist

### Before Testing
- [ ] Read CODE_REVIEW.md to understand known issues
- [ ] Prepare Windows 10/11 VM or dedicated test machine
- [ ] Ensure 100GB+ free disk space
- [ ] Document system specs (CPU, RAM, Windows version)
- [ ] Note internet connection speed

### Phase 1: Automated Validation (5 minutes)
```powershell
# After installing Dear Me, run:
cd "$env:LOCALAPPDATA\DearMe\windows"
powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Full

# Check results:
# ✓ All tests pass → Proceed to Phase 2
# ✗ Some tests fail → Review CODE_REVIEW.md for known issues
```

### Phase 2: Manual Critical Tests (30 minutes)
From TEST_PLAN.md, run these high-priority tests:

1. **Test 2.1**: Virtual environment verification
2. **Test 2.2**: Port conflict detection
3. **Test 2.4**: Ollama service check
4. **Test 2.7**: Backend startup
5. **Test 2.9**: Frontend startup
6. **Test 2.11**: Success banner
7. **Test 2.12**: Browser open and journal load
8. **Test 5.1**: Complete first-time installation
9. **Test 5.2**: Daily use workflow

### Phase 3: Edge Cases (1-2 hours, optional)
- Test #3.5: First-time installation with missing Ollama
- Test #3.7: Uninstaller functionality
- Test #5.4: Port already in use
- Test #7.1: MSVC build tools missing
- Test #8.3: Non-technical user instructions

### Phase 4: Performance (30 minutes)
- Test #6.1: First installation time (~15 min expected)
- Test #6.2: Daily launch time (~30 sec expected)
- Test #6.3: Browser load time (< 5 sec expected)

---

## 📋 Test Execution Workflow

### Step 1: Prepare Test Environment

```powershell
# On a Windows 10/11 system (preferably clean VM):
# 1. Note current system state
Get-ComputerInfo | Select WindowsProductName, OsBuildNumber, OsSystemRoot
# 2. Verify internet connection
Test-NetConnection -ComputerName 8.8.8.8 -Port 53
# 3. Check free disk space
Get-Volume | Select DriveLetter, SizeRemaining
```

### Step 2: Run Automated Installation
```powershell
# Download: Dear_Me_1.0.0_Windows.exe
# Run installer
# Follow prompts (test both scenarios):
#   A) User selects "Y" for model download (wait ~20 min)
#   B) User selects "N" to skip model (faster)
```

### Step 3: Run Automated Validation
```powershell
# From windows directory:
powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Full

# Or with verbose output:
powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Verbose

# Capture output:
powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Full | Tee-Object test_results.txt
```

### Step 4: Analyze Results

**If all tests pass** ✓:
1. Proceed to manual testing from TEST_PLAN.md
2. Run critical path tests (Phase 2)
3. Document any observations
4. Try edge cases (Phase 3)

**If some tests fail** ✗:
1. Check CODE_REVIEW.md for known issues
2. Note which tests failed
3. Determine if expected (known issue) or unexpected
4. If unexpected, troubleshoot and report

### Step 5: Test Daily Workflow

```powershell
# Close all services (Ctrl+C in batch window)
# Wait 10 seconds
# Double-click "Dear Me" shortcut
# Time from click to browser appearing (should be ~30 sec)
# Verify journal app loads
# Create test entry
# Close batch window
```

### Step 6: Document Results

Create `TEST_RESULTS.md`:
```markdown
# Test Results - [Date]

## Environment
- Windows Version: [e.g., Windows 11 Build 22621]
- CPU: [e.g., Intel i7-9700K]
- RAM: [e.g., 16GB]
- Free Disk: [e.g., 250GB]
- Internet: [e.g., 100 Mbps]

## Automated Tests
- Passed: [number]/[total]
- Failed: [number]
- Warnings: [number]
- Success Rate: [%]

## Critical Manual Tests
- [Test name]: PASS/FAIL
- [Test name]: PASS/FAIL
- ...

## Issues Found
1. [Description of issue]
   - Severity: Critical/High/Medium/Low
   - Impact: [What breaks?]
   - Workaround: [If any]

## Performance
- First install time: [minutes]
- Daily launch time: [seconds]
- Browser load time: [seconds]

## Recommendations
[Any improvements needed before release]
```

---

## 🔍 Interpreting Test Results

### Automated Test Exit Codes
- **Exit 0**: All critical tests passed ✓
- **Exit 1**: Some tests failed but installation may work ✗
- **Exit 2**: Installation validation failed ✗✗

### Common Failures & Root Causes

| Test Fails | Likely Cause | Fix |
|-----------|--------------|-----|
| Python package not found | Package failed to install silently | Re-run `pip install -r requirements.txt` |
| Python not found | PATH not updated after install | Restart terminal/computer |
| Ollama service not running | Service didn't auto-start | Manually start: Services → Ollama |
| Port 8001 in use | Another app using port | Close other apps using port |
| HF_HOME not set | Environment variable didn't persist | Set manually via System Properties |
| Shortcuts not found | Installer didn't complete | Reinstall |

---

## 📊 Test Coverage Map

### PowerShell Script Coverage
```
install_dependencies.ps1
├── Admin elevation ✓
├── Python installation ✓
├── Node.js installation ✓
├── Ollama installation ✓
├── Virtual environment ✓
├── Pip requirements ✓
├── MSVC error handling ✓
├── Model download ✓
└── Environment variables ✓
```

### Batch File Coverage
```
setup_windows.bat
├── Venv verification ✓
├── Port conflict detection ✓
├── Ollama service check ✓
├── Model verification ✓
├── Backend startup ✓
├── Frontend startup ✓
├── Success banner ✓
├── Browser open ✓
├── Monitor loop ✓
└── Cleanup ✓
```

### NSIS Installer Coverage
```
build_installer.nsi
├── File placement ✓
├── Shortcuts creation ✓
├── Registry entries ✓
├── Prerequisites running ✓
├── Uninstaller ✓
└── Database preservation ✓
```

---

## ⚠️ Known Issues from Code Review

### Critical (Test Carefully)
1. **Path handling**: Test from custom directories
2. **Execution policy**: Verify PowerShell can run
3. **winget fallback**: Test on system without winget
4. **Batch path spaces**: Install to path with spaces
5. **String escaping**: Check environment variables

### High Priority (Watch For)
6. **HTTP timeout**: If services slow, watch for timeout
7. **Model verification**: Broken model should be detected
8. **Ollama service**: Check Windows Services panel

### Medium Priority (Nice to Catch)
9. **Disk space**: Test with < 1GB free
10. **Package verification**: All packages should install
11. **Python PATH**: Should update automatically
12. **Logging**: Check for log files created
13. **Color output**: Verify Unicode displays correctly
14. **Version checking**: Verify minimum versions met
15. **Process cleanup**: Kill old processes properly

---

## 💡 Testing Tips

### Speed Up Testing
- Use Ctrl+C to skip model download (~20 min savings)
- Test edge cases in parallel (multiple VMs)
- Reuse VMs for multiple test runs (snapshot before testing)
- Use `-Full` flag for automated tests to include port checks

### Document Evidence
- Screenshot error messages
- Save batch window output to file
- Record system event logs for troubleshooting
- Screenshot shortcuts and registry entries

### Troubleshooting Tips
- Enable Windows logging: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned`
- Check PowerShell transcript: `$PROFILE`
- Review pip install log: Look for "Collecting" vs "Using cached"
- Monitor Ollama: `ollama list`, `ollama show llama3.1:8b`
- Check environment: `echo %PATH%`, `echo %HF_HOME%`

### VM Best Practices
- Snapshot before testing
- Test multiple Windows versions (10, 11)
- Test multiple architectures (if possible: x64, future ARM)
- Test with different disk sizes
- Test with different internet speeds (if possible)

---

## 📈 Testing Metrics to Track

Track these metrics to measure quality:

| Metric | Target | Actual |
|--------|--------|--------|
| **Installation Success Rate** | 100% | __ |
| **First Launch Success Rate** | 100% | __ |
| **Average Install Time (no model)** | 15 min | __ |
| **Average Daily Launch Time** | 30 sec | __ |
| **Bug Count** | < 5 | __ |
| **Critical Bugs** | 0 | __ |
| **User Documentation Clarity** | 4/5 stars | __ |
| **Installer UX Rating** | 4/5 stars | __ |

---

## 🎓 Learning Resources

If tests fail and you need to debug:

### PowerShell Debugging
```powershell
# Enable strict mode for better error detection
Set-StrictMode -Version Latest

# Enable transcript to log everything
Start-Transcript -Path "C:\Temp\transcript.txt"

# Use verbose output
$VerbosePreference = "Continue"
```

### Batch Debugging
```batch
REM Enable echo to see what's executing
echo on

REM Enable delayed expansion debugging
setlocal enabledelayedexpansion
echo Current variables: %variable%

REM Pause on errors
pause
```

### Checking Logs
```powershell
# Windows Event Viewer
Get-WinEvent -LogName System | Where-Object {$_.Id -eq 1001}

# Application logs
Get-WinEvent -LogName Application | Where-Object {$_.Source -like "*Python*"}

# PowerShell logs
Get-WinEvent -LogName "Windows PowerShell"
```

---

## ✅ Sign-Off Checklist

Before declaring installation ready for release:

### Automated Tests
- [ ] All critical tests pass
- [ ] No unexpected failures
- [ ] Performance meets targets
- [ ] Edge cases handled gracefully

### Manual Tests
- [ ] Installation completes successfully
- [ ] First launch works in ~30 seconds
- [ ] Journal app fully functional
- [ ] Can create and save entries

### Documentation
- [ ] User guide is clear
- [ ] Error messages are helpful
- [ ] SmartScreen bypass documented
- [ ] Troubleshooting covers common issues

### Edge Cases
- [ ] Handles port conflicts
- [ ] Detects missing Ollama
- [ ] Works with custom install paths
- [ ] Survives system restart
- [ ] Uninstall preserves data

### Quality
- [ ] No memory leaks
- [ ] No orphaned processes
- [ ] Clean registry entries
- [ ] Proper cleanup on exit

---

## 🚀 Release Readiness

When ALL of these are complete:
- ✅ CODE_REVIEW.md issues addressed or documented
- ✅ TEST_PLAN.md manual tests completed
- ✅ test_installation.ps1 validates installation
- ✅ Automated tests show 100% pass rate
- ✅ Manual testing shows 100% success
- ✅ Edge cases handled properly
- ✅ Performance meets targets
- ✅ Documentation reviewed by users

**Status**: 🟡 **Ready for Testing** (Pre-Release Phase)

---

**Last Updated**: March 21, 2026
**Testing Framework Version**: 1.0
