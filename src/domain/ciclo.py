"""Periodo (mes, año) del ciclo de incentivos y parser de filenames."""

from __future__ import annotations

import re
from dataclasses import dataclass


# Meses completos y abreviados en español (lowercase).
MESES_COMPLETOS: set[str] = {
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
}

MESES_ABREVIADOS: dict[str, str] = {
    "ene": "enero",
    "feb": "febrero",
    "mar": "marzo",
    "abr": "abril",
    "may": "mayo",
    "jun": "junio",
    "jul": "julio",
    "ago": "agosto",
    "sep": "septiembre",
    "set": "septiembre",  # variante en español rioplatense
    "oct": "octubre",
    "nov": "noviembre",
    "dic": "diciembre",
}

# Todas las variantes válidas para el regex (ordenadas por longitud desc).
_VARIANTES_MES: tuple[str, ...] = tuple(
    sorted(
        (*MESES_COMPLETOS, *MESES_ABREVIADOS.keys()),
        key=len,
        reverse=True,
    )
)

# Regex: captura mes (cualquier variante) + año opcional (2 o 4 dígitos).
# Usamos lookarounds explícitos en lugar de \b para que "_" sea tratado
# como separador válido (los nombres de archivo lo usan).
_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9])(" + "|".join(_VARIANTES_MES) + r")(?![a-zA-Z0-9])"
    r"(?:[\s\-_/]*(\d{2,4}))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Periodo:
    """Representa el periodo (mes, año) de un ciclo de incentivos.

    El año es opcional porque algunos filenames solo incluyen el mes.
    """

    mes: str
    anio: int | None = None

    def __str__(self) -> str:
        if self.anio is not None:
            return f"{self.mes} {self.anio}"
        return self.mes


def _normalizar_mes(mes_raw: str) -> str | None:
    """Normaliza una variante de mes a su nombre completo en lowercase.

    Retorna None si la variante no es válida.
    """
    mes_lower = mes_raw.lower()
    if mes_lower in MESES_COMPLETOS:
        return mes_lower
    if mes_lower in MESES_ABREVIADOS:
        return MESES_ABREVIADOS[mes_lower]
    return None


def _parsear_anio(anio_raw: str | None) -> int | None:
    """Convierte el string de año capturado a int.

    Años de 2 dígitos se interpretan como 20XX (rango 2000-2099).
    Si el string no es un entero válido, retorna None.
    """
    if anio_raw is None:
        return None
    try:
        anio_int = int(anio_raw)
    except ValueError:
        return None
    if anio_int < 100:
        return 2000 + anio_int
    return anio_int


def detectar_periodo_de_filename(filename: str) -> Periodo | None:
    """Detecta mes y año del ciclo desde el nombre de un archivo.

    Acepta variantes comunes:
        - "Base incentivos junio 2026 - Soy Prevenido.xlsx"
        - "SOY PREVENIDO JUN 2026.xlsx"
        - "Base junio-2026.xlsx"
        - "archivo FEBRERO.xlsx" (sin año → mes detectado, año=None)

    Returns:
        Periodo con mes (siempre) y año (opcional). None si no detecta mes.
    """
    match = _PATTERN.search(filename)
    if match is None:
        return None

    mes = _normalizar_mes(match.group(1))
    if mes is None:
        return None

    anio = _parsear_anio(match.group(2))
    return Periodo(mes=mes, anio=anio)
