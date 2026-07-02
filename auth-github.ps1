# PIC Dashboard — GitHub One-Time Authentication
# Run this once whenever you need to set or update your Personal Access Token
# Get a token at: https://github.com/settings/tokens (needs 'repo' + 'workflow' scopes)

$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $folder

Write-Host ""
Write-Host "PIC Dashboard — GitHub Authentication" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Need a token? Go to: https://github.com/settings/tokens" -ForegroundColor Yellow
Write-Host "Click 'Generate new token (classic)', tick 'repo' and 'workflow', generate and copy." -ForegroundColor Yellow
Write-Host ""

$token = Read-Host "Paste your Personal Access Token"
$token = $token.Trim()

if ($token -eq "") {
    Write-Host "No token entered. Exiting." -ForegroundColor Red
    Start-Sleep 3
    exit
}

# Save token into remote URL
git remote set-url origin "https://investmentcollective:$token@github.com/investmentcollective/pundicci.git"

Write-Host ""
Write-Host "Token saved. Committing and pushing now..." -ForegroundColor Green
Write-Host ""

git add .
$timestamp = Get-Date -Format "dd MMM yyyy HH:mm"
git commit -m "Dashboard update — $timestamp"

$pushResult = git push origin main 2>&1
Write-Host $pushResult

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All done! Live at:" -ForegroundColor Green
    Write-Host "https://investmentcollective.github.io/pundicci/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "From now on just double-click push.bat to publish updates." -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "Push failed. Check your token has 'repo' and 'workflow' scopes." -ForegroundColor Red
    Write-Host "Regenerate at: https://github.com/settings/tokens" -ForegroundColor Yellow
}

Write-Host ""
Start-Sleep -Seconds 5
