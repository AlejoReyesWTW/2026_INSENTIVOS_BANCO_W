"""Mapeo de columnas entre archivos origen y destino.

El mapeo se hace por NOMBRE de columna (no por letra) para ser robusto
ante cambios de layout en los archivos de insumo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def normalizar_header(nombre: str | None) -> str:
    """Normaliza un nombre de columna para comparación robusta.

    Pasos:
        1. Si es None o vacío, retorna "".
        2. Quita acentos (NFD + filtro de marcas).
        3. Convierte a lowercase.
        4. strip() al inicio y final.
        5. Colapsa separadores (espacios y underscores repetidos) en un solo espacio.

    Ejemplos:
        >>> normalizar_header("Código_Agencia")
        'codigo agencia'
        >>> normalizar_header("  CEDULA     ")
        'cedula'
        >>> normalizar_header("Cédula")
        'cedula'
    """
    if not nombre:
        return ""
    # Descomponer caracteres con acento (NFD separa la base de la marca).
    sin_acentos = "".join(
        c
        for c in unicodedata.normalize("NFD", nombre)
        if unicodedata.category(c) != "Mn"
    )
    normalizado = sin_acentos.lower().strip()
    # Colapsar espacios y underscores repetidos en un solo espacio.
    normalizado = re.sub(r"[\s_]+", " ", normalizado)
    return normalizado


@dataclass(frozen=True)
class MapeoColumnas:
    """Define cómo una columna de un archivo origen se mapea a una destino.

    La comparación se hace por nombre NORMALIZADO (sin acentos, lowercase,
    sin espacios extra) para ser robusto ante variaciones tipográficas.
    """

    origen: str  # nombre lógico de la columna en el archivo origen
    destino: str  # nombre lógico de la columna en el archivo destino

    def match_normalizado(self, header_leido: str | None) -> bool:
        """Retorna True si `header_leido` (normalizado) coincide con el origen.

        Args:
            header_leido: nombre tal como aparece en el archivo origen.
        """
        return normalizar_header(self.origen) == normalizar_header(header_leido)
