@echo off
REM ============================================================
REM  Compilar la app de Incentivos Banco W a un .exe
REM  Genera la estructura de distribucion en la carpeta "dist"
REM  - Destino del exe: dist/
REM  - Plantilla y logo van DENTRO del exe (recursos --add-data)
REM  - Fuera del exe SOLO (editables por la operacion):
REM      Configuracion.json
REM      Base_Comisiones_Insentivos.xlsx   (tabla de incentivos)
REM      Correccion_nombres_base_subgerentes.xlsx  (nombres a corregir)
REM ============================================================
chcp 65001 >nul
setlocal

echo.
echo === Compilando Control de Incentivos a .exe ===
echo.

REM 1. Activar el entorno virtual
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] No se encontro .venv. Ejecute primero: python -m venv .venv
    pause
    exit /b 1
)

REM 2. Instalar dependencias (si hace falta)
echo [1/4] Asegurando dependencias...
pip install --quiet pyinstaller customtkinter openpyxl pillow darkdetect et_xmlfile packaging
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

REM 3. Compilar con PyInstaller (un solo archivo, sin consola)
echo [2/4] Compilando main.py (esto puede tardar 1-3 minutos)...
REM  --add-data "ORIGEN;DESTINO"  incrusta la plantilla y el logo DENTRO del exe.
REM  --icon "IMG\logo.ico"        usa el logo como icono del exe (no el de Python).
pyinstaller --noconfirm --clean --onefile --noconsole --name "Control Incentivos" ^
    --add-data "Insumos\Plantillas\Base incentivos - Soy Prevenido.xlsx;Insumos\Plantillas" ^
    --add-data "IMG\logo.ico;IMG" ^
    --add-data "IMG\imagen (1).png;IMG" ^
    --icon "IMG\logo.ico" ^
    main.py
if errorlevel 1 (
    echo [ERROR] Fallo la compilacion de PyInstaller.
    pause
    exit /b 1
)

REM 4. Copiar SOLO los datos editables del usuario al lado del exe.
echo [3/4] Copiando datos editables al lado del exe...
copy /y "Configuracion.json" "dist\Configuracion.json" >nul
copy /y "Base_Comisiones_Insentivos.xlsx" "dist\Base_Comisiones_Insentivos.xlsx" >nul
if exist "Correccion_nombres_base_subgerentes.xlsx" (
    copy /y "Correccion_nombres_base_subgerentes.xlsx" "dist\Correccion_nombres_base_subgerentes.xlsx" >nul
)

echo.
echo [4/4] COMPILACION COMPLETA.
echo.
echo El ejecutable quedo en:  dist\Control Incentivos.exe
echo Junto a el estan SOLO los datos editables:
echo   - Configuracion.json
echo   - Base_Comisiones_Insentivos.xlsx   (incentivos: la operacion puede cambiarlos)
echo   - Correccion_nombres_base_subgerentes.xlsx  (si agregan nombres aqui,
echo      el proceso los aplica en cada ciclo; no hace falta recompilar)
echo La plantilla y el logo viajan DENTRO del exe.
echo Al ejecutarlo se crean:  logs_automatizacion\  y  salidas\<anio>\<mes>\<dia>\
echo.
echo Para PROBAR: doble clic en "dist\Control Incentivos.exe"
echo.
pause
endlocal