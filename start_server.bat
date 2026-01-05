@echo off
echo Starting Ostrich Backend Server...
echo ================================

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set PORT=8000

echo Starting Flask server on port %PORT%...
echo Server will be available at: http://localhost:%PORT%
echo Press Ctrl+C to stop the server
echo.

python app.py

pause