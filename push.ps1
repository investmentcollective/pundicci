# PIC Dashboard — Publish to GitHub
# Double-click push.bat to run this (not this file directly)

$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $folder

$timestamp = Get-Date -Format "dd MMM yyyy HH:mm"
git add .
git commit -m "Dashboard update — $timestamp"
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Published! Live at:" -ForegroundColor Green
    Write-Host "https://investmentcollective.github.io/pundicci/" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Push failed — token may have expired." -ForegroundColor Red
    Write-Host "Run auth-github.bat to set a new token." -ForegroundColor Yellow
}

Write-Host ""
Start-Sleep -Seconds 4
