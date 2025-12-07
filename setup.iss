[Setup]
AppName=AuEdu
AppVersion=1.0.0
DefaultDirName={pf}\AuEdu
OutputDir=Installer
OutputBaseFilename=AuEdu_Installer
SetupIconFile=icoapp.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\AuEdu.exe"; DestDir: "{app}"
Source: "resources\*"; DestDir: "{app}\resources"; Flags: recursesubdirs
Source: "form\*"; DestDir: "{app}\form"; Flags: recursesubdirs
Source: "models\*"; DestDir: "{app}\models"; Flags: recursesubdirs
Source: "image_student\*"; DestDir: "{app}\image_student"; Flags: recursesubdirs

[Icons]
Name: "{commondesktop}\AuEdu"; Filename: "{app}\AuEdu.exe"
