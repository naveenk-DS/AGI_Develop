[Setup]
AppName=AGI_Start
AppVersion=0.2.0
AppPublisher=Naveen
AppPublisherURL=https://github.com/naveenk-DS/AGI_Develop
DefaultDirName={autopf}\AGI_Start
DefaultGroupName=AGI_Start
OutputDir=F:\naveen\AGI_Start\installer\output
OutputBaseFilename=AGI_Start_Setup_v0.2.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=F:\naveen\AGI_Start\installer\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"
Name: "autostart";   Description: "Start automatically on Windows boot"; GroupDescription: "Startup:"

[Files]
Source: "F:\naveen\AGI_Start\app\*";        DestDir: "{app}\app";        Flags: ignoreversion recursesubdirs
Source: "F:\naveen\AGI_Start\core\*";       DestDir: "{app}\core";       Flags: ignoreversion recursesubdirs
Source: "F:\naveen\AGI_Start\config\*";     DestDir: "{app}\config";     Flags: ignoreversion recursesubdirs
Source: "F:\naveen\AGI_Start\tests\*";      DestDir: "{app}\tests";      Flags: ignoreversion recursesubdirs
Source: "F:\naveen\AGI_Start\pyproject.toml"; DestDir: "{app}";          Flags: ignoreversion
Source: "F:\naveen\AGI_Start\requirements.txt"; DestDir: "{app}";        Flags: ignoreversion

[Icons]
Name: "{group}\AGI_Start Dashboard";  Filename: "{app}\core\open_dashboard.bat"
Name: "{group}\AGI_Start Stop";       Filename: "{app}\core\stop.bat"
Name: "{group}\Uninstall AGI_Start";  Filename: "{uninstallexe}"
Name: "{commondesktop}\AGI_Start";    Filename: "{app}\core\open_dashboard.bat"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-File ""{app}\installer\post_install.ps1"""; \
    Flags: runhidden waituntilterminated; StatusMsg: "Setting up AGI_Start..."

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-File ""{app}\installer\uninstall.ps1"""; \
    Flags: runhidden waituntilterminated