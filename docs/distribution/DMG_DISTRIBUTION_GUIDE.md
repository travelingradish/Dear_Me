# DMG Installer Distribution Guide for Dear Me

This guide explains how to build, host, and distribute the Dear Me DMG installer to non-technical users.

## Quick Start

### For You (Developer)

```bash
cd /Users/wenjuanchen/Dear_Me

# Build the DMG installer
bash build_dmg.sh

# Result: Dear_Me_1.0.0.dmg (ready to distribute)
```

**That's it!** The DMG is now ready to share with users.

---

## What's Inside the DMG

When users download and open `Dear_Me_1.0.0.dmg`, they see:

```
Dear Me (DMG Window)
├── Dear Me.app (the application)
├── Applications (symlink for drag-and-drop)
├── install_dependencies.sh (dependency installer)
└── README.txt (user instructions)
```

---

## User Installation Flow (What Users See)

### 1. Download
User downloads `Dear_Me_1.0.0.dmg` from your website/link

### 2. Open
User double-clicks the DMG file → Finder opens installer window

### 3. Drag to Applications
User drags "Dear Me.app" to "Applications" folder
```
Dear Me.app → [Applications folder]
```

### 4. Install Dependencies (First Time)
User double-clicks `install_dependencies.sh`
- Terminal window opens
- Script detects if Ollama, Node.js, Python are installed
- If missing, uses Homebrew to install them automatically
- Takes ~5-10 minutes depending on internet speed

### 5. Launch
User opens Applications folder and double-clicks "Dear Me.app"
- Terminal window opens showing startup progress
- Browser automatically opens to `http://localhost:3000`
- App is ready to use!

### 6. Future Launches
Next time: Just open Applications → Double-click "Dear Me.app"
- No installation needed
- Services start in ~30 seconds
- Browser opens automatically

---

## Distribution Methods

### Option A: Website Download (Recommended)

1. **Upload to your website:**
   ```bash
   # Copy to your web server
   scp Dear_Me_1.0.0.dmg user@yourserver.com:/var/www/downloads/
   ```

2. **Create download page:**
   ```html
   <a href="https://yoursite.com/downloads/Dear_Me_1.0.0.dmg">
     Download Dear Me (1.2 GB)
   </a>
   ```

3. **Users can download and install immediately**

### Option B: Direct Share (Email, Slack, Teams)

If DMG is small enough, attach or share link:
```
Hi! Download Dear Me here:
https://yoursite.com/downloads/Dear_Me_1.0.0.dmg

Just download, open the .dmg, and follow the instructions!
```

### Option C: Cloud Storage (Dropbox, Google Drive, OneDrive)

```
1. Upload Dear_Me_1.0.0.dmg to Dropbox
2. Right-click → Share link
3. Set anyone with link can download
4. Share link with users
```

### Option D: App Store (Advanced)

If you eventually want to distribute via Mac App Store:
- Requires Apple Developer account ($99/year)
- Handles code signing and notarization automatically
- Much larger reach but longer approval process

---

## File Sizes & Bandwidth

```
Dear_Me_1.0.0.dmg breakdown:
├── Dear Me.app (app code)         ~15 MB
├── install_dependencies.sh        ~1 KB
├── README.txt                     ~3 KB
└── (Total compressed)             ~1.2 GB

Note: Large due to system dependency bundles
(Ollama ~500MB, Node.js ~200MB, Python ~300MB)
```

### Bandwidth Considerations

- **For 10 users:** 12 GB total
- **For 100 users:** 120 GB total (might want CDN)
- **For 1000+ users:** Definitely use CDN (Cloudflare, AWS CloudFront)

---

## Customization

### Update App Version

When you release a new version:

```bash
# 1. Update version in build_dmg.sh
# Find: VERSION="1.0.0"
# Change to: VERSION="1.0.1"

# 2. Rebuild DMG
bash build_dmg.sh

# 3. Replace old DMG on your server
# Delete: Dear_Me_1.0.0.dmg
# Upload: Dear_Me_1.0.1.dmg
```

### Update Installation Instructions

Edit `build_dmg.sh` to customize the README.txt with:
- Your website URL
- Your support email
- Custom setup instructions
- Feature list
- Known issues

### Update Dependency Versions

If you want newer versions of Ollama, Node.js, or Python:

Edit the `install_dependencies.sh` section in `build_dmg.sh`:
```bash
# Before (current)
brew install node
brew install python@3.13
brew install ollama

# After (if you want different versions)
brew install node@18    # Specific version
brew install python@3.12  # Different Python version
```

---

## macOS Gatekeeper & Code Signing

### Why Users See a Warning

On first run, macOS shows:
```
"Dear Me.app" cannot be opened because the developer
cannot be verified.
```

This is **normal** for apps not on the App Store. Users can bypass by:
1. Right-clicking the app
2. Selecting "Open"
3. Clicking "Open" again

### Optional: Remove Warning (Requires Notarization)

To remove the warning, you need to notarize your app with Apple:

```bash
# 1. Create Apple Developer account ($99/year)

# 2. After building DMG, notarize it:
xcrun notarytool submit Dear_Me_1.0.0.dmg \
  --apple-id your@apple.id \
  --password your-app-password \
  --team-id YOUR_TEAM_ID

# 3. Staple the notarization:
xcrun stapler staple Dear_Me_1.0.0.dmg

# Now users won't see the warning!
```

**Cost:** Free (just Apple Developer account)
**Time:** ~30 minutes setup
**Worth it:** Only if distributing to 100+ users

---

## Testing Before Distribution

### Test the DMG Installation Locally

```bash
# 1. Build DMG
bash build_dmg.sh

# 2. Mount it
open Dear_Me_1.0.0.dmg

# 3. Try the installation:
# - Drag Dear Me.app to Applications
# - Run install_dependencies.sh
# - Launch Dear Me.app
# - Verify it works!
```

### Test on Different Macs

If possible, test on:
- [ ] Your Mac (Intel)
- [ ] Friend's Mac (if different architecture - M1/M2/Intel)
- [ ] Older macOS version (if supporting older OS)
- [ ] Fresh user account (simulates new user)

### Checklist Before Sharing

- [ ] DMG builds without errors
- [ ] Can drag app to Applications
- [ ] install_dependencies.sh is executable
- [ ] Services start correctly
- [ ] Browser opens automatically
- [ ] WiFi IP is displayed for mobile access
- [ ] Tested on at least one other Mac

---

## Troubleshooting for Users

### Common Issues & Solutions

#### "Permission Denied" on install script
```bash
# Solution: Make script executable
chmod +x install_dependencies.sh
# Then double-click again
```

#### "Ollama not found" after installation
```bash
# Solution: Restart Terminal
# Or verify Homebrew installed it:
brew list | grep ollama
```

#### App won't launch
```bash
# Try launching from command line:
open /Applications/Dear\ Me.app

# Check for errors in Terminal output
```

#### Port 8001 or 3000 in use
```bash
# Already handled by setup.sh!
# But if issues persist:
lsof -i :8001  # See what's using port
kill -9 <PID>  # Kill the process
```

---

## Support Resources to Create

Before distributing, consider creating:

1. **Installation Video** (2-3 min YouTube)
   - Show drag-to-applications step
   - Show dependency install
   - Show first launch

2. **FAQ Document**
   - Gatekeeper warning explanation
   - Phone access setup
   - Common errors and fixes

3. **Support Email/Contact**
   - For users having issues
   - Update frequency communication

4. **Release Notes**
   - What's new in each version
   - Known issues
   - Roadmap

---

## Distribution Checklist

- [ ] DMG builds successfully
- [ ] Tested installation on 2+ Macs
- [ ] Tested with fresh user account
- [ ] All documentation is accurate
- [ ] Download hosting set up (website/cloud storage)
- [ ] Support email/contact ready
- [ ] FAQ document created
- [ ] Installation instructions are clear
- [ ] Gatekeeper behavior explained to users
- [ ] Version numbering system decided (1.0.0, 1.0.1, etc.)

---

## Version Management

### Naming Convention
```
Dear_Me_MAJOR.MINOR.PATCH.dmg

Examples:
Dear_Me_1.0.0.dmg    (Initial release)
Dear_Me_1.0.1.dmg    (Bug fix)
Dear_Me_1.1.0.dmg    (New feature)
Dear_Me_2.0.0.dmg    (Major update)
```

### Update Process

1. **Update code in your repo**
2. **Update version in build_dmg.sh**
3. **Run: `bash build_dmg.sh`**
4. **Test thoroughly**
5. **Upload to distribution site**
6. **Announce update to users**

---

## Next Steps

1. **Build your first DMG:**
   ```bash
   bash build_dmg.sh
   ```

2. **Test it thoroughly:**
   - Mount the DMG
   - Run through installation
   - Verify everything works

3. **Set up distribution:**
   - Choose hosting method
   - Create download page
   - Test download link

4. **Create support resources:**
   - FAQ document
   - Installation guide PDF
   - Support email

5. **Share with users!**

---

## Questions?

If you need to customize further:
- Edit `build_dmg.sh` directly
- Modify installation scripts
- Add custom branding
- Update README.txt with your info

All the building blocks are in place to create a professional DMG installer for non-technical users.

Good luck with your launch! 🚀
