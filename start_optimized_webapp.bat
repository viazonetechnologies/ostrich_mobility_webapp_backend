@echo off
echo ========================================
echo OSTRICH WEBAPP - OPTIMIZED VERSION
echo ========================================
echo Starting optimized webapp backend...

REM Set environment variables
set FLASK_ENV=development
set PORT=8000

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install/upgrade requirements
echo Installing requirements...
pip install flask flask-cors PyJWT pymysql pillow python-dotenv

REM Start the optimized application
echo.
echo Starting optimized Flask application on port %PORT%...
echo Performance optimizations enabled:
echo - Database connection pooling: ENABLED
echo - Query result caching: ENABLED  
echo - Background cleanup: ENABLED
echo - Fallback database support: ENABLED
echo.

REM Start server
python app_optimized.py

echo.
echo Webapp is running at: http://localhost:%PORT%
echo Performance stats: http://localhost:%PORT%/api/v1/performance/stats
echo.
pause