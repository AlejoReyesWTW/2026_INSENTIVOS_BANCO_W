"""Constantes de la UI (colores, paths)."""

from __future__ import annotations

from pathlib import Path

# Colores del tema WTW.
COLOR_WTW = "#FF6900"
COLOR_WTW_HOVER = "#00A3AD"
COLOR_WTW_SECONDARY = "#9ca3af"  # Gris para estados deshabilitados / secundarios
COLOR_FONDO = "#ffffff"
COLOR_WHITE = "#ffffff"  # Blanco puro (alias de FONDO)
COLOR_PANEL = "#202027"
COLOR_PANEL_2 = "#292931"
COLOR_TEXTO = "#1F7797"
COLOR_TEXTO_SECUNDARIO = "#181818"
COLOR_OK = "#22C55E"
COLOR_WARNING = "#F59E0B"
COLOR_ERROR = "#EF4444"
COLOR_DESHABILITADO = "#7F33CF"

# Colores para el estilo claro de los inputs.
COLOR_INPUT_BG = "#ffffff"  # Fondo blanco del input
COLOR_INPUT_BORDER = "#d0d0d0"  # Borde gris claro
COLOR_INPUT_TEXT = "#181818"  # Texto oscuro
COLOR_LABEL_HINT = "#dc2626"  # Rojo para labels de "Por favor proporcione..."

# Paths del proyecto (asumiendo que se ejecuta desde la raíz).
RUTA_BASE = Path(__file__).resolve().parent.parent.parent
RUTA_CONFIG = RUTA_BASE / "Configuracion.json"
RUTA_PLANTILLA = (
    RUTA_BASE / "Insumos" / "Plantillas" / "Base incentivos - Soy Prevenido.xlsx"
)
RUTA_SALIDA = RUTA_BASE / "Insumos" / "Salida"
RUTA_LOGS = RUTA_BASE / "Logs"

# Tamaño de la ventana principal.
ANCHO_VENTANA = 1100
ALTO_VENTANA = 700
