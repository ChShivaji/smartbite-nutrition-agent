@echo off
title SmartBite AI Nutrition Agent
echo ===================================================
echo   Starting SmartBite AI Nutrition Agent...
echo   Server will open on http://localhost:5000
echo ===================================================
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo ===================================================
    echo  ERROR: Server stopped or failed to start.
    echo  Check if Python is installed and in your PATH.
    echo ===================================================
)

echo.
echo Press any key to exit...
pause >nul
