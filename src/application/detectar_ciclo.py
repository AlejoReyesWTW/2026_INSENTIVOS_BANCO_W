"""Caso de uso: detectar el ciclo (mes/año) del nombre del archivo SOY PREVENIDO.

Es un wrapper delgado sobre `domain.ciclo.detectar_periodo_de_filename` que
añade manejo de errores con tipos del dominio.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.ciclo import Periodo, detectar_periodo_de_filename
from src.domain.errores import MesAnioNoDetectadoError


def detectar_ciclo(ruta_archivo: Path | str) -> Periodo:
    """Detecta el ciclo (mes/año) del nombre del archivo de insumo.

    Args:
        ruta_archivo: ruta al archivo SOY PREVENIDO (Path o str).

    Returns:
        Periodo con mes (siempre) y año (opcional, según el filename).

    Raises:
        MesAnioNoDetectadoError: si no se detecta ningún mes en el nombre.
    """
    nombre = Path(ruta_archivo).name
    periodo = detectar_periodo_de_filename(nombre)
    if periodo is None:
        raise MesAnioNoDetectadoError(
            f"No se pudo detectar mes/año del nombre del archivo: {nombre!r}. "
            "Asegúrate de que el nombre incluya un mes válido (enero, febrero, etc.)."
        )
    return periodo
