@echo off
cd /d "%~dp0"
echo.
echo  PIC Dashboard - Publishing to GitHub...
echo.

echo  Step 1: Processing bet log...
python process_bets.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  process_bets.py failed. Check Python is installed (python --version).
    echo  Install openpyxl if missing: pip install openpyxl
    echo.
    pause
    exit /b 1
)

echo.
echo  Step 2: Committing and pushing...
git add .
git commit -m "Dashboard update"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  Published! Live at:
    echo  https://investmentcollective.github.io/pundicci/
) else (
    echo.
    echo  Push failed. Token may have expired.
    echo  Run auth-github.bat to set a new token.
)

echo.
pause
