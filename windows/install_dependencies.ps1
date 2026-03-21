# Dear Me - First-Time Installer (Windows)
# This script installs all prerequisites and prepares the environment
# Run with: powershell -ExecutionPolicy Bypass -File install_dependencies.ps1

# Color codes for output
$BLUE = "`e[34m"
$GREEN = "`e[32m"
$RED = "`e[31m"
$YELLOW = "`e[33m"
$NC = "`e[0m"

function Print-Header {
    param([string]$text)
    Write-Host ""
    Write-Host "$BLUE================================$NC" -NoNewline
    Write-Host ""
    Write-Host "$BLUE$text$NC" -NoNewline
    Write-Host ""
    Write-Host "$BLUE================================$NC" -NoNewline
    Write-Host ""
    Write-Host ""
}

function Print-Step {
    param([string]$step, [string]$text)
    Write-Host "$BLUE[$step]$NC $text"
}

function Print-Success {
    param([string]$text)
    Write-Host "$GREEN✅ $text$NC"
}

function Print-Warning {
    param([string]$text)
    Write-Host "$YELLOW⚠️  $text$NC"
}

function Print-Error {
    param([string]$text)
    Write-Host "$RED❌ $text$NC"
}

# Self-elevate to Administrator if not already elevated
function Ensure-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)

    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Print-Warning "This script needs Administrator privileges to install software"

        # Re-run as Administrator
        $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
        Start-Process powershell -ArgumentList $arguments -Verb RunAs
        exit
    }
}

# Main script start
Ensure-Admin

Print-Header "🌟 Dear Me - First-Time Installer"

# Step 1: Check prerequisites
Print-Step "[1/5]" "Checking prerequisites..."

$missingTools = @()

# Check Python
if (-not (Get-Command python.exe -ErrorAction SilentlyContinue)) {
    $missingTools += "Python 3.13"
} else {
    Print-Success "Python found"
}

# Check Node.js
if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
    $missingTools += "Node.js LTS"
} else {
    Print-Success "Node.js found"
}

# Check Ollama
if (-not (Get-Command ollama.exe -ErrorAction SilentlyContinue)) {
    $missingTools += "Ollama"
} else {
    Print-Success "Ollama found"
}

# Step 2: Install missing tools via winget
if ($missingTools.Count -gt 0) {
    Print-Warning "Installing missing tools: $($missingTools -join ', ')"

    if ($missingTools -contains "Python 3.13") {
        Print-Step "[2/5]" "Installing Python 3.13..."

        try {
            # Try winget first
            winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements -e --silent 2>$null

            # Verify installation
            $pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe"
            if (-not (Test-Path $pythonPath)) {
                throw "Python installation verification failed"
            }

            # Add Python to PATH for this session
            $env:PATH = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313;" + $env:PATH
            Print-Success "Python 3.13 installed"
        }
        catch {
            Print-Error "Failed to install Python via winget"
            Print-Warning "Please download from https://www.python.org/downloads/ and install manually"
            Print-Warning "Important: Check 'Add Python to PATH' during installation"
            exit 1
        }
    }

    if ($missingTools -contains "Node.js LTS") {
        Print-Step "[2/5]" "Installing Node.js LTS..."

        try {
            winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements -e --silent 2>$null
            Print-Success "Node.js LTS installed"
        }
        catch {
            Print-Error "Failed to install Node.js via winget"
            Print-Warning "Please download from https://nodejs.org/ and install manually"
            exit 1
        }
    }

    if ($missingTools -contains "Ollama") {
        Print-Step "[2/5]" "Installing Ollama..."

        try {
            winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements -e --silent 2>$null
            Print-Success "Ollama installed"
        }
        catch {
            Print-Error "Failed to install Ollama via winget"
            Print-Warning "Please download from https://ollama.ai and install manually"
            exit 1
        }
    }
} else {
    Print-Step "[2/5]" "All tools already installed"
}

# Step 3: Wait for Ollama service to start
Print-Step "[3/5]" "Waiting for Ollama service..."

$maxAttempts = 20
$attempts = 0
$ollamaReady = $false

while ($attempts -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $ollamaReady = $true
        break
    }
    catch {
        $attempts++
        if ($attempts % 5 -eq 0) {
            Write-Host "." -NoNewline
        }
        Start-Sleep -Seconds 2
    }
}

if ($ollamaReady) {
    Print-Success "Ollama service is running"
} else {
    Print-Warning "Ollama service not responding - it may be running in background"
}

# Step 4: Set up Python virtual environment
Print-Step "[4/5]" "Setting up Python environment..."

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Split-Path -Parent $scriptDir
$backendDir = Join-Path $appDir "backend"
$venvDir = Join-Path $backendDir "venv"

if (-not (Test-Path $venvDir)) {
    Print-Warning "Creating virtual environment (this may take a minute)..."

    try {
        Set-Location $backendDir
        python.exe -m venv venv
        Print-Success "Virtual environment created"
    }
    catch {
        Print-Error "Failed to create virtual environment"
        exit 1
    }
}

# Upgrade pip
Print-Warning "Upgrading pip (this may take a minute)..."
& "$venvDir\Scripts\pip.exe" install --upgrade pip --quiet 2>&1 | Where-Object { $_ -notmatch "already satisfied" } | Out-Null

# Install requirements
Print-Warning "Installing Python dependencies (this may take a few minutes)..."
$pipOutput = & "$venvDir\Scripts\pip.exe" install -r "$backendDir\requirements.txt" 2>&1

# Check for MSVC build tools error
if ($pipOutput -match "error: Microsoft Visual C\+\+ 14\.0 or greater is required" -or `
    $pipOutput -match "error: \"MSBuild\.exe\" not found") {

    Print-Error "Missing C++ build tools required by chromadb"
    Print-Warning "Please install: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    Print-Warning "After installation, run this script again"
    exit 1
} else {
    Print-Success "Python dependencies installed"
}

# Set HF_HOME environment variable
Print-Step "[5/5]" "Configuring model cache..."

$modelCachePath = Join-Path $env:LOCALAPPDATA "DearMe\model_cache"
[Environment]::SetEnvironmentVariable("HF_HOME", $modelCachePath, "User")
$env:HF_HOME = $modelCachePath

Print-Success "Model cache configured at $modelCachePath"

# Ask about downloading model
Print-Warning ""
Print-Warning "The AI model (llama3.1:8b) is ~4.7GB and takes 15-20 minutes to download."
Print-Warning ""

$response = Read-Host "Download AI model now? (Y/n)"

if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
    Print-Step "[Model]" "Downloading llama3.1:8b model..."
    Print-Warning "(This will take 15-20 minutes and requires a stable internet connection)"
    Print-Warning ""

    try {
        ollama.exe pull llama3.1:8b
        Print-Success "Model downloaded successfully"
    }
    catch {
        Print-Error "Model download failed"
        Print-Warning "You can download it manually later by running: ollama pull llama3.1:8b"
    }
} else {
    Print-Warning "Model download skipped"
    Print-Warning "You can download it later by running: ollama pull llama3.1:8b"
}

# Final success message
Write-Host ""
Write-Host "$GREEN================================$NC"
Write-Host "$GREEN🎉 Installation Complete!$NC"
Write-Host "$GREEN================================$NC"
Write-Host ""
Write-Host "You can now launch Dear Me by:"
Write-Host "  1. Double-clicking 'Dear Me' on your Desktop"
Write-Host "  2. Or running: cd backend && ..\windows\setup_windows.bat"
Write-Host ""
Write-Host "On first launch, all services will start automatically (~30 seconds)"
Write-Host ""

Read-Host "Press Enter to exit"
