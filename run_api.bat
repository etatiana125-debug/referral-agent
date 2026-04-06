@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Pinterest Referral Agent - Run API
echo ========================================

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: .venv is not found.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

echo Starting server...
echo Open in browser: http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload
if errorlevel 1 (
  echo.
  echo ERROR: Server stopped with an error.
  pause
  exit /b 1
)

exit /b 0
