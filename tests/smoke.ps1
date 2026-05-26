Write-Host "=== AGI_Start Smoke Test ===" -ForegroundColor Cyan

$pass = 0
$fail = 0

function Check($name, $url, $method = "GET") {
    try {
        if ($method -eq "GET") {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        } else {
            $r = Invoke-WebRequest -Uri $url -Method POST -UseBasicParsing -TimeoutSec 5
        }
        if ($r.StatusCode -eq 200) {
            Write-Host "  PASS  $name" -ForegroundColor Green
            $global:pass++
        } else {
            Write-Host "  FAIL  $name (status $($r.StatusCode))" -ForegroundColor Red
            $global:fail++
        }
    } catch {
        Write-Host "  FAIL  $name (unreachable)" -ForegroundColor Red
        $global:fail++
    }
}

Check "FastAPI Health"     "http://127.0.0.1:8001/health"
Check "Ollama"             "http://127.0.0.1:11434/api/tags"
Check "Qdrant"             "http://127.0.0.1:6333/healthz"
Check "n8n"                "http://127.0.0.1:5678/healthz"
Check "Dashboard"          "http://127.0.0.1:8001/dashboard/"
Check "Agent tools"        "http://127.0.0.1:8001/agent/tools"
Check "Backup list"        "http://127.0.0.1:8001/backup/list"
Check "License status"     "http://127.0.0.1:8001/license/status"

Write-Host ""
Write-Host "Result: $pass passed, $fail failed" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Red" })

if ($fail -eq 0) {
    Write-Host "All systems operational." -ForegroundColor Green
} else {
    Write-Host "Fix failing services before continuing." -ForegroundColor Red
}