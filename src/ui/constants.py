"""Constantes de la UI (colores, paths)."""

from __future__ import annotations

from pathlib import Path

# Colores del tema WTW.
COLOR_WTW = "#FF6900"
COLOR_WTW_HOVER = "#00A3AD"
COLOR_FONDO = "#ffffff"
COLOR_PANEL = "#202027"
COLOR_PANEL_2 = "#292931"
COLOR_TEXTO = "#1F7797"
COLOR_TEXTO_SECUNDARIO = "#181818"
COLOR_OK = "#22C55E"
COLOR_WARNING = "#F59E0B"
COLOR_ERROR = "#EF4444"
COLOR_DESHABILITADO = "#7F33CF"

# Paths del proyecto (asumiendo que se ejecuta desde la raíz).
RUTA_BASE = Path(__file__).resolve().parent.parent.parent
RUTA_CONFIG = RUTA_BASE / "Configuracion.json"
RUTA_PLANTILLA = (
    RUTA_BASE / "Insumos" / "Plantillas" / "Base incentivos - Soy Prevenido.xlsx"
)
RUTA_SALIDA = RUTA_BASE / "Insumos" / "Salida"
RUTA_LOGS = RUTA_BASE / "Logs"

# Tamaño de la ventana principal.
ANCHO_VENTANA = 1050
ALTO_VENTANA = 650
