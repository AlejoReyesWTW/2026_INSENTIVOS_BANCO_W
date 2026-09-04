"""Utilidades para manejo de archivos (Excel, paths, nombres únicos)."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def es_archivo_temporal(ruta: Path | str) -> bool:
    """Retorna True si el archivo es un temporal de Excel (~$ al inicio).

    Excel crea archivos como `~$archivo.xlsx` cuando otro proceso lo tiene
    abierto. Estos NO deben procesarse.

    Args:
        ruta: ruta (str o Path) al archivo a chequear.

    Returns:
        True si el nombre del archivo empieza con `~$`.
    """
    nombre = Path(ruta).name
    return nombre.startswith("~$")


def normalizar_nombre_archivo(nombre: str, minusculas: bool = False) -> str:
    """Normaliza un nombre de archivo para uso como nombre de archivo.

    Pasos:
        1. strip() al inicio y final.
        2. Quita acentos (NFD + filtro de marcas).
        3. Colapsa espacios múltiples en uno.
        4. Reemplaza espacios por underscores.
        5. Opcionalmente convierte a minúsculas.

    Args:
        nombre: nombre a normalizar.
        minusculas: si True, convierte a minúsculas.

    Returns:
        Nombre normalizado.
    """
    nombre = nombre.strip()
    # Quitar acentos.
    sin_acentos = "".join(
        c
        for c in unicodedata.normalize("NFD", nombre)
        if unicodedata.category(c) != "Mn"
    )
    # Colapsar espacios múltiples.
    colapsado = re.sub(r"\s+", " ", sin_acentos)
    # Reemplazar espacios por underscore.
    resultado = colapsado.replace(" ", "_")
    if minusculas:
        resultado = resultado.lower()
    return resultado


def generar_nombre_unico_si_existe(ruta: Path | str) -> Path:
    """Si la ruta ya existe, le agrega un timestamp al nombre.

    Útil para evitar sobrescribir archivos de salida de ciclos anteriores.

    Args:
        ruta: ruta propuesta para el archivo.

    Returns:
        La misma ruta si no existe, o una nueva ruta con timestamp si ya existe.
    """
    ruta_p = Path(ruta)
    if not ruta_p.exists():
        return ruta_p
    # Formato: archivo_YYYYMMDD_HHMMSS.ext
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nuevo_nombre = f"{ruta_p.stem}_{timestamp}{ruta_p.suffix}"
    return ruta_p.parent / nuevo_nombre
