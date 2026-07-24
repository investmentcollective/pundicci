@echo off
cd /d "%~dp0"
echo.
echo  PIC Dashboard - Publishing to GitHub...
echo.
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
