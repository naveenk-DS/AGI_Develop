Write-Host "=== NAVIX Smoke Test ===" -ForegroundColor Cyan

$pass = 0
$fail = 0

function Check($name, $url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
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

Write-Host ""
Write-Host "Core Services" -ForegroundColor Yellow
Check "FastAPI Health"     "http://127.0.0.1:8001/health"
Check "Ollama"             "http://127.0.0.1:11434/api/tags"
Check "Qdrant"             "http://127.0.0.1:6333/healthz"

Write-Host ""
Write-Host "NAVIX Endpoints" -ForegroundColor Yellow
Check "Dashboard"          "http://127.0.0.1:8001/dashboard/"
Check "Agent tools"        "http://127.0.0.1:8001/agent/tools"
Check "NAVIX status"       "http://127.0.0.1:8001/navix/status"
Check "News headlines"     "http://127.0.0.1:8001/navix/news/headlines"
Check "World context"      "http://127.0.0.1:8001/navix/world/context"

Write-Host ""
Write-Host "Result: $pass passed, $fail failed" -ForegroundColor $(if ($fail -eq 0) {"Green"} else {"Red"})