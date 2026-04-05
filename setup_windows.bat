@echo off
chcp 65001 > nul

set VENV_DIR=.venv

echo ========================================
echo Настройка проекта для Windows
echo ========================================

echo [1/4] Проверяю Python...
python --version
if errorlevel 1 (
  echo [ОШИБКА] Python не найден.
  echo Установите Python 3.11+ и включите опцию "Add Python to PATH".
  pause
  exit /b 1
)

echo [2/4] Создаю виртуальное окружение %VENV_DIR%...
if exist "%VENV_DIR%\Scripts\python.exe" (
  echo Виртуальное окружение уже существует.
) else (
  python -m venv %VENV_DIR%
  if errorlevel 1 (
    echo [ОШИБКА] Не удалось создать виртуальное окружение.
    pause
    exit /b 1
  )
)

echo [3/4] Активирую виртуальное окружение...
call %VENV_DIR%\Scripts\activate.bat
if errorlevel 1 (
  echo [ОШИБКА] Не удалось активировать виртуальное окружение.
  pause
  exit /b 1
)

echo [4/4] Устанавливаю зависимости...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo [ОШИБКА] Не удалось установить зависимости.
  echo Проверьте интернет и настройки прокси, затем запустите setup_windows.bat снова.
  pause
  exit /b 1
)

echo.
echo Готово! Теперь запустите run_api.bat
pause
