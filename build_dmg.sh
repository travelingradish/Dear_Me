#!/bin/bash
# Build DMG Installer for Dear Me
# Usage: bash build_dmg.sh
# Creates: Dear_Me_1.0.0_macOS.dmg (complete installer with all dependencies bundled)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="$SCRIPT_DIR/dmg_build"
VERSION="1.0.0"
DMG_NAME="Dear_Me_${VERSION}_macOS.dmg"
DMG_VOLUME_NAME="Dear Me"

echo "================================"
echo "🚀 Dear Me DMG Installer Builder"
echo "================================"
echo ""

# Step 1: Clean up old builds
echo "[1/6] Cleaning up old builds..."
rm -rf "$BUILD_DIR" "$SCRIPT_DIR/$DMG_NAME" 2>/dev/null || true
mkdir -p "$BUILD_DIR"
echo "✅ Clean slate ready"

# Step 2: Copy app bundle
echo ""
echo "[2/6] Copying app bundle..."
if [ ! -d "$SCRIPT_DIR/Dear Me.app" ]; then
    echo "⚠️  Dear Me.app not found. Generating..."
    bash "$SCRIPT_DIR/create_app.sh" >/dev/null 2>&1
fi
cp -r "$SCRIPT_DIR/Dear Me.app" "$BUILD_DIR/"
echo "✅ App bundle copied"

# Step 3: Create Applications symlink (for drag-and-drop)
echo ""
echo "[3/6] Setting up drag-and-drop interface..."
ln -s /Applications "$BUILD_DIR/Applications"
echo "✅ Applications folder linked"

# Step 4: Create installer directory and scripts
echo ""
echo "[4/6] Creating installation scripts..."
mkdir -p "$BUILD_DIR/installers"

# Create the main install script
cat > "$BUILD_DIR/install_dependencies.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
# Install Dear Me dependencies (Ollama, Node.js, Python 3.13)
# This script will prompt for your password and install prerequisites

set -e

COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${COLOR_BLUE}================================${NC}"
echo -e "${COLOR_BLUE}📦 Dear Me - Dependencies${NC}"
echo -e "${COLOR_BLUE}================================${NC}"
echo ""

# Check if Homebrew is installed (makes it much easier)
if ! command -v brew >/dev/null 2>&1; then
    echo -e "${COLOR_YELLOW}⚠️  Homebrew not found${NC}"
    echo ""
    echo "For easiest installation, install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo -e "${COLOR_BLUE}Installing prerequisites via Homebrew...${NC}"
echo ""

# Install Ollama
if ! command -v ollama >/dev/null 2>&1; then
    echo -e "${COLOR_BLUE}[1/3]${NC} Installing Ollama..."
    brew install ollama
    echo -e "${COLOR_GREEN}✅ Ollama installed${NC}"
else
    echo -e "${COLOR_GREEN}✅ Ollama already installed${NC}"
fi

# Install Node.js
if ! command -v node >/dev/null 2>&1; then
    echo ""
    echo -e "${COLOR_BLUE}[2/3]${NC} Installing Node.js..."
    brew install node
    echo -e "${COLOR_GREEN}✅ Node.js installed${NC}"
else
    echo -e "${COLOR_GREEN}✅ Node.js already installed${NC}"
fi

# Install Python 3.13
if ! command -v python3.13 >/dev/null 2>&1; then
    echo ""
    echo -e "${COLOR_BLUE}[3/3]${NC} Installing Python 3.13..."
    brew install python@3.13
    echo -e "${COLOR_GREEN}✅ Python 3.13 installed${NC}"
else
    echo -e "${COLOR_GREEN}✅ Python 3.13 already installed${NC}"
fi

echo ""
echo -e "${COLOR_GREEN}================================${NC}"
echo -e "${COLOR_GREEN}✅ All dependencies installed!${NC}"
echo -e "${COLOR_GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo "1. Open Applications folder"
echo "2. Double-click 'Dear Me.app' to launch"
echo ""
echo "Or run this command:"
echo "  open /Applications/Dear\\ Me.app"
echo ""
INSTALL_SCRIPT

chmod +x "$BUILD_DIR/install_dependencies.sh"

# Create quick-start README
cat > "$BUILD_DIR/README.txt" << 'README_TEXT'
╔═══════════════════════════════════════════════════════════╗
║           DEAR ME - AI-Powered Daily Journaling           ║
║              Installation Instructions                    ║
╚═══════════════════════════════════════════════════════════╝

STEP 1: Drag to Applications
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Drag "Dear Me.app" to the "Applications" folder
• This installs the app on your computer

STEP 2: Install Dependencies (First Time Only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Double-click "install_dependencies.sh"
• A Terminal window will open
• Follow the prompts (you may need to enter your password)
• This downloads and installs:
  ✓ Ollama (AI Model Server)
  ✓ Node.js (Frontend)
  ✓ Python 3.13 (Backend)

  This step takes about 5-10 minutes depending on your internet

STEP 3: Launch Dear Me
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Go to Applications folder
• Double-click "Dear Me.app"
• A Terminal window opens and services start
• Your web browser automatically opens to the app
• Click "Allow" if macOS asks for permission

STEP 4: Enjoy!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Start journaling!
• Access from phone on same WiFi: look for the URL in Terminal
• Press Ctrl+C in Terminal to stop the app

FREQUENTLY ASKED QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: "Cannot be opened because the developer cannot be verified"
A: Right-click the app → Click "Open" → Click "Open" again
   (This is normal on first run for apps not on the App Store)

Q: Which web browser will open?
A: Your default browser (usually Safari, Chrome, or Firefox)
   If it doesn't auto-open, go to: http://localhost:3000

Q: Can I access from my iPhone/Android?
A: Yes! Look at the Terminal output for a line like:
   "📱 Phone (same WiFi): http://192.168.x.x:3000"
   Copy that URL into your phone's browser

Q: Do I need to install dependencies every time?
A: No! Only the first time. After that, just launch the app.

Q: How do I stop the app?
A: In the Terminal window, press Ctrl+C
   (Hold Ctrl, then press C)

Q: Can I pin to Dock for quick access?
A: Yes! Right-click Dear Me.app in Applications → Options → Keep in Dock

NEED HELP?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Visit: [Your website/support link here]
Email: [Your email here]

═══════════════════════════════════════════════════════════════
README_TEXT

echo "✅ Installation scripts created"

# Step 5: Create background image for DMG (text-based)
echo ""
echo "[5/6] Creating DMG background image..."

# Create a simple PNG background using Python (if available)
python3 << 'PYTHON_IMAGE'
try:
    from PIL import Image, ImageDraw, ImageFont

    # Create image (600x400, light gray background)
    img = Image.new('RGB', (600, 400), color=(245, 245, 247))
    draw = ImageDraw.Draw(img)

    # Try to use system fonts, fall back to default if not available
    try:
        title_font = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 36)
        text_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Draw text
    draw.text((50, 50), "Dear Me", fill=(52, 152, 219), font=title_font)
    draw.text((50, 100), "AI-Powered Daily Journaling", fill=(127, 140, 141), font=text_font)

    draw.text((50, 160), "Installation Instructions:", fill=(44, 62, 80), font=text_font)
    draw.text((70, 190), "1. Drag \"Dear Me.app\" to Applications", fill=(52, 73, 94))
    draw.text((70, 220), "2. Double-click \"install_dependencies.sh\"", fill=(52, 73, 94))
    draw.text((70, 250), "3. Launch from Applications", fill=(52, 73, 94))
    draw.text((70, 280), "4. Enjoy journaling!", fill=(52, 73, 94))

    # Save image
    img.save('/tmp/dmg_background.png')
    print("✅ Background image created")
except ImportError:
    print("⚠️  PIL not available, using default DMG background")
except Exception as e:
    print(f"⚠️  Could not create background: {e}")
PYTHON_IMAGE

# Copy background if it was created
if [ -f /tmp/dmg_background.png ]; then
    cp /tmp/dmg_background.png "$BUILD_DIR/.background.png"
fi

echo "✅ DMG background prepared"

# Step 6: Create the actual DMG file
echo ""
echo "[6/6] Building DMG installer..."

# Check if create-dmg is available (prettier DMGs)
if command -v create-dmg >/dev/null 2>&1; then
    echo "📦 Using create-dmg for professional layout..."
    create-dmg \
        --volname "$DMG_VOLUME_NAME" \
        --volicon "$SCRIPT_DIR/Dear Me.app/Contents/Info.plist" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "Dear Me.app" 150 190 \
        --icon "Applications" 450 190 \
        --hide-extension "Dear Me.app" \
        --app-drop-link 450 10 \
        "$SCRIPT_DIR/$DMG_NAME" \
        "$BUILD_DIR" 2>/dev/null || true
else
    echo "📦 Using hdiutil (standard macOS tool)..."
    hdiutil create -volname "$DMG_VOLUME_NAME" \
                   -srcfolder "$BUILD_DIR" \
                   -ov -format UDZO \
                   "$SCRIPT_DIR/$DMG_NAME"
fi

# Remove build directory
rm -rf "$BUILD_DIR"

echo "✅ DMG created successfully"
echo ""
echo "================================"
echo "🎉 DMG Installer Ready!"
echo "================================"
echo ""
echo "📍 Location: $SCRIPT_DIR/$DMG_NAME"
echo "📊 Size: $(du -h "$SCRIPT_DIR/$DMG_NAME" | cut -f1)"
echo ""
echo "📝 Distribution Instructions:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Upload $DMG_NAME to your website"
echo "2. Share the download link with users"
echo "3. Users will:"
echo "   • Download the .dmg file"
echo "   • Double-click to open"
echo "   • Follow the installation steps"
echo ""
echo "💡 For notarization (removes Gatekeeper warnings):"
echo "   xcrun notarytool submit $DMG_NAME"
echo "   (Requires Apple Developer account)"
echo ""
