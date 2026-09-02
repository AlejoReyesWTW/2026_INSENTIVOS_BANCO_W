@echo off
REM Reinstala el entorno del proyecto desde cero.
REM Borra .venv, lo recrea y reinstala requirements.txt silenciando alertas.
REM Doble click desde el explorador, o ejecutar desde la terminal.

setlocal

cd /d "%~dp0"

echo [1/4] Eliminando venv anterior...
if exist ".venv" (
    rmdir /s /q ".venv"
) else (
    echo       .venv no existe, saltando.
)

echo [2/4] Creando venv nuevo...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] No se pudo crear el venv. ¿Esta Python en el PATH?
    pause
    exit /b 1
)

echo [3/4] Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip --disable-pip-version-check -q

echo [4/4] Instalando dependencias desde requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check --no-cache-dir -q
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion. Revisa requirements.txt o tu conexion.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Entorno reinstalado OK.
echo   Para arrancar la UI:  run.bat
echo ============================================
echo.
echo [Cerrando en 5 segundos...]
timeout /t 5

endlocal
