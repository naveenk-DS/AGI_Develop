# Uninstall script
Write-Host "Uninstalling AGI_Start..."

# Stop services
try {
    $proc = Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue
    if ($proc) { Stop-Process -Name "uvicorn" -Force }
}
catch {}

# Stop Docker services
$InstallDir = "C:\Program Files\AGI_Start"
if (Test-Path "$InstallDir\core\docker-compose.yml") {
    Set-Location "$InstallDir\core"
    docker compose down 2>$null
}

# Remove scheduled tasks
Unregister-ScheduledTask -TaskName "AGI_Start_Service"     -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "AGI_Start_AutoUpdater" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "AGI_Start_AutoStart"   -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "AGI_Start uninstalled successfully"