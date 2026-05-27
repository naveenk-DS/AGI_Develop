Write-Host "=== AGI_Start Smoke Test v0.2.0 ===" -ForegroundColor Cyan

$pass = 0
$fail = 0

function Check($name, $url, $method = "GET") {
    try {
        if ($method -eq "GET") {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        }
        else {
            $r = Invoke-WebRequest -Uri $url -Method POST -UseBasicParsing -TimeoutSec 10
        }
        if ($r.StatusCode -eq 200) {
            Write-Host "  PASS  $name" -ForegroundColor Green
            $global:pass++
        }
        else {
            Write-Host "  FAIL  $name (status $($r.StatusCode))" -ForegroundColor Red
            $global:fail++
        }
    }
    catch {
        Write-Host "  FAIL  $name (unreachable)" -ForegroundColor Red
        $global:fail++
    }
}

Write-Host ""
Write-Host "Core Services" -ForegroundColor Yellow
Check "FastAPI Health"       "http://127.0.0.1:8001/health"
Check "Ollama"               "http://127.0.0.1:11434/api/tags"
Check "Qdrant"               "http://127.0.0.1:6333/healthz"
Check "n8n"                  "http://127.0.0.1:5678/healthz"

Write-Host ""
Write-Host "API Endpoints" -ForegroundColor Yellow
Check "Dashboard"            "http://127.0.0.1:8001/dashboard/"
Check "Agent tools"          "http://127.0.0.1:8001/agent/tools"
Check "Backup list"          "http://127.0.0.1:8001/backup/list"
Check "License status"       "http://127.0.0.1:8001/license/status"
Check "Templates list"       "http://127.0.0.1:8001/templates/list"
Check "Sessions list"        "http://127.0.0.1:8001/sessions/list"
Check "Analytics overview"   "http://127.0.0.1:8001/analytics/overview"
Check "Settings all"         "http://127.0.0.1:8001/settings/all"

Write-Host ""
Write-Host "Auth" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8001/webhook/test" `
        -Headers @{"X-API-Key" = "naveen-agi-webhook-key-2024" } `
        -UseBasicParsing -TimeoutSec 10
    if ($r.StatusCode -eq 200) {
        Write-Host "  PASS  Webhook auth test" -ForegroundColor Green
        $global:pass++
    }
    else {
        Write-Host "  FAIL  Webhook auth test (status $($r.StatusCode))" -ForegroundColor Red
        $global:fail++
    }
}
catch {
    Write-Host "  FAIL  Webhook auth test (unreachable)" -ForegroundColor Red
    $global:fail++
}


Write-Host ""
Write-Host "Health Monitor" -ForegroundColor Yellow
Check "Health Status"   "http://127.0.0.1:8001/analytics/health-status"