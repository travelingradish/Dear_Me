; Dear Me - NSIS Installer Script
; Build with: makensis /DAPP_VERSION=1.0.0 build_installer.nsi
; Output: ..\Dear_Me_1.0.0_Windows.exe

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "x64.nsh"

; Define version (passed from build_installer.ps1)
!ifndef APP_VERSION
  !define APP_VERSION "1.0.0"
!endif

; Basic settings
Name "Dear Me"
OutFile "..\Dear_Me_${APP_VERSION}_Windows.exe"
InstallDir "$LOCALAPPDATA\DearMe"
RequestExecutionLevel user

; UI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install Dear Me"
  SetOutPath "$INSTDIR"

  ; Copy backend directory
  File /r "..\backend"

  ; Copy frontend build (only build, not node_modules)
  File /r "..\frontend\build"

  ; Copy windows launcher scripts
  File /r "..\windows"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall_DearMe.exe"

  ; Register in Add/Remove Programs (per-user)
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe" "DisplayName" "Dear Me"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe" "UninstallString" "$INSTDIR\Uninstall_DearMe.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe" "Publisher" "Dear Me"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe" "DisplayIcon" "$INSTDIR\windows\assets\dear_me.ico"

  ; Desktop shortcut
  CreateDirectory "$DESKTOP"
  CreateShortcut "$DESKTOP\Dear Me.lnk" "cmd.exe" '/c "$INSTDIR\windows\setup_windows.bat"' "$INSTDIR\windows\assets\dear_me.ico"

  ; Start Menu
  CreateDirectory "$SMPROGRAMS\Dear Me"
  CreateShortcut "$SMPROGRAMS\Dear Me\Dear Me.lnk" "cmd.exe" '/c "$INSTDIR\windows\setup_windows.bat"' "$INSTDIR\windows\assets\dear_me.ico"
  CreateShortcut "$SMPROGRAMS\Dear Me\Uninstall.lnk" "$INSTDIR\Uninstall_DearMe.exe"

  DetailPrint "Installation complete!"
SectionEnd

Section "Install Prerequisites"
  ; Run PowerShell script to install Python, Node, Ollama
  ; This runs with admin elevation if needed
  nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\windows\install_dependencies.ps1"'
  Pop $0

  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION "Prerequisites installation had issues. You may need to install Python 3.13, Node.js, and Ollama manually."
  ${EndIf}
SectionEnd

; Uninstaller section
Section "Uninstall"
  ; Kill running processes
  ExecToLog 'taskkill /FI "WINDOWTITLE eq DearMe-Backend" /F'
  ExecToLog 'taskkill /FI "WINDOWTITLE eq DearMe-Frontend" /F'

  ; Preserve database (user's journal data)
  SetOverwrite off
  File /oname=dear_me.db_backup.txt "..\backend\dear_me.db"
  SetOverwrite on

  ; Remove files
  RMDir /r "$INSTDIR\backend"
  RMDir /r "$INSTDIR\frontend"
  RMDir /r "$INSTDIR\windows"

  ; Remove uninstaller
  Delete "$INSTDIR\Uninstall_DearMe.exe"
  RMDir "$INSTDIR"

  ; Remove shortcuts
  RMDir /r "$SMPROGRAMS\Dear Me"
  Delete "$DESKTOP\Dear Me.lnk"

  ; Remove registry entry
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe"

  ; Show message about preserved data
  MessageBox MB_ICONINFORMATION "Dear Me has been uninstalled. Your journal entries have been preserved at $INSTDIR (if the folder still exists)."
SectionEnd

; Helper function for version comparison
!macro ReadUninstaller
  ReadRegStr $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\DearMe" "UninstallString"
  ${If} $R0 != ""
    MessageBox MB_ICONQUESTION "An older version of Dear Me is installed. Would you like to remove it first?" IDYES UninstallOld
    Goto SkipUninstall
    UninstallOld:
      ExecWait '"$R0" _?=$INSTDIR'
    SkipUninstall:
  ${EndIf}
!macroend

Function .onInit
  ${If} ${RunningX64}
    ${If} ${CMAKE_SIZEOF_VOID_P} == 8
      ; 64-bit installer on 64-bit system
    ${Else}
      ; 32-bit installer on 64-bit system (not ideal but works)
      StrCpy $INSTDIR "$LOCALAPPDATA\DearMe"
    ${EndIf}
  ${EndIf}

  ; Check for existing installation
  !insertmacro ReadUninstaller
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION "Are you sure you want to uninstall Dear Me?" IDYES +2
  Abort
FunctionEnd
