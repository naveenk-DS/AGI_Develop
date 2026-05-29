# Post-install script — runs after Inno Setup copies files
$InstallDir = $args[0]
if (-not $InstallDir) { $InstallDir = "C:\Program Files\AGI_Start" }

$LogFile = "$InstallDir\logs\install.log"
New-Item -ItemType Directory -Force -Path "$InstallDir\logs"
New-Item -ItemType Directory -Force -Path "$InstallDir\data\qdrant"
New-Item -ItemType Directory -Force -Path "$InstallDir\data\n8n"
New-Item -ItemType Directory -Force -Path "$InstallDir\backups"
New-Item -ItemType Directory -Force -Path "$InstallDir\watch\processed"

function Log($msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $msg" | Tee-Object -FilePath $LogFile -Append
}

Log "AGI_Start post-install started"

# Install Python dependencies
Log "Installing Python dependencies..."
Set-Location $InstallDir
uv sync 2>&1 | ForEach-Object { Log $_ }

# Register auto-start
Log "Registering auto-start..."
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$InstallDir\core\start.bat`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask `
    -TaskName "AGI_Start_Service" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force

# Register auto-updater
$updateAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-File `"$InstallDir\core\update.ps1`""
$updateTrigger = New-ScheduledTaskTrigger -Daily -At "03:15AM"
$updateSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName "AGI_Start_AutoUpdater" `
    -Action $updateAction `
    -Trigger $updateTrigger `
    -Settings $updateSettings `
    -Principal $principal `
    -Force

Log "AGI_Start installed successfully"
Log "Starting services..."

Start-Process "cmd.exe" -ArgumentList "/c `"$InstallDir\core\start.bat`"" -WindowStyle Hidden