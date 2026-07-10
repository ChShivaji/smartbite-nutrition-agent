@echo off
title SmartBite AI Nutrition Agent Startup
echo ===================================================
echo   Starting SmartBite AI Nutrition Agent...
echo ===================================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b
)

:: Try creating/activating virtual environment using uv or standard venv
echo Setting up environment...
if exist .venv (
    echo Virtual environment (.venv) already exists.
) else (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ===================================================
echo   SmartBite is ready!
echo   Launching local server on http://localhost:5000
echo   Press Ctrl+C in this terminal to stop.
echo ===================================================
echo.

python app.py
pause
