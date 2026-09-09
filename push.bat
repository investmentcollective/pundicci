@echo off
setlocal
cd /d "%~dp0"

echo.
echo  PIC Dashboard - Publishing to GitHub...
echo.

REM OneDrive sync can leave a stale lock behind after an interrupted git run
if exist ".git\index.lock" (
    echo  Clearing stale git lock...
    del /f /q ".git\index.lock" >nul 2>&1
    if exist ".git\index.lock" (
        echo.
        echo  COULD NOT REMOVE .git\index.lock
        echo  Close any open git tools / editors, pause OneDrive sync, then retry.
        goto :end
    )
)

echo  Staging changes...
git add -A
if errorlevel 1 goto :failed

REM "git diff --cached --quiet" returns 1 when there ARE staged changes
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Dashboard update"
    if errorlevel 1 goto :failed
    echo  Committed.
) else (
    echo  Nothing new to commit - pushing any existing commits.
)

echo  Pushing...
git push origin main
if errorlevel 1 goto :pushfailed

echo.
echo  Published. Live at:
echo  https://investmentcollective.github.io/pundicci/
echo  GitHub Pages takes about a minute to rebuild.
goto :end

:failed
echo.
echo  STOPPED - could not stage or commit.
echo  NOTHING has been published.
goto :end

:pushfailed
echo.
echo  Commit succeeded but the PUSH failed.
echo  Token may have expired - run auth-github.bat to set a new one.
goto :end

:end
echo.
pause
