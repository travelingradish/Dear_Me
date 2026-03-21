# Windows Installer - Code Review & Potential Issues

**Date**: March 21, 2026
**Reviewer**: Code Quality Audit
**Status**: Pre-Testing Analysis

---

## ✅ Strengths

### PowerShell Script (`install_dependencies.ps1`)
- ✅ **Self-elevation**: Correctly checks and re-runs as admin
- ✅ **Color output**: Uses ANSI codes for readability
- ✅ **Fallback logic**: Has try-catch blocks for installations
- ✅ **Environment variables**: Properly sets `HF_HOME` for user context
- ✅ **User prompts**: Clear Y/N choice for model download
- ✅ **Error detection**: Catches MSVC build tools error specifically

### Batch File (`setup_windows.bat`)
- ✅ **Delayed expansion**: Uses `SETLOCAL ENABLEDELAYEDEXPANSION` for loop variables
- ✅ **Port detection**: Uses both netstat and PowerShell for reliability
- ✅ **Process killing**: Uses taskkill with window title matching
- ✅ **Exit codes**: Returns proper error codes (exit /b 1 for errors)
- ✅ **Cleanup handler**: Has cleanup label that removes temp files/processes

### NSIS Script (`build_installer.nsi`)
- ✅ **Modular sections**: Clear separation of main install, shortcuts, prerequisites
- ✅ **Registry entries**: Adds app to Add/Remove Programs correctly
- ✅ **Uninstall protection**: Asks user confirmation before uninstall
- ✅ **Database preservation**: Skips deleting dear_me.db

---

## ⚠️ Issues Found & Recommendations

### 🔴 CRITICAL Issues

#### Issue 1: Path Handling in Batch File
**Location**: `setup_windows.bat`, line ~15
```batch
SET "SCRIPT_DIR=%~dp0"
for %%A in ("%SCRIPT_DIR:~0,-1%") do set "APP_DIR=%%~dpA"
```

**Problem**: The path manipulation to remove trailing backslash and go up one level is fragile. If script runs from unexpected locations, this breaks.

**Recommendation**:
```batch
REM Better approach:
SET "SCRIPT_DIR=%~dp0"
REM Windows guarantees ~dp0 includes trailing backslash
REM Navigate up: assume windows/ is one level below project root
for %%D in ("%SCRIPT_DIR:~0,-1%") do set "APP_DIR=%%~dpD"
REM Add comment that APP_DIR should be project root
if not exist "%APP_DIR%backend" (
    echo ERROR: Could not find backend directory
    echo Expected at: %APP_DIR%backend
    exit /b 1
)
```

**Priority**: HIGH - Test this path resolution carefully

---

#### Issue 2: PowerShell Execution Policy Scope
**Location**: `install_dependencies.ps1`, top of script

**Problem**: Script sets execution policy but doesn't verify it was applied:
```powershell
# Current approach assumes -ExecutionPolicy Bypass worked
# But doesn't verify
```

**Recommendation**:
```powershell
# Verify execution policy is set correctly
$currentPolicy = Get-ExecutionPolicy -Scope Process
if ($currentPolicy -eq "Restricted") {
    Write-Host "ERROR: Could not change execution policy"
    exit 1
}
```

**Priority**: MEDIUM - Graceful failure instead of silent failure

---

#### Issue 3: winget Fallback Not Implemented
**Location**: `install_dependencies.ps1`, winget install commands

**Problem**: Script uses `winget install` but if winget fails, no fallback to direct download:
```powershell
winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements -e --silent 2>$null
# No fallback if this fails!
```

**Recommendation**:
```powershell
try {
    winget install Python.Python.3.13 --accept-source-agreements ... 2>$null
} catch {
    Write-Warning "winget failed, trying alternative: download from python.org"
    # Implement direct .exe download or provide clear URL
}
```

**Priority**: MEDIUM - Improves reliability on systems without winget

---

#### Issue 4: Batch File Path Spaces
**Location**: `setup_windows.bat`, multiple locations

**Problem**: Paths with spaces might not be handled correctly:
```batch
cd /d "%APP_DIR%backend"  # Correct usage with quotes
start "DearMe-Backend" /MIN cmd /c "%VENV_PYTHON% main.py"  # Potential issue
```

**Recommendation**: All paths should be in quotes consistently:
```batch
start "DearMe-Backend" /MIN cmd /c "%VENV_PYTHON:~0% main.py"
REM Or better:
start "DearMe-Backend" /MIN cmd /c ^
  "^"%VENV_PYTHON%^" main.py"
```

**Priority**: MEDIUM - Could break on custom install paths with spaces

---

#### Issue 5: PowerShell String Escaping
**Location**: `install_dependencies.ps1`, path strings

**Problem**: `HF_HOME` path might have issues with spaces or special chars:
```powershell
$modelCachePath = Join-Path $env:LOCALAPPDATA "DearMe\model_cache"
[Environment]::SetEnvironmentVariable("HF_HOME", $modelCachePath, "User")
# What if $env:LOCALAPPDATA contains spaces? (unlikely but possible)
```

**Recommendation**:
```powershell
# Ensure double quotes around all path values
[Environment]::SetEnvironmentVariable("HF_HOME", "`"$modelCachePath`"", "User")
# Verify it was set
$verifyPath = [Environment]::GetEnvironmentVariable("HF_HOME", "User")
if ($verifyPath -ne $modelCachePath) {
    Write-Warning "HF_HOME may not have been set correctly"
}
```

**Priority**: LOW - Edge case

---

### 🟡 HIGH Priority Issues

#### Issue 6: No Timeout on HTTP Polling
**Location**: `setup_windows.bat`, polling loops

**Problem**: While loops poll without time limits. If service is very slow, script waits indefinitely:
```batch
for /l %%A in (1,1,60) do (
    REM Polls up to 60 times × 1 second = 60 seconds max
    REM But if backend hangs, this is still slow
)
```

**Better approach**: Add timeout variable that users can modify:
```batch
set "BACKEND_TIMEOUT=60"
set "BACKEND_TRIES=0"
for /l %%A in (1,1,%BACKEND_TIMEOUT%) do (
    if !BACKEND_TRIES! geq %BACKEND_TIMEOUT% (
        echo Backend took too long to start
        goto TIMEOUT_ERROR
    )
    set /a "BACKEND_TRIES+=1"
)
```

**Priority**: MEDIUM - Affects user experience if backend slow

---

#### Issue 7: Model Download Verification Missing
**Location**: `setup_windows.bat`, section [3/5]

**Problem**: Script checks if model exists with PowerShell but doesn't verify model is functional:
```powershell
$models = & ollama list
if ($models | Select-String 'llama3.1:8b') { exit 0 }
# This checks if model is LISTED, not if it WORKS
```

**Recommendation**:
```powershell
try {
    # Try to actually use the model
    $response = & ollama generate --model llama3.1:8b "test" 2>&1
    if ($response -match "error") {
        exit 1  # Model listed but broken
    }
} catch {
    exit 1  # Model not usable
}
```

**Priority**: MEDIUM - Could proceed with broken model

---

#### Issue 8: Ollama Service Status Not Checked
**Location**: `install_dependencies.ps1`, Ollama startup

**Problem**: Script waits for HTTP endpoint but doesn't check Windows service status:
```powershell
# Tries HTTP endpoint but what if service crashed?
# Service could be hung, not responding
```

**Recommendation**:
```powershell
# Check service status on Windows
$ollamaService = Get-Service -Name "Ollama" -ErrorAction SilentlyContinue
if ($ollamaService -and $ollamaService.Status -ne "Running") {
    try {
        Start-Service -Name "Ollama"
        Write-Host "Started Ollama service"
    } catch {
        Write-Warning "Could not start Ollama service"
    }
}
```

**Priority**: HIGH - Improves debugging if service issues

---

#### Issue 9: No Disk Space Check
**Location**: Both scripts

**Problem**: Scripts don't verify sufficient disk space before installing:
- Python: ~200 MB
- Node: ~500 MB
- Ollama: varies but service takes space
- Model: ~4.7 GB
- **Total**: ~6 GB needed

**Recommendation**:
```powershell
# In install_dependencies.ps1
$driveLetter = $env:SYSTEMDRIVE
$drive = Get-Volume -DriveLetter $driveLetter[0]
$freeGB = $drive.SizeRemaining / 1GB
if ($freeGB -lt 7) {
    Write-Error "Insufficient disk space. Need 7GB, have ${freeGB}GB"
    exit 1
}
```

**Priority**: MEDIUM - Prevents partial installations

---

### 🟠 MEDIUM Priority Issues

#### Issue 10: No Verification of Installation Success
**Location**: `install_dependencies.ps1`

**Problem**: After `pip install -r requirements.txt`, script doesn't verify all packages installed:
```powershell
& "$venvDir\Scripts\pip.exe" install -r "$backendDir\requirements.txt" 2>&1
# What if 5/26 packages failed silently?
```

**Recommendation**:
```powershell
$pipOutput = & "$venvDir\Scripts\pip.exe" install -r "$backendDir\requirements.txt" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed with exit code $LASTEXITCODE"
    exit 1
}
# Verify critical packages
$packages = @("fastapi", "chromadb", "sentence-transformers")
foreach ($package in $packages) {
    & "$venvDir\Scripts\pip.exe" show $package > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Critical package $package not installed"
        exit 1
    }
}
```

**Priority**: MEDIUM - Silent failures could cause runtime issues

---

#### Issue 11: Python PATH Not Refreshed
**Location**: `install_dependencies.ps1`, after Python install

**Problem**: After winget installs Python, PATH may not be updated in current session:
```powershell
$env:PATH = "C:\Users\...\Python313;" + $env:PATH
# This only affects current PowerShell session
# Next process won't have updated PATH
```

**Recommendation**:
```powershell
# Verify Python is in PATH
$pythonPath = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Warning "Python not in PATH, adding manually..."
    $env:PATH = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313;" + $env:PATH

    # Re-verify
    $pythonPath = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $pythonPath) {
        throw "Python still not found in PATH"
    }
}
```

**Priority**: MEDIUM - Could cause "python.exe not found" errors later

---

#### Issue 12: No Logging to File
**Location**: Both scripts

**Problem**: Complex installation can fail, but no log file captures what happened:
- User can't easily debug
- No record of what was attempted

**Recommendation**:
```powershell
# In install_dependencies.ps1
$logPath = Join-Path $env:TEMP "DearMe_Install_$(Get-Date -Format yyyyMMdd_HHmmss).log"
Start-Transcript -Path $logPath

# ... all script execution gets logged ...

Stop-Transcript
Write-Host "Installation log saved to: $logPath"
```

**Priority**: MEDIUM - Helps with troubleshooting

---

#### Issue 13: Batch File Color Output Limits
**Location**: `setup_windows.bat`

**Problem**: Batch file uses Unicode characters (✓, ✗) which may not display correctly on all Windows terminals:
```batch
set "CHECK=✓"
set "ERROR=✗"
```

**Recommendation**:
```batch
REM Use ASCII-only characters for better compatibility
set "CHECK=[OK]"
set "ERROR=[FAIL]"
REM Or detect terminal capabilities
for /f "tokens=*" %%A in ('powershell -Command "$([console]::OutputEncoding.WebName)"') do set "ENCODING=%%A"
```

**Priority**: LOW - Usually works, but edge case on older systems

---

#### Issue 14: No Version Checking
**Location**: Both scripts

**Problem**: Scripts install latest version of tools, but don't check minimum versions:
- Python: Assumes 3.13 correct version
- Node: Assumes latest LTS
- Ollama: No version verification

**Recommendation**:
```powershell
$pythonVersion = [version](python --version 2>&1 | Select-Object -Last 1 | % { $_ -replace '[^\d.]' })
if ($pythonVersion -lt [version]"3.10") {
    Write-Error "Python 3.10+ required, got $pythonVersion"
    exit 1
}
```

**Priority**: LOW - Good for edge cases

---

#### Issue 15: Backend/Frontend Process Cleanup Race Condition
**Location**: `setup_windows.bat`, cleanup label

**Problem**: Cleanup tries to kill processes but race condition if they're exiting:
```batch
taskkill /FI "WINDOWTITLE eq DearMe-Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq DearMe-Frontend" /F >nul 2>&1
```

**Recommendation**:
```batch
REM Kill with retry logic
for /l %%i in (1,1,3) do (
    taskkill /FI "WINDOWTITLE eq DearMe-Backend" /F >nul 2>&1
    if !errorlevel! equ 0 goto BACKEND_KILLED
    timeout /t 1 /nobreak >nul
)
:BACKEND_KILLED
REM ... repeat for frontend ...
```

**Priority**: LOW - Minor issue, cleanup usually works

---

### 🟢 LOW Priority Issues

#### Issue 16: Inconsistent Error Messages
**Location**: Multiple locations across scripts

**Problem**: Some errors use "✗" character, some use "ERROR:", some are silent

**Recommendation**: Standardize on consistent format:
```powershell
function Print-Error { param([string]$msg)
    Write-Host "❌ ERROR: $msg" -ForegroundColor Red
}

function Print-Success { param([string]$msg)
    Write-Host "✅ SUCCESS: $msg" -ForegroundColor Green
}

function Print-Warning { param([string]$msg)
    Write-Host "⚠️ WARNING: $msg" -ForegroundColor Yellow
}
```

**Priority**: LOW - Nice to have, not critical

---

#### Issue 17: No Input Validation
**Location**: `build_installer.ps1`, app version parameter

**Problem**: Version parameter has no validation:
```powershell
param([string]$Version = "1.0.0")
# What if user passes invalid version like "1.0.0.0.0"?
```

**Recommendation**:
```powershell
param([string]$Version = "1.0.0")
if (-not ($Version -match '^\d+\.\d+\.\d+$')) {
    throw "Invalid version format: $Version (expected X.Y.Z)"
}
```

**Priority**: LOW - Dev-only script

---

#### Issue 18: Frontend Build Cache
**Location**: `build_installer.ps1`

**Problem**: If frontend build fails midway, residual files might cause issues on retry:
```powershell
npm run build --silent
# If this fails halfway, old files still exist
```

**Recommendation**:
```powershell
# Clean before building
if (Test-Path "$frontendDir\build") {
    Remove-Item "$frontendDir\build" -Recurse -Force
}
npm run build --silent
```

**Priority**: LOW - Edge case

---

## 📋 Summary of Issues by Severity

### 🔴 CRITICAL (5)
1. ✅ Path handling in batch file
2. ✅ Execution policy verification
3. ✅ winget fallback
4. ✅ Batch path spaces
5. ✅ PowerShell string escaping

### 🟡 HIGH (3)
6. ✅ HTTP polling timeout
7. ✅ Model download verification
8. ✅ Ollama service status check

### 🟠 MEDIUM (7)
9. ✅ Disk space check
10. ✅ Installation success verification
11. ✅ Python PATH refresh
12. ✅ Logging to file
13. ✅ Batch file color output
14. ✅ Version checking
15. ✅ Process cleanup race condition

### 🟢 LOW (3)
16. ✅ Error message consistency
17. ✅ Input validation
18. ✅ Frontend build cache

---

## 🎯 Testing Priorities

**Before Release, MUST test:**
- [ ] Issue #1 (Path handling) - Run from different directories
- [ ] Issue #2 (Exec policy) - Monitor output carefully
- [ ] Issue #3 (winget fallback) - Test on system without winget
- [ ] Issue #4 (Path spaces) - Install to custom path with spaces
- [ ] Issue #8 (Ollama service) - Monitor Windows services during run
- [ ] Issue #10 (Package verification) - Check all critical packages install

**Should test, affects UX:**
- [ ] Issue #6 (Timeout) - Intentionally slow backend, watch timeout
- [ ] Issue #7 (Model verification) - Test with corrupted model
- [ ] Issue #9 (Disk space) - Test on system with < 1GB free

**Nice to have:**
- [ ] Issue #12 (Logging) - Check logs for debugging
- [ ] Issue #16 (Error consistency) - Review all error output

---

## ✅ Recommendations for Future Versions

1. **Unit tests**: Create `.ps1` unit tests using Pester framework
2. **CI/CD**: GitHub Actions to build and test on Windows runners
3. **Signed code**: Code sign PowerShell scripts to avoid execution policy issues
4. **Installer customization**: Allow custom install paths, Python versions, etc.
5. **Auto-update**: Add framework for automatic updates (Sparkle equivalent)
6. **Analytics**: Telemetry to track install success rates and failure points
7. **Rollback**: Create automatic rollback if installation fails

---

**End of Code Review**
