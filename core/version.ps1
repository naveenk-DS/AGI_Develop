# Check current version info
$ProductDir = "F:\naveen\AGI_Start"
Set-Location $ProductDir

$commit = git rev-parse --short HEAD
$branch = git branch --show-current
$tag = git describe --tags --abbrev=0 2>$null
$date = git log -1 --format="%ci"

Write-Host "=== AGI_Start Version Info ===" -ForegroundColor Cyan
Write-Host "Tag:     $tag"     -ForegroundColor Green
Write-Host "Branch:  $branch"  -ForegroundColor Green
Write-Host "Commit:  $commit"  -ForegroundColor Green
Write-Host "Date:    $date"    -ForegroundColor Green