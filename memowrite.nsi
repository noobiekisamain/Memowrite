; Memowrite - Windows setup wizard
; Build with:  makensis memowrite.nsi

Unicode true
SetCompressor /SOLID lzma
SetCompressorDictSize 32

!define APPNAME "Memowrite"
!define VERSION "1.0.0"
!define PUBLISHER "Memowrite"
!define STAGE "/tmp/claude-0/stage"
!define BRAND "/home/claude/mw/branding"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Memowrite"

Name "${APPNAME} ${VERSION}"
OutFile "/home/claude/mw/dist/Memowrite-Setup-${VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\Memowrite"
InstallDirRegKey HKCU "Software\Memowrite" "InstallDir"
RequestExecutionLevel user
BrandingText "Memowrite ${VERSION} - code in plain English"
ShowInstDetails show
ShowUninstDetails show

VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Memowrite"
VIAddVersionKey "FileDescription" "Memowrite Setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "LegalCopyright" "MIT License"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

!define MUI_ICON "${BRAND}/memowrite.ico"
!define MUI_UNICON "${BRAND}/memowrite.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${BRAND}/wizard-side.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${BRAND}/wizard-side.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "${BRAND}/wizard-header.bmp"
!define MUI_ABORTWARNING
!define MUI_COMPONENTSPAGE_SMALLDESC

!define MUI_WELCOMEPAGE_TITLE "Welcome to Memowrite"
!define MUI_WELCOMEPAGE_TEXT "Memowrite is a programming language written in plain English words.$\r$\n$\r$\n    say $\"Hello!$\"$\r$\n    repeat 3 times$\r$\n        draw star at random(0, 400), 100$\r$\n    end$\r$\n$\r$\nThis wizard installs:$\r$\n  - the Memowrite language and Memowrite Studio$\r$\n  - 25 example programs (apps, games, 2D models)$\r$\n  - Visual Studio Code and Visual Studio support$\r$\n  - the 'memowrite' command and .mw file icons$\r$\n$\r$\nNo administrator rights are needed. Click Next to continue."

!define MUI_FINISHPAGE_TITLE "Memowrite is ready!"
!define MUI_FINISHPAGE_TEXT "Memowrite has been installed.$\r$\n$\r$\nOpen Memowrite Studio, pick something from Examples and press F5 to run it. Double-click any .mw file to run it too."
!define MUI_FINISHPAGE_RUN "$INSTDIR\MemowriteStudio.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Open Memowrite Studio"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Show everything Memowrite can do (Examples.md)"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION ShowExamplesDoc
!define MUI_FINISHPAGE_LINK "Open the examples folder"
!define MUI_FINISHPAGE_LINK_LOCATION "$INSTDIR\examples"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${STAGE}/LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Var VSCodeCli

; ------------------------------------------------------------------ sections

Section "Memowrite language and Studio (required)" SecCore
  SectionIn RO
  SetOutPath "$INSTDIR"
  ; remove an old copy of the interpreter first so no stale files are left behind
  RMDir /r "$INSTDIR\memowrite"
  File /r "${STAGE}/*.*"

  WriteRegStr HKCU "Software\Memowrite" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Memowrite" "Version" "${VERSION}"
  WriteUninstaller "$INSTDIR\Uninstall Memowrite.exe"

  WriteRegStr HKCU "${UNINSTKEY}" "DisplayName" "Memowrite ${VERSION}"
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTKEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayIcon" "$INSTDIR\branding\memowrite.ico"
  WriteRegStr HKCU "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTKEY}" "UninstallString" "$\"$INSTDIR\Uninstall Memowrite.exe$\""
  WriteRegStr HKCU "${UNINSTKEY}" "QuietUninstallString" "$\"$INSTDIR\Uninstall Memowrite.exe$\" /S"
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKCU "${UNINSTKEY}" "EstimatedSize" "$0"

  ; warm up: compile the interpreter once so the first run is fast
  DetailPrint "Preparing Memowrite..."
  nsExec::ExecToLog '"$INSTDIR\runtime\python.exe" -X utf8 -m compileall -q "$INSTDIR\memowrite"'
  Pop $0
SectionEnd

Section "Start menu shortcuts" SecStart
  CreateDirectory "$SMPROGRAMS\Memowrite"
  CreateShortcut "$SMPROGRAMS\Memowrite\Memowrite Studio.lnk" "$INSTDIR\MemowriteStudio.exe" "" "$INSTDIR\branding\memowrite.ico" 0
  CreateShortcut "$SMPROGRAMS\Memowrite\Memowrite Shell.lnk" "$INSTDIR\memowrite.exe" "" "$INSTDIR\branding\memowrite.ico" 0
  CreateShortcut "$SMPROGRAMS\Memowrite\Memowrite Examples.lnk" "$INSTDIR\examples"
  CreateShortcut "$SMPROGRAMS\Memowrite\Everything Memowrite Can Do.lnk" "notepad.exe" "$\"$INSTDIR\Examples.md$\""
  CreateShortcut "$SMPROGRAMS\Memowrite\Uninstall Memowrite.lnk" "$INSTDIR\Uninstall Memowrite.exe"
SectionEnd

Section "Desktop shortcut" SecDesktop
  CreateShortcut "$DESKTOP\Memowrite Studio.lnk" "$INSTDIR\MemowriteStudio.exe" "" "$INSTDIR\branding\memowrite.ico" 0
SectionEnd

Section "Open .mw files with Memowrite (file icon)" SecAssoc
  WriteRegStr HKCU "Software\Classes\.mw" "" "Memowrite.Program"
  WriteRegStr HKCU "Software\Classes\.mw" "Content Type" "text/plain"
  WriteRegStr HKCU "Software\Classes\.mw" "PerceivedType" "text"
  WriteRegStr HKCU "Software\Classes\.mw\ShellNew" "NullFile" ""
  WriteRegStr HKCU "Software\Classes\Memowrite.Program" "" "Memowrite Program"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\DefaultIcon" "" "$INSTDIR\branding\memowrite-file.ico"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell" "" "open"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\open" "" "Run with Memowrite"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\open\command" "" "$\"$INSTDIR\memowrite.exe$\" --pause $\"%1$\""
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\edit" "" "Edit with Memowrite Studio"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\edit" "Icon" "$INSTDIR\branding\memowrite.ico"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\edit\command" "" "$\"$INSTDIR\MemowriteStudio.exe$\" $\"%1$\""
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\check" "" "Check for mistakes"
  WriteRegStr HKCU "Software\Classes\Memowrite.Program\shell\check\command" "" "$\"$INSTDIR\memowrite.exe$\" --pause check $\"%1$\""
  WriteRegStr HKCU "Software\Classes\Applications\MemowriteStudio.exe\shell\open\command" "" "$\"$INSTDIR\MemowriteStudio.exe$\" $\"%1$\""
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
SectionEnd

Section "Add the memowrite command to PATH" SecPath
  DetailPrint "Adding $INSTDIR to your PATH..."
  nsExec::ExecToLog `powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$$d='$INSTDIR'; $$p=[Environment]::GetEnvironmentVariable('Path','User'); if(-not $$p){$$p=''}; if(($$p -split ';') -notcontains $$d){ [Environment]::SetEnvironmentVariable('Path', (($$p.TrimEnd(';') + ';' + $$d).TrimStart(';')), 'User') }"`
  Pop $0
SectionEnd

Section "Visual Studio Code extension" SecVSCode
  StrCpy $VSCodeCli ""
  ${If} ${FileExists} "$LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
    StrCpy $VSCodeCli "$LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
  ${ElseIf} ${FileExists} "$PROGRAMFILES64\Microsoft VS Code\bin\code.cmd"
    StrCpy $VSCodeCli "$PROGRAMFILES64\Microsoft VS Code\bin\code.cmd"
  ${ElseIf} ${FileExists} "$PROGRAMFILES\Microsoft VS Code\bin\code.cmd"
    StrCpy $VSCodeCli "$PROGRAMFILES\Microsoft VS Code\bin\code.cmd"
  ${EndIf}
  ${If} $VSCodeCli != ""
    DetailPrint "Installing the Memowrite extension into Visual Studio Code..."
    nsExec::ExecToLog `"$VSCodeCli" --install-extension "$INSTDIR\vscode\memowrite-1.0.0.vsix" --force`
    Pop $0
  ${Else}
    ; VS Code not found: drop the extension where VS Code looks for extensions
    DetailPrint "Visual Studio Code was not found - copying the extension into your .vscode folder"
    SetOutPath "$PROFILE\.vscode\extensions\memowrite.memowrite-1.0.0"
    File /r "${STAGE}/vscode/memowrite/*.*"
    SetOutPath "$INSTDIR"
  ${EndIf}
SectionEnd

Section "Visual Studio 2019/2022 syntax colors" SecVS
  ; Visual Studio reads TextMate grammars from %USERPROFILE%\.vs\Extensions
  SetOutPath "$PROFILE\.vs\Extensions\Memowrite"
  File /r "${STAGE}/vscode/memowrite/*.*"
  SetOutPath "$INSTDIR"
SectionEnd

Section "Copy examples to Documents\Memowrite" SecDocs
  SetOutPath "$DOCUMENTS\Memowrite\Examples"
  SetOverwrite off
  File /r "${STAGE}/examples/*.*"
  SetOverwrite on
  SetOutPath "$DOCUMENTS\Memowrite"
  SetOverwrite off
  File "${STAGE}/File.Memory"
  SetOverwrite on
  SetOutPath "$INSTDIR"
SectionEnd

; ------------------------------------------------------------------ descriptions

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "The Memowrite language, its huge standard library, Memowrite Studio, the 'memowrite' command, the logo and Examples.md."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStart} "Memowrite Studio, Shell, Examples and the guide in your Start menu."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "A Memowrite Studio icon on your desktop."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecAssoc} "Shows the Memowrite icon on .mw files. Double-click runs them, right-click edits them."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecPath} "Lets you type 'memowrite game.mw' in any terminal (also needed by the VS Code Run button)."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecVSCode} "Syntax colors, snippets, a Run button and mistake checking for .mw files in Visual Studio Code."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecVS} "Memowrite syntax colors inside Visual Studio 2019 and 2022."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "Your own copy of the example programs in Documents\Memowrite to change and play with."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Function ShowExamplesDoc
  Exec '"notepad.exe" "$INSTDIR\Examples.md"'
FunctionEnd

Function .onInit
  ; already installed? reuse that folder
  ReadRegStr $0 HKCU "Software\Memowrite" "InstallDir"
  ${If} $0 != ""
    StrCpy $INSTDIR $0
  ${EndIf}
FunctionEnd

; ------------------------------------------------------------------ uninstall

Section "Uninstall"
  ; VS Code extension
  StrCpy $0 ""
  ${If} ${FileExists} "$LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
    StrCpy $0 "$LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
  ${ElseIf} ${FileExists} "$PROGRAMFILES64\Microsoft VS Code\bin\code.cmd"
    StrCpy $0 "$PROGRAMFILES64\Microsoft VS Code\bin\code.cmd"
  ${EndIf}
  ${If} $0 != ""
    nsExec::ExecToLog `"$0" --uninstall-extension memowrite.memowrite`
    Pop $1
  ${EndIf}
  RMDir /r "$PROFILE\.vscode\extensions\memowrite.memowrite-1.0.0"
  RMDir /r "$PROFILE\.vs\Extensions\Memowrite"

  ; PATH
  nsExec::ExecToLog `powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$$d='$INSTDIR'; $$p=[Environment]::GetEnvironmentVariable('Path','User'); if($$p){ $$n=(($$p -split ';') | Where-Object { $$_ -and ($$_ -ne $$d) }) -join ';'; [Environment]::SetEnvironmentVariable('Path', $$n, 'User') }"`
  Pop $1

  ; file association
  ReadRegStr $1 HKCU "Software\Classes\.mw" ""
  ${If} $1 == "Memowrite.Program"
    DeleteRegKey HKCU "Software\Classes\.mw"
  ${EndIf}
  DeleteRegKey HKCU "Software\Classes\Memowrite.Program"
  DeleteRegKey HKCU "Software\Classes\Applications\MemowriteStudio.exe"
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'

  ; shortcuts
  Delete "$DESKTOP\Memowrite Studio.lnk"
  RMDir /r "$SMPROGRAMS\Memowrite"

  ; files (your own programs in Documents\Memowrite are kept)
  RMDir /r "$INSTDIR\runtime"
  RMDir /r "$INSTDIR\memowrite"
  RMDir /r "$INSTDIR\examples"
  RMDir /r "$INSTDIR\library"
  RMDir /r "$INSTDIR\branding"
  RMDir /r "$INSTDIR\vscode"
  Delete "$INSTDIR\memowrite.exe"
  Delete "$INSTDIR\MemowriteStudio.exe"
  Delete "$INSTDIR\Examples.md"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\File.Memory"
  Delete "$INSTDIR\Uninstall Memowrite.exe"
  RMDir "$INSTDIR"

  DeleteRegKey HKCU "${UNINSTKEY}"
  DeleteRegKey HKCU "Software\Memowrite"
SectionEnd
