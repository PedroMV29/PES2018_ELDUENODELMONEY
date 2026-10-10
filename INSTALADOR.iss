#define MyAppName "PES2018_ELDUEÑODELMONEY"
#define MyAppVersion "3.4"
#define MyAppExeName "PES2018_ELDUEÑODELMONEY.exe"

[Setup]
AppId={{D14970AC-02F9-4F13-932A-E60B84323F77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PES 2018 DueñodelMundo (proyecto independiente)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=instalador
OutputBaseFilename=PES2018_ELDUEÑODELMONEY_Setup_3_4
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir PES 2018 DueñodelMundo"; Flags: nowait postinstall skipifsilent
