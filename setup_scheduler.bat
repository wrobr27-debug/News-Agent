@echo off
echo ========================================
echo   Bilaspur News Agent -- Scheduler Setup
echo ========================================
echo.
echo This must be Run as Administrator.
echo Right-click this file and select "Run as administrator"
echo.

set "SCRIPT_DIR=%~dp0"
set "PYTHON_CMD=python"
set "MAIN_SCRIPT=%SCRIPT_DIR%src\main.py"

echo Creating task: BilaspurNewsAgent (daily at 8:00 AM)...
schtasks /create /tn "BilaspurNewsAgent" /tr "%PYTHON_CMD% \"%MAIN_SCRIPT%\" --social" /sc daily /st 08:00 /f /rl HIGHEST

echo.
echo Creating task: BilaspurNewsDashboard (runs continuously on system startup)...
schtasks /create /tn "BilaspurNewsDashboard" /tr "%PYTHON_CMD% \"%MAIN_SCRIPT%\" dashboard" /sc ONSTART /f /rl HIGHEST /ru "SYSTEM"

echo.
echo Done! Tasks created.
echo.
echo To test: Run the following in PowerShell:
echo   Start-ScheduledTask -TaskName "BilaspurNewsAgent"
echo   Start-ScheduledTask -TaskName "BilaspurNewsDashboard"
echo.
pause
