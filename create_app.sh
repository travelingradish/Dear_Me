#!/bin/bash
# Create a macOS .app bundle for Dear Me
# Run this once: bash create_app.sh
# Then move Dear Me.app to ~/Applications or keep it here

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR/Dear Me.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"

echo "🚀 Creating Dear Me.app..."

# Create directory structure
mkdir -p "$MACOS_DIR"

# Create the launch script (executable)
cat > "$MACOS_DIR/launch" << 'EOF'
#!/bin/bash
# Opens Terminal.app with the Dear Me.command script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMAND_FILE="$SCRIPT_DIR/../../../Dear Me.command"
open -a Terminal "$COMMAND_FILE"
EOF

chmod +x "$MACOS_DIR/launch"

# Create Info.plist (macOS bundle metadata)
cat > "$CONTENTS_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIdentifier</key>
    <string>com.dearme.launcher</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Dear Me</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Dear Me - AI-Powered Daily Journaling</string>
</dict>
</plist>
EOF

# Create PkgInfo file (optional but helps macOS recognize the app)
echo -n "APPL????" > "$CONTENTS_DIR/PkgInfo"

# Remove quarantine attribute if Gatekeeper applied it
xattr -d com.apple.quarantine "$APP_DIR" 2>/dev/null || true

echo ""
echo "✅ Dear Me.app created successfully!"
echo ""
echo "Next steps:"
echo "1. Move Dear Me.app to ~/Applications:"
echo "   mv \"$APP_DIR\" ~/Applications/"
echo ""
echo "2. (Optional) Add to Dock: drag Dear Me.app to your Dock"
echo ""
echo "3. Single-click to launch - or:"
echo "   open \"$APP_DIR\""
echo ""
echo "Note: On first run, you may see a Gatekeeper security warning."
echo "      Right-click the app and select 'Open' to bypass it."
echo ""
