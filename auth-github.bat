@echo off
cd /d "%~dp0"
echo.
echo  PIC Dashboard - GitHub Setup
echo  =============================
echo.
echo  You need a GitHub Personal Access Token.
echo  Get one at: https://github.com/settings/tokens
echo  (Classic token, tick repo + workflow scopes)
echo.
set /p TOKEN= Paste your token here and press Enter:

if "%TOKEN%"=="" (
    echo No token entered. Exiting.
    pause
    exit /b
)

echo.
echo  Clearing any stale lock files...
del /f /q "%~dp0.git\HEAD.lock" 2>nul
del /f /q "%~dp0.git\index.lock" 2>nul
del /f /q "%~dp0.git\objects\maintenance.lock" 2>nul

echo  Saving token and pushing...
echo.

git remote set-url origin "https://investmentcollective:%TOKEN%@github.com/investmentcollective/pundicci.git"

git add .
git commit -m "Dashboard update"
git push --force origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  SUCCESS! Live at:
    echo  https://investmentcollective.github.io/pundicci/
    echo.
    echo  Future updates: just double-click push.bat
) else (
    echo.
    echo  Push failed. Make sure your token has repo + workflow scopes.
    echo  Regenerate at: https://github.com/settings/tokens
)

echo.
pause
