# Dear Me - Windows Installer Builder
# Builds the NSIS .exe installer from source files
# Usage: powershell -ExecutionPolicy Bypass -File build_installer.ps1

param(
    [string]$Version = "1.0.0",
    [switch]$BuildFrontend = $false
)

# Color codes
$GREEN = "`e[32m"
$RED = "`e[31m"
$YELLOW = "`e[33m"
$NC = "`e[0m"

function Print-Success {
    param([string]$text)
    Write-Host "$GREEN✅ $text$NC"
}

function Print-Error {
    param([string]$text)
    Write-Host "$RED❌ $text$NC"
}

function Print-Warning {
    param([string]$text)
    Write-Host "$YELLOW⚠️  $text$NC"
}

function Print-Header {
    param([string]$text)
    Write-Host ""
    Write-Host "$YELLOW================================$NC"
    Write-Host "$YELLOW$text$NC"
    Write-Host "$YELLOW================================$NC"
    Write-Host ""
}

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "frontend"
$frontendBuildDir = Join-Path $frontendDir "build"

Print-Header "🔨 Dear Me - Windows Installer Builder"

Write-Host "Version: $Version"
Write-Host "Project Root: $projectRoot"
Write-Host ""

# Step 1: Check if NSIS is installed
Write-Host "[1/4] Checking for NSIS..."

$nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
$nsisPath32 = "C:\Program Files\NSIS\makensis.exe"

if (Test-Path $nsisPath) {
    Print-Success "NSIS found at $nsisPath"
    $makensis = $nsisPath
} elseif (Test-Path $nsisPath32) {
    Print-Success "NSIS found at $nsisPath32"
    $makensis = $nsisPath32
} elseif (Get-Command makensis -ErrorAction SilentlyContinue) {
    Print-Success "NSIS found in PATH"
    $makensis = "makensis"
} else {
    Print-Error "NSIS not found!"
    Print-Warning "Install NSIS from: https://nsis.sourceforge.io/Download"
    Print-Warning "Or install via: winget install NSIS.NSIS"
    exit 1
}

# Step 2: Check/build frontend
Write-Host "[2/4] Checking frontend build..."

if ($BuildFrontend -or -not (Test-Path $frontendBuildDir)) {
    Print-Warning "Building frontend..."

    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Print-Warning "Installing frontend dependencies..."
        Set-Location $frontendDir

        try {
            npm ci --silent
            if ($LASTEXITCODE -ne 0) {
                Print-Error "npm ci failed"
                exit 1
            }
        }
        catch {
            Print-Error "Failed to run npm ci"
            exit 1
        }
    }

    Print-Warning "Running npm build (this may take 2-3 minutes)..."
    $env:GENERATE_SOURCEMAP = "false"

    try {
        npm run build --silent
        if ($LASTEXITCODE -ne 0) {
            Print-Error "npm run build failed"
            exit 1
        }
    }
    catch {
        Print-Error "Failed to run npm build"
        exit 1
    }

    Print-Success "Frontend built successfully"
} else {
    Print-Success "Frontend build already exists"
}

# Step 3: Create icon (optional)
Write-Host "[3/4] Checking for icon..."

$iconPath = Join-Path $scriptDir "assets\dear_me.ico"

if (-not (Test-Path $iconPath)) {
    Print-Warning "Icon not found at $iconPath"
    Print-Warning "You can create it using ImageMagick:"
    Print-Warning "  magick convert $frontendDir\public\logo192.png -define icon:auto-resize=""256,48,32,16"" $iconPath"
    Print-Warning ""
    Print-Warning "For now, the installer will use default Windows icon"
} else {
    Print-Success "Icon found"
}

# Step 4: Build installer
Write-Host "[4/4] Building NSIS installer..."

$outputFile = Join-Path $projectRoot "Dear_Me_${Version}_Windows.exe"

try {
    Set-Location $scriptDir

    # Run makensis with version define
    & $makensis "/DAPP_VERSION=$Version" "build_installer.nsi"

    if ($LASTEXITCODE -ne 0) {
        Print-Error "NSIS build failed"
        exit 1
    }

    # Verify output file
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length / 1MB
        Print-Success "Installer created: $outputFile (${fileSize:F1} MB)"
    } else {
        Print-Error "Installer file not created"
        exit 1
    }
}
catch {
    Print-Error "Build failed: $_"
    exit 1
}

# Summary
Write-Host ""
Print-Header "✨ Build Complete!"

Write-Host "Output file: $outputFile"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Test on a Windows VM or local machine"
Write-Host "  2. Users will see SmartScreen warning (unsigned exe)"
Write-Host "  3. They should click 'More info' → 'Run anyway'"
Write-Host ""
Write-Host "To sign the executable (optional):"
Write-Host "  signtool sign /f <certificate.pfx> /p <password> /t http://timestamp.comodoca.com/authenticode $outputFile"
Write-Host ""
