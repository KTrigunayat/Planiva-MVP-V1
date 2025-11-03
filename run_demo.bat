@echo off
echo 🎉 Event Planning Agent v2 - Complete Demo
echo ==========================================
echo.
echo This will run the complete Event Planning Agent v2 system
echo with Priya & Rohit's wedding data and display all functionalities.
echo.
echo 📋 What this demo will show:
echo    ✓ Multi-agent AI system in action
echo    ✓ Real-time progress tracking
echo    ✓ Intelligent vendor matching
echo    ✓ Automated combination scoring  
echo    ✓ Comprehensive blueprint generation
echo    ✓ Multi-format export capabilities
echo.
echo ⏳ Starting demo... (This may take a few minutes)
echo.

REM Change to script directory
cd /d "%~dp0"

REM Run the complete demo
python run_complete_demo.py

echo.
echo 🎊 Demo finished! Check the generated files for Priya & Rohit's wedding plan.
echo.
pause