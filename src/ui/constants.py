"""Constantes de la UI (colores, paths)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from src.domain.ciclo import Periodo

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

# ----------------------------------------------------------------
# Estructura de carpetas de la SOLUCIÓN (raíz "incentivos")
#
#   incentivos/                     <- RUTA_RAIZ (carpeta del .exe)
#   ├── Base_Comisiones_Insentivos.xlsx   <- Excel editable (comisiones)
#   ├── Configuracion.json               <- config editable
#   ├── App.exe                          <- el ejecutable
#   ├── logs_automatizacion/             <- logs diarios (auditoría)
#   └── salidas/                         <- salidas fuera del exe
#       └── <año>/<mes>/<día>/           <- estructura por fecha
# ----------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Empaquetado (.exe): raíz = carpeta del ejecutable (datos del usuario).
    RUTA_RAIZ = Path(sys.executable).resolve().parent
    # Recursos internos del exe (plantilla, logo): _MEIPASS de PyInstaller.
    RUTA_INTERNA = Path(getattr(sys, "_MEIPASS", RUTA_RAIZ))
else:
    # En desarrollo: raíz del proyecto es la misma para datos y recursos.
    RUTA_RAIZ = Path(__file__).resolve().parent.parent.parent
    RUTA_INTERNA = RUTA_RAIZ

# Alias de compatibilidad (el logo vive dentro del proyecto).
RUTA_BASE = RUTA_RAIZ

# Datos del usuario (FUERA del exe, editables por la operación).
RUTA_CONFIG = RUTA_RAIZ / "Configuracion.json"
RUTA_COMISIONES = RUTA_RAIZ / "Base_Comisiones_Insentivos.xlsx"
RUTA_LOGS = RUTA_RAIZ / "logs_automatizacion"
RUTA_SALIDA_BASE = RUTA_RAIZ / "salidas"

# Recursos INTERNOS del exe (no editables, empaquetados).
RUTA_PLANTILLA = (
    RUTA_INTERNA / "Insumos" / "Plantillas" / "Base incentivos - Soy Prevenido.xlsx"
)
RUTA_LOGO_EXE = RUTA_INTERNA / "IMG" / "logo.ico"

# Tamaño de la ventana principal.
ANCHO_VENTANA = 1100
ALTO_VENTANA = 700


def ruta_salida_del_ciclo(periodo: Periodo | None = None) -> Path:
    """Carpeta de salida por fecha: salidas/<año>/<mes>/<día>.

    Si no se pasa un periodo, usa la fecha actual del sistema.
    """
    if periodo is not None and periodo.anio is not None:
        anio = periodo.anio
        mes_texto = periodo.mes
    else:
        hoy = date.today()
        anio = hoy.year
        mes_texto = _MESES[hoy.month]
    dia = str(date.today().day)
    return RUTA_SALIDA_BASE / str(anio) / mes_texto / dia


_MESES = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
