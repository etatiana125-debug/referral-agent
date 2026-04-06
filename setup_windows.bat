@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Setup for Referral Content Agent
echo ========================================

echo [1/6] Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python is not found in PATH.
  echo Install Python 3.11+ and enable "Add Python to PATH".
  pause
  exit /b 1
)

echo [2/6] Creating virtual environment (.venv)...
if exist ".venv\Scripts\python.exe" (
  echo .venv already exists.
) else (
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create .venv
    pause
    exit /b 1
  )
)

echo [3/6] Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo ERROR: Failed to activate .venv
  pause
  exit /b 1
)

echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: Failed to upgrade pip
  pause
  exit /b 1
)

echo [5/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Failed to install dependencies from requirements.txt
  pause
  exit /b 1
)

echo [6/6] Done.
echo Next step: run run_api.bat
pause
exit /b 0
