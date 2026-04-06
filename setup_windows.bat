@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Pinterest Referral Agent - Windows Setup
echo ========================================

echo [1/5] Check Python in PATH...
python --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python is not found in PATH.
  echo Install Python 3.11+ and enable "Add Python to PATH".
  pause
  exit /b 1
)

echo [2/5] Create .venv if missing...
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

echo [3/5] Upgrade pip in .venv...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: Failed to upgrade pip in .venv
  pause
  exit /b 1
)

echo [4/5] Install dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Failed to install dependencies.
  pause
  exit /b 1
)

echo [5/5] Setup done.
echo Next: run run_api.bat
pause
exit /b 0
