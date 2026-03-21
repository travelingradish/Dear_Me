================================================================================
                     DEAR ME - Windows Installation Guide
================================================================================

Thank you for downloading Dear Me! This guide will help you get started.

================================================================================
                              FIRST TIME SETUP
================================================================================

1. RUN THE INSTALLER
   - The installer will automatically install Python, Node.js, and Ollama
   - This takes about 10-15 minutes on first run
   - After installation, you'll see a "Dear Me" shortcut on your Desktop

2. LAUNCH THE APP
   - Double-click the "Dear Me" shortcut on your Desktop
   - A command window will appear (this is normal - don't close it)
   - The app will open in your web browser automatically
   - First launch takes ~30 seconds

3. CREATE YOUR ACCOUNT
   - Username and password (no email required!)
   - Name your AI companion for a personal touch
   - Start journaling!

================================================================================
                           WINDOWS SMARTSCREEN WARNING
================================================================================

You may see a security warning: "Windows protected your PC"

This is normal for unsigned applications. To continue:
  1. Click "More info"
  2. Click "Run anyway"

This warning appears because the installer isn't signed with an expensive
certificate. The installer is safe - you can review the source code here:
https://github.com/travelingradish/Dear_Me

================================================================================
                         DOWNLOADING THE AI MODEL
================================================================================

If you skipped the model download during installation (it's ~4.7GB):

1. Open Command Prompt (Win + R, type "cmd")
2. Run: ollama pull llama3.1:8b
3. Wait 15-20 minutes for download to complete
4. Launch Dear Me - it will now work!

================================================================================
                          DAILY USE (AFTER SETUP)
================================================================================

Every time you want to use Dear Me:
  1. Double-click "Dear Me" on your Desktop (or Start Menu)
  2. Wait ~30 seconds for everything to start
  3. Your browser opens to http://localhost:3000
  4. Close the command window when done

================================================================================
                         ACCESSING FROM YOUR PHONE
================================================================================

To access Dear Me from another device on the same WiFi:

1. Look for this line in the command window:
   "Phone (same WiFi): http://192.168.x.x:3000"

2. Open that URL in your phone's browser

Note: This only works if both devices are on the same WiFi network.

================================================================================
                              HOW TO STOP
================================================================================

To stop Dear Me:
  1. Close the command window, OR
  2. Press Ctrl+C in the command window

Your journal entries are automatically saved - no data loss when you stop.

================================================================================
                            TROUBLESHOOTING
================================================================================

"Ollama service not responding"
  - Install Ollama from: https://ollama.ai
  - Restart your computer
  - Run setup_windows.bat again

"Python/Node.js not found"
  - Run the install_dependencies.ps1 script manually:
    Right-click: powershell -ExecutionPolicy Bypass -File windows\install_dependencies.ps1

"Port 8001 or 3000 already in use"
  - Another application is using these ports
  - Close other applications that use these ports
  - Restart your computer if needed

"Model download failed"
  - Check your internet connection
  - Try again later: ollama pull llama3.1:8b

For more help, visit: https://github.com/travelingradish/Dear_Me/issues

================================================================================
                            UNINSTALLING
================================================================================

To uninstall Dear Me:
  1. Go to Settings → Apps → Apps & features
  2. Find "Dear Me" in the list
  3. Click it and select "Uninstall"
  4. Your journal entries are preserved

To find your journal data after uninstall:
  - Look in: %LOCALAPPDATA%\DearMe\backend\dear_me.db

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
