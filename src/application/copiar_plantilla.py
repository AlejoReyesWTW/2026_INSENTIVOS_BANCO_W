"""Caso de uso: copiar la plantilla de salida al directorio de destino.

Wrapper sobre `infrastructure.excel_writer.copiar_plantilla` que:
1. Crea el directorio de salida si no existe.
2. Construye la ruta de destino combinando directorio + nombre de archivo.
3. Delega la copia a infrastructure.
"""

from __future__ import annotations

from pathlib import Path

from src.infrastructure.excel_writer import copiar_plantilla


def copiar_plantilla_a_salida(
    plantilla: Path | str,
    directorio_salida: Path | str,
    nombre_archivo: str,
) -> Path:
    """Copia la plantilla al directorio de salida con el nombre dado.

    Args:
        plantilla: ruta del archivo plantilla origen.
        directorio_salida: carpeta donde se copiará (se crea si no existe).
        nombre_archivo: nombre del archivo destino (ej: "base_incentivos_junio_2026.xlsx").

    Returns:
        La ruta completa del archivo destino.
    """
    directorio = Path(directorio_salida)
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / nombre_archivo
    return copiar_plantilla(plantilla, destino)
