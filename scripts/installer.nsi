; Uniform installer for an NSIS package: copies the NSISDIR folders of a Release Archive tree into NSISDIR.
; makensis -DNAME=Foo -DVERSION=1.0.0 -DSRC=<dir> -DFILES=<nsh> [-DLICENSE=<file>] -DOUTFILE=<exe> installer.nsi
; FILES, written by installer.py, lists every shipped path. Without LICENSE, there is no license page
;
; The uninstaller removes only what this package created: a path that already existed,
; from NSIS itself or another package, is overwritten but never logged, so never deleted.
; Paths an earlier version of the package created stay logged across upgrades
!ifndef NAME
  !error "define NAME"
!endif

!ifndef VERSION
  !error "define VERSION"
!endif

!ifndef SRC
  !error "define SRC"
!endif

!ifndef FILES
  !error "define FILES"
!endif

!ifndef OUTFILE
  !error "define OUTFILE"
!endif

Unicode true
ManifestDPIAware true
SetCompressor /SOLID lzma

Name "${NAME} ${VERSION}"
OutFile "${OUTFILE}"
RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\NSIS"
InstallDirRegKey HKLM "Software\NSIS" ""

!define UNINST_DIR "$INSTDIR\Uninstall"
!define UNINST_EXE "${UNINST_DIR}\${NAME}.exe"
; Which paths the installer created, as keys of the files and dirs sections
!define UNINST_LOG "${UNINST_DIR}\${NAME}.ini"
; ponytail: one Add/Remove Programs entry per package, the last NSIS folder installed to wins
!define ARP "Software\Microsoft\Windows\CurrentVersion\Uninstall\NSIS ${NAME}"

!include LogicLib.nsh
!include MUI2.nsh

!ifdef LICENSE
  !insertmacro MUI_PAGE_LICENSE "${LICENSE}"
!endif
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

!macro PackageDir Path
  ${IfNot} ${FileExists} "$INSTDIR\${Path}\*.*"
    CreateDirectory "$INSTDIR\${Path}"
    WriteINIStr "${UNINST_LOG}" dirs "${Path}" 1
  ${EndIf}
!macroend

!macro PackageFile Path
  ${IfNot} ${FileExists} "$INSTDIR\${Path}"
    WriteINIStr "${UNINST_LOG}" files "${Path}" 1
  ${EndIf}
  File "/oname=$INSTDIR\${Path}" "${SRC}\${Path}"
!macroend

!macro UnPackageFile Path
  ReadINIStr $0 "${UNINST_LOG}" files "${Path}"
  ${If} $0 == 1
    Delete "$INSTDIR\${Path}"
  ${EndIf}
!macroend

; RMDir without /r: a folder something else has put files in stays
!macro UnPackageDir Path
  ReadINIStr $0 "${UNINST_LOG}" dirs "${Path}"
  ${If} $0 == 1
    RMDir "$INSTDIR\${Path}"
  ${EndIf}
!macroend

!include "${FILES}"

Section
  CreateDirectory "${UNINST_DIR}"
  !insertmacro PackageInstall
  WriteUninstaller "${UNINST_EXE}"

  WriteRegStr HKLM "${ARP}" DisplayName "${NAME} (NSIS)"
  WriteRegStr HKLM "${ARP}" DisplayVersion "${VERSION}"
  WriteRegStr HKLM "${ARP}" InstallLocation "$INSTDIR"
  WriteRegStr HKLM "${ARP}" UninstallString '"${UNINST_EXE}"'
  WriteRegStr HKLM "${ARP}" QuietUninstallString '"${UNINST_EXE}" /S'
  WriteRegDWORD HKLM "${ARP}" NoModify 1
  WriteRegDWORD HKLM "${ARP}" NoRepair 1
SectionEnd

; The uninstaller lives in NSISDIR\Uninstall, its parent is NSISDIR
Function un.onInit
  GetFullPathName $INSTDIR "$INSTDIR\.."
FunctionEnd

Section Uninstall
  !insertmacro PackageUninstall
  Delete "${UNINST_LOG}"
  Delete "${UNINST_EXE}"
  ; Shared by every package, removed with the last one
  RMDir "${UNINST_DIR}"
  DeleteRegKey HKLM "${ARP}"
SectionEnd
