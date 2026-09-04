"""Escritor de archivos Excel (.xlsx) para el pipeline de incentivos.

Copia plantillas, escribe datos e inserta fórmulas (BUSCARX, SI anidadas, etc.)
como texto para que Excel las evalúe al abrir.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import openpyxl

from src.domain.errores import ArchivoNoEncontradoError, HojaFaltanteError


def copiar_plantilla(origen: Path | str, destino: Path | str) -> Path:
    """Copia una plantilla .xlsx al destino (sobreescribe si existe).

    Args:
        origen: ruta del archivo plantilla origen.
        destino: ruta donde se copia la plantilla.

    Returns:
        La ruta de destino (Path).

    Raises:
        ArchivoNoEncontradoError: si la plantilla origen no existe.
    """
    origen_p = Path(origen)
    destino_p = Path(destino)
    if not origen_p.exists():
        raise ArchivoNoEncontradoError(
            f"No se encontró la plantilla origen: {origen_p}"
        )
    # shutil.copy2 preserva metadata; copy + overwrite.
    shutil.copy2(origen_p, destino_p)
    return destino_p


class ExcelWriter:
    """Encapsula la escritura de un archivo .xlsx.

    El archivo destino debe existir (se carga como plantilla).
    Usar copiar_plantilla() primero si se quiere empezar desde una plantilla base.
    """

    def __init__(self, ruta: Path | str) -> None:
        self.ruta = Path(ruta)
        if not self.ruta.exists():
            raise ArchivoNoEncontradoError(
                f"No se encontró el archivo Excel destino: {self.ruta}"
            )
        self._workbook = openpyxl.load_workbook(self.ruta)

    def escribir_datos(
        self,
        hoja: str,
        fila_inicio: int,
        datos: list[list[Any]],
    ) -> None:
        """Escribe filas de datos a partir de fila_inicio (1-based).

        Cada sublista de datos es una fila; sus elementos se escriben en
        columnas consecutivas empezando en A.

        Raises:
            HojaFaltanteError: si la hoja no existe.
        """
        if hoja not in self._workbook.sheetnames:
            raise HojaFaltanteError(
                f"No existe la hoja '{hoja}' en {self.ruta}. "
                f"Hojas disponibles: {self._workbook.sheetnames}"
            )
        ws = self._workbook[hoja]
        for offset, fila in enumerate(datos):
            for col_idx, valor in enumerate(fila, start=1):
                ws.cell(row=fila_inicio + offset, column=col_idx, value=valor)

    def escribir_formula(
        self,
        hoja: str,
        fila: int,
        col: int,
        formula: str,
    ) -> None:
        """Inserta una fórmula (texto) en una celda específica.

        Excel la evaluará al abrir el archivo. Compatible con BUSCARX, SI, etc.

        Raises:
            HojaFaltanteError: si la hoja no existe.
        """
        if hoja not in self._workbook.sheetnames:
            raise HojaFaltanteError(f"No existe la hoja '{hoja}' en {self.ruta}.")
        ws = self._workbook[hoja]
        ws.cell(row=fila, column=col, value=formula)

    def insertar_formula_rango(
        self,
        hoja: str,
        col: int,
        fila_inicio: int,
        fila_fin: int,
        formula_por_fila: Callable[[int], str],
    ) -> None:
        """Inserta una fórmula (distinta por fila) en un rango vertical.

        Args:
            hoja: nombre de la hoja.
            col: número de columna (1-based, A=1).
            fila_inicio: primera fila del rango (1-based).
            fila_fin: última fila del rango (1-based, inclusiva).
            formula_por_fila: callable que recibe el número de fila y devuelve
                la fórmula a insertar en esa fila.

        Raises:
            HojaFaltanteError: si la hoja no existe.
        """
        if hoja not in self._workbook.sheetnames:
            raise HojaFaltanteError(f"No existe la hoja '{hoja}' en {self.ruta}.")
        ws = self._workbook[hoja]
        for fila in range(fila_inicio, fila_fin + 1):
            ws.cell(row=fila, column=col, value=formula_por_fila(fila))

    def guardar(self) -> None:
        """Persiste los cambios al archivo .xlsx."""
        self._workbook.save(self.ruta)

    def cerrar(self) -> None:
        """Cierra el workbook (libera el handle del archivo)."""
        self._workbook.close()
