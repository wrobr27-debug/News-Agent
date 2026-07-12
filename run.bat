@echo off
chcp 65001 >nul
cd /d "%~dp0"
python src\main.py %*
if %ERRORLEVEL% NEQ 0 pause
