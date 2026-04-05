@echo off
chcp 65001 > nul

set VENV_DIR=.venv

echo ========================================
echo Запуск API
echo ========================================

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [ОШИБКА] Виртуальное окружение не найдено.
  echo Сначала запустите setup_windows.bat
  pause
  exit /b 1
)

call %VENV_DIR%\Scripts\activate.bat
if errorlevel 1 (
  echo [ОШИБКА] Не удалось активировать виртуальное окружение.
  echo Запустите setup_windows.bat повторно.
  pause
  exit /b 1
)

echo Запускаю сервер...
echo Откройте в браузере: http://127.0.0.1:8000
python -m uvicorn app.main:app --reload
