@echo off
REM Launcher del Panel WTW.
REM Activa el venv del proyecto y arranca View/Panel.py con el Python correcto.
REM Doble click desde el explorador, o ejecutar desde la terminal.

setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el venv en ".venv\".
    echo         Crear con:  python -m venv .venv
    echo         Instalar:   .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python View\Panel.py

endlocal
