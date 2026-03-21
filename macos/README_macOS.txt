================================================================================
                    DEAR ME - macOS Installation Guide
================================================================================

Thank you for downloading Dear Me! This guide will help you get started.

================================================================================
                              FIRST TIME SETUP
================================================================================

1. MOUNT THE DMG FILE
   - Double-click "Dear_Me_1.0.0_macOS.dmg" in your Downloads folder
   - A Finder window appears showing "Dear Me.app" and "Applications" folder

2. INSTALL THE APP
   - Drag "Dear Me.app" to the "Applications" folder
   - Wait for copy to complete (~30 seconds)
   - Close the Finder window when done

3. RUN THE INSTALLER (First Time Only)
   - Open the DMG again (it's still mounted)
   - Double-click "install_dependencies.sh"
   - A Terminal window opens and installs:
     • Homebrew (if needed)
     • Python 3.13
     • Node.js
     • Ollama
     • Python dependencies
   - This takes about 10-15 minutes
   - The Terminal window will show "Installation Complete!"

4. CREATE YOUR ACCOUNT
   - Open Applications folder
   - Double-click "Dear Me"
   - Your browser opens to http://localhost:3000
   - Create username/password (no email required!)
   - Name your AI companion
   - Start journaling!

================================================================================
                          SYSTEM REQUIREMENTS
================================================================================

• macOS 10.13 (High Sierra) or newer
• At least 5 GB free disk space
• Internet connection for initial setup and model download

================================================================================
                         DOWNLOADING THE AI MODEL
================================================================================

The AI model is ~4.7GB and takes 15-20 minutes to download.

If you skipped the model download during installation:

1. Open Terminal (Cmd + Space, type "terminal", press Enter)
2. Run: ollama pull llama3.1:8b
3. Wait for download to complete
4. Launch Dear Me - it will now work!

================================================================================
                          DAILY USE (AFTER SETUP)
================================================================================

Every time you want to use Dear Me:

1. Open Applications folder
2. Double-click "Dear Me"
3. Wait ~2-3 minutes for services to start
4. Your browser opens to http://localhost:3000
5. Close the Terminal window when done

Optional: Create a Desktop shortcut for faster access:
   - Open macos/ folder inside the DMG
   - Drag "Dear Me.command" to your Desktop
   - Next time, just double-click the Desktop shortcut!

================================================================================
                         ACCESSING FROM YOUR PHONE
================================================================================

To access Dear Me from another device on the same WiFi:

1. Look for this line in the Terminal window:
   "Phone (same WiFi): http/192.168.x.x:3000"

2. Open that URL in your phone's browser

Note: This only works if both devices are on the same WiFi network.

================================================================================
                              HOW TO STOP
================================================================================

To stop Dear Me:
   1. Close the Terminal window, OR
   2. Press Ctrl+C in the Terminal window

Your journal entries are automatically saved - no data loss when you stop.

================================================================================
                            TROUBLESHOOTING
================================================================================

"Cannot open Dear Me.app"
  - Right-click the app → Open → Open (bypasses Gatekeeper)
  - This appears because the app isn't signed with an Apple cert

"Homebrew installation failed"
  - Ensure you have a stable internet connection
  - Run manually: /bin/bash -c "$(curl -fsSL ...)"
  - Visit https://brew.sh for details

"Port 8001 or 3000 already in use"
  - Another application is using these ports
  - Close other applications that use these ports
  - Or restart your Mac

"npm not found" or "Node not installed"
  - Run the installer script again:
    - Double-click "install_dependencies.sh" from the DMG

"Model download failed"
  - Check your internet connection
  - Try again later: ollama pull llama3.1:8b

For more help, visit: https://github.com/travelingradish/Dear_Me/issues

================================================================================
                            UNINSTALLING
================================================================================

To uninstall Dear Me:

1. Drag "Dear Me.app" from Applications to Trash
2. Empty Trash
3. Optional: Remove dependencies (Homebrew packages stay installed)

Your journal entries are preserved in:
   ~/projects/dear_me/backend/dear_me.db
   (or wherever you cloned the project)

================================================================================
                         PRIVACY & YOUR JOURNAL
================================================================================

Dear Me is designed for your privacy:
  - Your journal entries stay on your computer
  - The AI model runs locally (no cloud connection)
  - No data is sent to external servers
  - You control all your personal information

================================================================================

Enjoy Dear Me! 🌟
Be here, be now, be you.

================================================================================
