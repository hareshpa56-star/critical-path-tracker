@echo off
:: Kill any existing server on port 8080
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
:: Start the server
cd /d "%~dp0"
python server.py
