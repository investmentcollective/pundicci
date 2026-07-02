# PIC Dashboard — GitHub Authentication Setup
# Run this ONCE to save your Personal Access Token and push everything up
# After this, just use push.ps1 for all future updates

$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $folder

Write-Host ""
Write-Host "PIC Dashboard — GitHub Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You need a GitHub Personal Access Token with 'repo' and 'workflow' scopes." -ForegroundColor Yellow
Write-Host "Get one at: https://github.com/settings/tokens" -ForegroundColor Yellow
Write-Host ""

$token = Read-Host "Paste your Personal Access Token here"
$token = $token.Trim()

if ($token -eq "") {
    Write-Host "No token entered. Exiting." -ForegroundColor Red
    Start-Sleep 3
    exit
}

# Save token into git remote URL
$remoteUrl = "https://investmentcollective:$token@github.com/investmentcollective/pundicci.git"
git remote set-url origin $remoteUrl

Write-Host ""
Write-Host "Token saved. Committing and pushing all files..." -ForegroundColor Green

git add .
$timestamp = Get-Date -Format "dd MMM yyyy HH:mm"
git commit -m "Dashboard update — $timestamp" 2>&1

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Green
$result = git push origin main 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! Dashboard is live at:" -ForegroundColor Green
    Write-Host "https://investmentcollective.github.io/pundicci/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Future updates: just double-click push.ps1" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "Push failed. Error details:" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  - Make sure your token has 'repo' AND 'workflow' scopes" -ForegroundColor Yellow
    Write-Host "  - Regenerate at https://github.com/settings/tokens" -ForegroundColor Yellow
}

Write-Host ""
Start-Sleep -Seconds 5
