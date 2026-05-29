# PIC Dashboard — Push to GitHub
# Double-click this file any time you want to publish updates

$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $folder

$timestamp = Get-Date -Format "dd MMM yyyy HH:mm"
$message = "Dashboard update — $timestamp"

git add .
git commit -m $message
git push origin main

Write-Host "`nPublished! Live at:" -ForegroundColor Green
Write-Host "https://investmentcollective.github.io/pundicci/PIC_Dashboard.html" -ForegroundColor Cyan
Start-Sleep -Seconds 3
