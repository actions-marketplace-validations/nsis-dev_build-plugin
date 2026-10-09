; Uniform installer for an NSIS plugin: copies the Plugins directory of a Release Archive tree into NSISDIR.
; makensis -DNAME=Foo -DVERSION=1.0.0 -DSRC=<dir> [-DLICENSE=<file>] -DOUTFILE=<exe> installer.nsi
; Without LICENSE, there is no license page
!ifndef NAME
  !error "define NAME"
!endif

!ifndef VERSION
  !error "define VERSION"
!endif

!ifndef SRC
  !error "define SRC"
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

!include MUI2.nsh

!ifdef LICENSE
  !insertmacro MUI_PAGE_LICENSE "${LICENSE}"
!endif
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

!macro ShipFolder Folder
  !if /FileExists "${SRC}\${Folder}"
    File /r "${SRC}\${Folder}"
  !endif
!macroend

Section
  SetOutPath "$INSTDIR"
  !insertmacro ShipFolder Plugins
  !insertmacro ShipFolder Contrib
  !insertmacro ShipFolder Docs
  !insertmacro ShipFolder Examples
  !insertmacro ShipFolder Include
SectionEnd
