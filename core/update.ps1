# AGI_Start Auto-Updater
# Runs daily via Task Scheduler

$ProductDir = "F:\naveen\AGI_Start"
$LogFile = "$ProductDir\logs\updater.log"
$Branch = "main"

function Log($msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $msg" | Tee-Object -FilePath $LogFile -Append
}

Log "=== Auto-updater started ==="

# Step 1 — check if git is available
try {
    $gitVersion = git --version
    Log "Git found: $gitVersion"
}
catch {
    Log "ERROR: Git not found. Skipping update."
    exit 1
}

# Step 2 — fetch latest from GitHub
Set-Location $ProductDir
Log "Fetching latest from GitHub..."

try {
    git fetch origin $Branch 2>&1 | ForEach-Object { Log $_ }
}
catch {
    Log "ERROR: Could not fetch from GitHub: $_"
    exit 1
}

# Step 3 — check if update is available
$local = git rev-parse HEAD
$remote = git rev-parse "origin/$Branch"

if ($local -eq $remote) {
    Log "Already up to date. No update needed."
    Log "=== Auto-updater finished ==="
    exit 0
}

Log "Update available: $local -> $remote"

# Step 4 — pull latest code
Log "Pulling latest code..."
git pull origin $Branch 2>&1 | ForEach-Object { Log $_ }

# Step 5 — install new dependencies
Log "Installing new dependencies..."
uv sync 2>&1 | ForEach-Object { Log $_ }

# Step 6 — restart API
Log "Restarting API..."
try {
    $process = Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Name "uvicorn" -Force
        Log "Stopped old API process"
    }
}
catch {
    Log "No running API process found"
}

Start-Sleep -Seconds 3

# Step 7 — log completion
Log "Update complete: now at $(git rev-parse HEAD)"
Log "=== Auto-updater finished ==="