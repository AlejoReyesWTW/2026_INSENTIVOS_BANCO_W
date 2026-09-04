"""Generador de fórmulas Excel (BUSCARX, réplicas, etc.).

Todas las fórmulas usan el separador `;` propio de Excel en español.
"""

from __future__ import annotations


def _entrecomillar_hoja(hoja: str) -> str:
    """Encierra el nombre de hoja entre comillas simples (sintaxis segura).

    Ejemplos:
        >>> _entrecomillar_hoja("Ventas")
        "'Ventas'"
        >>> _entrecomillar_hoja("Base red agencias")
        "'Base red agencias'"
    """
    return f"'{hoja}'"


def formula_buscarx(
    valor_ref: str,
    hoja_destino: str,
    col_busqueda: str,
    col_retorno: str,
) -> str:
    """Genera una fórmula BUSCARX para Excel en español.

    Args:
        valor_ref: referencia al valor buscado (ej: "I2", "@I:I", "N5").
        hoja_destino: nombre de la hoja donde buscar (ej: "Base red agencias").
        col_busqueda: letra de la columna donde buscar el valor (ej: "A").
        col_retorno: letra de la columna de donde retornar el dato (ej: "C").

    Returns:
        Fórmula completa, ej: `=BUSCARX(I2;'Base red agencias'!A:A;'Base red agencias'!C:C;1;0)`.

    Notas:
        - El 4° argumento es 1 (placeholder visible cuando no hay match).
        - El 5° argumento es 0 (coincidencia exacta).
    """
    hoja = _entrecomillar_hoja(hoja_destino)
    # 5 argumentos separados por ; (Excel español).
    # =BUSCARX(valor ; hoja!col_busq:col_busq ; hoja!col_ret:col_ret ; 1 ; 0)
    return (
        f"=BUSCARX({valor_ref};"
        f"{hoja}!{col_busqueda}:{col_busqueda};"
        f"{hoja}!{col_retorno}:{col_retorno};"
        f"1;0)"
    )


def formula_replica(ref_celda: str) -> str:
    """Genera una fórmula de réplica (=<ref>) que copia el valor de otra celda.

    Ejemplos:
        >>> formula_replica("P2")
        '=P2'
        >>> formula_replica("Q5")
        '=Q5'
    """
    return f"={ref_celda}"
