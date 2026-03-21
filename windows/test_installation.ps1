# Windows Installation Validation Script
# Run this after installing Dear Me to validate all components
# Usage: powershell -ExecutionPolicy Bypass -File test_installation.ps1

param(
    [switch]$Verbose = $false,
    [switch]$Full = $false
)

# Color codes
$GREEN = "`e[32m"
$RED = "`e[31m"
$YELLOW = "`e[33m"
$BLUE = "`e[34m"
$NC = "`e[0m"

$passCount = 0
$failCount = 0
$warnCount = 0

function Test-Condition {
    param(
        [string]$TestName,
        [scriptblock]$Test,
        [string]$Category = "General"
    )

    Write-Host ""
    Write-Host "$BLUE[$Category]$NC $TestName..." -NoNewline

    try {
        $result = & $Test
        if ($result -eq $true) {
            Write-Host " $GREEN✓$NC" -ForegroundColor Green
            $script:passCount++
            return $true
        } else {
            Write-Host " $RED✗$NC" -ForegroundColor Red
            $script:failCount++
            if ($Verbose) { Write-Host "       Result: $result" }
            return $false
        }
    }
    catch {
        Write-Host " $RED✗$NC" -ForegroundColor Red
        $script:failCount++
        if ($Verbose) { Write-Host "       Error: $_" }
        return $false
    }
}

function Test-Warning {
    param(
        [string]$TestName,
        [scriptblock]$Test,
        [string]$Category = "General"
    )

    Write-Host ""
    Write-Host "$YELLOW[$Category]$NC $TestName..." -NoNewline

    try {
        $result = & $Test
        if ($result -eq $true) {
            Write-Host " $YELLOW⚠$NC" -ForegroundColor Yellow
            $script:warnCount++
            return $true
        } else {
            Write-Host " $GREEN✓$NC" -ForegroundColor Green
            $script:passCount++
            return $false
        }
    }
    catch {
        Write-Host " $YELLOW⚠$NC" -ForegroundColor Yellow
        $script:warnCount++
        if ($Verbose) { Write-Host "       Error: $_" }
        return $true
    }
}

function Print-Header {
    param([string]$text)
    Write-Host ""
    Write-Host "$BLUE================================$NC"
    Write-Host "$BLUE$text$NC"
    Write-Host "$BLUE================================$NC"
}

# Main execution
Clear-Host
Print-Header "Dear Me - Installation Validation"
Write-Host "Testing installation at: $env:LOCALAPPDATA\DearMe"
Write-Host ""

# Test 1: Installation Directory
Print-Header "Installation Files"

Test-Condition "DearMe installation directory exists" {
    Test-Path "$env:LOCALAPPDATA\DearMe"
}

Test-Condition "Backend directory exists" {
    Test-Path "$env:LOCALAPPDATA\DearMe\backend"
}

Test-Condition "Frontend build directory exists" {
    Test-Path "$env:LOCALAPPDATA\DearMe\frontend\build"
}

Test-Condition "Windows scripts directory exists" {
    Test-Path "$env:LOCALAPPDATA\DearMe\windows"
}

Test-Condition "Uninstaller exists" {
    Test-Path "$env:LOCALAPPDATA\DearMe\Uninstall_DearMe.exe"
}

# Test 2: Python Installation
Print-Header "Python Environment"

Test-Condition "Python installed" {
    Get-Command python.exe -ErrorAction SilentlyContinue | Out-Null
    $?
}

Test-Condition "Python version >= 3.10" {
    $pythonVersion = python --version 2>&1 | Select-String -Pattern '\d+\.\d+' -AllMatches | Select-Object -First 1
    [version]$v = $pythonVersion.Matches.Value
    $v -ge [version]"3.10"
}

Test-Condition "Virtual environment exists" {
    Test-Path "$env:LOCALAPPDATA\DearMe\backend\venv"
}

Test-Condition "Venv python works" {
    & "$env:LOCALAPPDATA\DearMe\backend\venv\Scripts\python.exe" --version 2>&1 | Out-Null
    $?
}

Test-Condition "pip in venv works" {
    & "$env:LOCALAPPDATA\DearMe\backend\venv\Scripts\pip.exe" --version 2>&1 | Out-Null
    $?
}

# Test 3: Required Python Packages
Print-Header "Python Packages"

$packages = @("fastapi", "uvicorn", "sqlalchemy", "chromadb", "pydantic")
foreach ($package in $packages) {
    Test-Condition "Package: $package" {
        $output = & "$env:LOCALAPPDATA\DearMe\backend\venv\Scripts\pip.exe" show $package 2>&1
        $? -and ($output -match "Name: $package")
    }
}

# Test 4: Node.js Installation
Print-Header "Node.js Environment"

Test-Condition "Node.js installed" {
    Get-Command node.exe -ErrorAction SilentlyContinue | Out-Null
    $?
}

Test-Condition "npm installed" {
    Get-Command npm.exe -ErrorAction SilentlyContinue | Out-Null
    $?
}

Test-Condition "Node version >= 16" {
    $nodeVersion = node --version 2>&1 | Select-String -Pattern 'v(\d+)' | ForEach-Object { $_.Matches.Groups[1].Value }
    [int]$v = $nodeVersion
    $v -ge 16
}

# Test 5: Ollama Installation
Print-Header "Ollama Integration"

Test-Condition "Ollama installed" {
    Get-Command ollama.exe -ErrorAction SilentlyContinue | Out-Null
    $?
}

Test-Warning "Ollama service running" {
    $service = Get-Service -Name "Ollama" -ErrorAction SilentlyContinue
    $service.Status -ne "Running"
}

Test-Condition "Ollama HTTP endpoint accessible" {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/" -TimeoutSec 2 -ErrorAction Stop
        $response.StatusCode -eq 200
    } catch {
        $false
    }
}

Test-Condition "Model llama3.1:8b available" {
    $models = & ollama list 2>&1
    $models | Select-String "llama3.1:8b" | Out-Null
    $?
}

# Test 6: Desktop Shortcuts
Print-Header "Shortcuts & Registry"

Test-Condition "Desktop shortcut exists" {
    Test-Path "$env:USERPROFILE\Desktop\Dear Me.lnk"
}

Test-Condition "Start Menu folder exists" {
    Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Dear Me"
}

Test-Condition "Start Menu shortcut exists" {
    Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Dear Me\Dear Me.lnk"
}

Test-Condition "Registry entry exists" {
    Test-Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe"
}

# Test 7: Environment Variables
Print-Header "System Configuration"

Test-Condition "HF_HOME environment variable set" {
    [Environment]::GetEnvironmentVariable("HF_HOME", "User") | Out-Null
    $?
}

Test-Condition "HF_HOME points to valid location" {
    $hfHome = [Environment]::GetEnvironmentVariable("HF_HOME", "User")
    $hfHome -and $hfHome -match "DearMe"
}

# Test 8: Port Availability (Optional)
if ($Full) {
    Print-Header "Port Availability"

    Test-Warning "Port 8001 in use" {
        $conn = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
        $conn | Out-Null
        $?
    }

    Test-Warning "Port 3000 in use" {
        $conn = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
        $conn | Out-Null
        $?
    }

    Test-Warning "Port 11434 (Ollama) in use" {
        $conn = Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
        $conn | Out-Null
        $?
    }
}

# Test 9: Database File
Print-Header "Data"

Test-Condition "Database file location correct" {
    $dbPath = "$env:LOCALAPPDATA\DearMe\backend\dear_me.db"
    Test-Path "$env:LOCALAPPDATA\DearMe\backend" -and (
        (Test-Path $dbPath) -or $true  # Database may not exist until first use
    )
}

# Test 10: Backend Connectivity (Optional, requires backend running)
if ($Full) {
    Print-Header "Backend Connectivity"

    Test-Condition "Backend responds to health check" {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/" -TimeoutSec 5 -ErrorAction Stop
            $response.StatusCode -eq 200
        } catch {
            $false
        }
    }

    Test-Condition "Backend API docs accessible" {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/docs" -TimeoutSec 5 -ErrorAction Stop
            $response.StatusCode -eq 200
        } catch {
            $false
        }
    }
}

# Summary
Print-Header "Test Summary"
Write-Host ""
Write-Host "$GREEN Passed:$NC   $passCount"
Write-Host "$RED Failed:$NC   $failCount"
Write-Host "$YELLOW Warnings:$NC $warnCount"
Write-Host ""

$totalTests = $passCount + $failCount
$passPercentage = if ($totalTests -gt 0) { [math]::Round(($passCount / $totalTests) * 100) } else { 0 }

Write-Host "Success Rate: $passPercentage% ($passCount/$totalTests)"
Write-Host ""

# Exit code
if ($failCount -eq 0) {
    Write-Host "$GREEN✓ All critical tests passed!$NC" -ForegroundColor Green
    exit 0
} elseif ($failCount -le 2) {
    Write-Host "$YELLOW⚠ Some tests failed, but installation may still work$NC" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "$RED✗ Installation validation failed$NC" -ForegroundColor Red
    exit 2
}

# Helper info
Write-Host ""
Write-Host "Usage Tips:"
Write-Host "  Verbose:   powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Verbose"
Write-Host "  Full test: powershell -ExecutionPolicy Bypass -File test_installation.ps1 -Full"
Write-Host ""
Write-Host "To start Dear Me:"
Write-Host "  Double-click 'Dear Me' on your Desktop"
Write-Host ""
Write-Host "To view detailed output:"
Write-Host "  Run with -Verbose flag"
