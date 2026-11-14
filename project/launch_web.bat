@echo off
REM EchoAction AI - Web App Launcher
REM Run as web app:    launch_web.bat
REM Run as desktop app: launch_desktop.bat

cd /d "%~dp0"
echo Starting EchoAction AI on http://127.0.0.1:5003
python app.py
pause
