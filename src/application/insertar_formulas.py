"""Caso de uso: insertar fórmulas en la pestaña Ventas del archivo de salida.

Inserta 8 fórmulas en cada fila de Ventas (J, L, M, N, O, P, Q, R, S) usando:
- BUSCARX (buscar en pestañas de soporte).
- SI anidadas (calcular incentivo según VALOR PRIMA).
- Réplicas (=A, =B, =P, =Q).
"""

from __future__ import annotations

from src.domain.formulas import formula_buscarx, formula_replica
from src.domain.tabla_primas import TablaPrimas
from src.infrastructure.excel_writer import ExcelWriter


# Constantes de columnas (1-based).
_COL_J = 10  # CC_CAJERO (BUSCARX)
_COL_L = 12  # CAJERO (SI)
_COL_M = 13  # SUBGERENTE (SI)
_COL_N = 14  # COD (réplica de A)
_COL_O = 15  # AGENCIA2 (réplica de B)
_COL_P = 16  # CC_SUBGERENTE (BUSCARX)
_COL_Q = 17  # NOMBRE_SUBGERENTE (BUSCARX)
_COL_R = 18  # CC_NOVEDAD_SUBGERENTE (réplica de P)
_COL_S = 19  # NOMBRE_NOVEDAD_SUBGERENTE (réplica de Q)


def insertar_formulas_ventas(
    writer: ExcelWriter,
    tabla_primas: TablaPrimas,
    fila_inicio: int = 2,
    fila_fin: int = 31362,
    col_prima: str = "G",
) -> None:
    """Inserta las 8 fórmulas en Ventas para todas las filas del rango.

    Args:
        writer: ExcelWriter ya abierto sobre el archivo de salida.
        tabla_primas: tabla con las primas → incentivol cajero/subgerente.
        fila_inicio: primera fila de datos (default 2, después del encabezado).
        fila_fin: última fila de datos (default 31362 según la plantilla).
        col_prima: letra de la columna donde está VALOR PRIMA (default G).
    """
    # 1. Insertar fórmulas J (BUSCARX sobre COD_CAJERO en Base red agencias).
    #    Una sola formula por fila (busca la fila completa).
    for fila in range(fila_inicio, fila_fin + 1):
        formula_j = formula_buscarx(
            valor_ref=f"I{fila}",
            hoja_destino="Base red agencias",
            col_busqueda="A",
            col_retorno="C",
        )
        writer.escribir_formula("Ventas", fila, _COL_J, formula_j)

    # 2. Insertar fórmulas L y M (SI anidadas sobre VALOR PRIMA).
    writer.insertar_formula_rango(
        hoja="Ventas",
        col=_COL_L,
        fila_inicio=fila_inicio,
        fila_fin=fila_fin,
        formula_por_fila=lambda f: tabla_primas.formula_cajero(col_prima, f),
    )
    writer.insertar_formula_rango(
        hoja="Ventas",
        col=_COL_M,
        fila_inicio=fila_inicio,
        fila_fin=fila_fin,
        formula_por_fila=lambda f: tabla_primas.formula_subgerente(col_prima, f),
    )

    # 3. Insertar réplicas N (=A) y O (=B).
    for fila in range(fila_inicio, fila_fin + 1):
        writer.escribir_formula("Ventas", fila, _COL_N, formula_replica(f"A{fila}"))
        writer.escribir_formula("Ventas", fila, _COL_O, formula_replica(f"B{fila}"))

    # 4. Insertar fórmulas P y Q (BUSCARX sobre COD en Base subgerentes).
    for fila in range(fila_inicio, fila_fin + 1):
        formula_p = formula_buscarx(
            valor_ref=f"N{fila}",
            hoja_destino="Base subgerentes",
            col_busqueda="H",
            col_retorno="A",
        )
        formula_q = formula_buscarx(
            valor_ref=f"N{fila}",
            hoja_destino="Base subgerentes",
            col_busqueda="H",
            col_retorno="B",
        )
        writer.escribir_formula("Ventas", fila, _COL_P, formula_p)
        writer.escribir_formula("Ventas", fila, _COL_Q, formula_q)

    # 5. Insertar réplicas R (=P) y S (=Q).
    for fila in range(fila_inicio, fila_fin + 1):
        writer.escribir_formula("Ventas", fila, _COL_R, formula_replica(f"P{fila}"))
        writer.escribir_formula("Ventas", fila, _COL_S, formula_replica(f"Q{fila}"))
