@echo off
REM Complete Event Management Platform Demo Runner
REM This script runs the complete demo showcasing Event Planning, CRM, and Task Management

echo ========================================
echo Complete Event Management Platform Demo
echo ========================================
echo.
echo This demo will showcase:
echo   1. Event Planning - AI-powered vendor sourcing
echo   2. CRM - Client communication management
echo   3. Task Management - Task tracking and coordination
echo.
echo Using client data from: streamlit_gui/client_data.json
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Running demo...
echo.

REM Run the demo
python demo_complete_platform.py

echo.
echo ========================================
echo Demo execution completed
echo ========================================
echo.
echo To explore the platform interactively:
echo   1. Start the backend API (if not running)
echo   2. Run: streamlit run streamlit_gui/app.py
echo.

pause
