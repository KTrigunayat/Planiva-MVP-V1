@echo off
echo 🎉 Event Planning Agent v2 - Streamlit GUI
echo ==========================================

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies if needed
echo 📦 Checking dependencies...
pip install -r requirements.txt --quiet

REM Start the application
echo 🚀 Starting Event Planning Agent v2 GUI...
echo.
echo 📱 The application will be available at:
echo    http://localhost:8501
echo.
echo 💡 Press Ctrl+C to stop the server
echo ==========================================
echo.

python -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0

pause