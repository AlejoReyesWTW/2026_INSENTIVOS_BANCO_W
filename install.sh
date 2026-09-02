#!/usr/bin/env bash
# Reinstala el entorno del proyecto desde cero (Git Bash / WSL / Linux).
# Borra .venv, lo recrea y reinstala requirements.txt silenciando alertas.

set -e

cd "$(dirname "$0")"

echo "[1/4] Eliminando venv anterior..."
rm -rf .venv

echo "[2/4] Creando venv nuevo..."
python -m venv .venv

echo "[3/4] Actualizando pip..."
".venv/Scripts/python.exe" -m pip install --upgrade pip --disable-pip-version-check -q

echo "[4/4] Instalando dependencias desde requirements.txt..."
".venv/Scripts/python.exe" -m pip install -r requirements.txt --disable-pip-version-check --no-cache-dir -q

echo ""
echo "============================================"
echo "  Entorno reinstalado OK."
echo "  Para arrancar la UI:  ./run.sh"
echo "============================================"
