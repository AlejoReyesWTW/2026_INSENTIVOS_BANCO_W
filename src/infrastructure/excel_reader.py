"""Lector de archivos Excel (.xlsx) para el pipeline de incentivos.

Lee hojas de un .xlsx y devuelve los datos como lista de diccionarios.
Los encabezados se normalizan (lowercase, sin acentos, sin espacios extra)
para hacer el cruce por nombre robusto ante variaciones tipográficas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import openpyxl

from src.domain.errores import ArchivoNoEncontradoError, HojaFaltanteError
from src.domain.mapeo import normalizar_header


class ExcelReader:
    """Encapsula la lectura de un archivo .xlsx."""

    def __init__(self, ruta: Path | str) -> None:
        self.ruta = Path(ruta)
        if not self.ruta.exists():
            raise ArchivoNoEncontradoError(
                f"No se encontró el archivo Excel: {self.ruta}"
            )
        # read_only=True evita warnings de openpyxl por celdas fecha malformadas
        # y mejora performance. data_only=True evalúa fórmulas a sus valores.
        self._workbook = openpyxl.load_workbook(
            self.ruta, read_only=True, data_only=True
        )

    def listar_hojas(self) -> list[str]:
        """Devuelve los nombres de las hojas del archivo."""
        return list(self._workbook.sheetnames)

    def leer_hoja(
        self,
        nombre_hoja: str,
        fila_encabezado: int = 1,
        normalizar: bool = True,
    ) -> list[dict[str, Any]]:
        """Lee una hoja y devuelve los datos como lista de diccionarios.

        Args:
            nombre_hoja: nombre de la hoja a leer.
            fila_encabezado: número de fila (1-based) donde están los encabezados.
            normalizar: si True, normaliza los headers (lowercase, sin acentos, etc.).

        Returns:
            Lista de dicts, uno por fila de datos (excluyendo encabezado).
            Cada dict tiene keys = headers (normalizados si normalizar=True).

        Raises:
            HojaFaltanteError: si la hoja no existe en el archivo.
        """
        if nombre_hoja not in self._workbook.sheetnames:
            raise HojaFaltanteError(
                f"No existe la hoja '{nombre_hoja}' en {self.ruta}. "
                f"Hojas disponibles: {self._workbook.sheetnames}"
            )

        hoja = self._workbook[nombre_hoja]
        encabezados = self._leer_encabezados_crudos(hoja, fila_encabezado, normalizar)

        # Leer filas de datos (a partir de fila_encabezado + 1).
        filas_datos: list[dict[str, Any]] = []
        for fila_tuple in hoja.iter_rows(
            min_row=fila_encabezado + 1,
            values_only=True,
        ):
            # Saltar filas completamente vacías.
            if all(v is None for v in fila_tuple):
                continue
            fila_dict: dict[str, Any] = {}
            for idx, header in enumerate(encabezados):
                if not header:
                    continue  # Columna sin encabezado, se ignora.
                if idx < len(fila_tuple):
                    fila_dict[header] = fila_tuple[idx]
            filas_datos.append(fila_dict)

        return filas_datos

    def leer_encabezados(
        self,
        nombre_hoja: str,
        fila_encabezado: int = 1,
        normalizar: bool = True,
    ) -> list[str]:
        """Lee solo los encabezados de una hoja (sin las filas de datos).

        Útil para validar estructura sin cargar todas las filas.

        Args:
            nombre_hoja: nombre de la hoja.
            fila_encabezado: número de fila (1-based) donde están los encabezados.
            normalizar: si True, normaliza los headers.

        Returns:
            Lista de strings con los nombres de las columnas (normalizados si aplica).
            Columnas vacías o None se omiten.

        Raises:
            HojaFaltanteError: si la hoja no existe.
        """
        if nombre_hoja not in self._workbook.sheetnames:
            raise HojaFaltanteError(
                f"No existe la hoja '{nombre_hoja}' en {self.ruta}. "
                f"Hojas disponibles: {self._workbook.sheetnames}"
            )
        hoja = self._workbook[nombre_hoja]
        return self._leer_encabezados_crudos(hoja, fila_encabezado, normalizar)

    def _leer_encabezados_crudos(
        self,
        hoja,
        fila_encabezado: int,
        normalizar: bool,
    ) -> list[str]:
        """Helper interno: lee la fila de encabezados y aplica normalización."""
        try:
            fila_tuple = next(
                hoja.iter_rows(
                    min_row=fila_encabezado,
                    max_row=fila_encabezado,
                    values_only=True,
                )
            )
        except StopIteration:
            return []
        encabezados_crudos = [
            str(v).strip() if v is not None else "" for v in fila_tuple
        ]
        if not normalizar:
            return encabezados_crudos
        return [normalizar_header(h) for h in encabezados_crudos]

    def cerrar(self) -> None:
        """Cierra el workbook (libera el handle del archivo)."""
        self._workbook.close()
