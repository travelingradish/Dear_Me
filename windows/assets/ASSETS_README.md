# Windows Installer Assets

This directory contains visual assets for the Windows installer.

## Files Needed

### `dear_me.ico` (Required)
- **Purpose**: Application icon shown in shortcuts and Add/Remove Programs
- **Source**: Convert from `../../frontend/public/logo192.png`
- **Format**: Windows ICO (supports multiple sizes: 256, 48, 32, 16 pixels)
- **How to create**:

Using ImageMagick (recommended):
```powershell
magick convert ../../frontend/public/logo192.png -define icon:auto-resize="256,48,32,16" dear_me.ico
```

Or use an online converter:
https://convertio.co/png-ico/ → upload `logo192.png` → download as ICO

### `installer_banner.bmp` (Optional)
- **Purpose**: NSIS installer header image
- **Format**: 24-bit BMP, exactly 150x57 pixels
- **Currently**: Not required by current build_installer.nsi
- **If needed**: Create a gradient background with Dear Me logo, 150x57px, save as BMP

## Build System Note

The `build_installer.ps1` script attempts to create the ICO file automatically:
```powershell
magick convert ../../frontend/public/logo192.png -define icon:auto-resize="256,48,32,16" dear_me.ico
```

If ImageMagick is not installed, the icon conversion is skipped and the installer will use the default Windows icon.

## Testing

To verify icons are working:
1. After building the installer, check shortcuts in Start Menu
2. Right-click a shortcut → Properties to see the icon
3. The executable's icon should appear in File Explorer

---

*Note: Assets are not tracked in git (.gitignore). They are created during the build process.*
