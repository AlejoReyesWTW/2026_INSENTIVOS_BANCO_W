"""Lector de la tabla de comisiones/incentivos desde Base_Comisiones_Insentivos.xlsx.

El banco edita este archivo cuando cambian las comisiones. El sistema debe leer
la tabla de primas desde ahí para que los cálculos sean dinámicos.

Formato esperado (hoja "Hoja1"):
    F1:  ['cajero', None, None, 'subgerente', None]
    F2:  ['valor prima', 'comisión', None, 'valor prima', 'comisión']
    F3+: [2414, 137, None, 2414, 34]
         [5072, 290, None, 5072, 72]
         ...
    Col A = valor prima (cajero), Col B = comisión cajero.
    Col D = valor prima (subgerente), Col E = comisión subgerente.

Se tolera: filas de encabezado, filas vacías, valores numéricos o texto.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl

from src.domain.errores import ArchivoNoEncontradoError
from src.domain.tabla_primas import Prima, TablaPrimas


def leer_tabla_comisiones(ruta: Path | str) -> TablaPrimas:
    """Lee la tabla de comisiones desde el xlsx del banco.

    Args:
        ruta: ruta al archivo Base_Comisiones_Insentivos.xlsx.

    Returns:
        TablaPrimas con una entrada por fila de datos.

    Raises:
        ArchivoNoEncontradoError: si el archivo no existe.
    """
    ruta_p = Path(ruta)
    if not ruta_p.exists():
        raise ArchivoNoEncontradoError(
            f"No se encontró el archivo de comisiones: {ruta_p}"
        )

    wb = openpyxl.load_workbook(ruta_p, data_only=True, read_only=True)
    try:
        hoja = wb["Hoja1"]
        primas: list[Prima] = []
        for fila in hoja.iter_rows(min_row=3, max_col=5, values_only=True):
            a, b, _c, d, e = fila[:5]
            valor = _a_int(a) or _a_int(d)
            cajero = _a_int(b)
            subgerente = _a_int(e)
            if valor is None:
                continue
            primas.append(
                Prima(
                    valor=valor,
                    cajero=cajero if cajero is not None else 0,
                    subgerente=subgerente if subgerente is not None else 0,
                )
            )
        return TablaPrimas(tuple(primas))
    finally:
        wb.close()


def _a_int(valor) -> int | None:
    """Convierte un valor de celda a int, tolerando float/texto/vacío."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        try:
            return int(valor) if valor.is_integer() else None
        except (TypeError, ValueError, OverflowError):
            return None
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        return None
    try:
        numero = float(texto)
    except (TypeError, ValueError):
        return None
    try:
        return int(numero) if numero.is_integer() else None
    except (TypeError, ValueError, OverflowError):
        return None
