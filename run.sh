#!/usr/bin/env bash
# Launcher del Panel WTW (Git Bash / WSL / Linux).
# Activa el venv del proyecto y arranca main.py con el Python correcto.

set -e

cd "$(dirname "$0")"

if [ ! -f ".venv/Scripts/python.exe" ] && [ ! -f ".venv/bin/python" ]; then
	echo "[ERROR] No se encontro el venv en .venv/"
	echo "        Crear con:  python -m venv .venv"
	echo "        Instalar:   .venv/bin/python -m pip install -r requirements.txt"
	exit 1
fi

# Windows (Git Bash / MSYS)
if [ -f ".venv/Scripts/activate" ]; then
	# shellcheck disable=SC1091
	source ".venv/Scripts/activate"
fi

python main.py
