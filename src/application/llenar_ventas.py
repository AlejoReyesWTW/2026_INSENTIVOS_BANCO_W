"""Caso de uso: llenar la pestaña Ventas del archivo de salida.

Lee la hoja "Ventas" del archivo SOY PREVENIDO (insumo principal) y mapea
10 columnas específicas a las posiciones correctas en la pestaña Ventas de
la salida. Aplica limpieza del @ en COD_CAJERO.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.mapeo import normalizar_header
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.excel_writer import ExcelWriter


# Mapeo de columnas: clave = nombre normalizado de la columna en el insumo,
# valor = número de columna en la salida (1-based, A=1, B=2, ..., S=19).
#
# Las columnas NO listadas (10, 12-19) se llenan en otra fase:
# - 10 (J=CC_CAJERO): formula BUSCARX en T-307.
# - 12 (L=CAJERO), 13 (M=SUBGERENTE): formulas SI anidadas en T-307.
# - 14-15 (N=COD, O=AGENCIA2): replicas de A y B (T-307).
# - 16-17 (P,Q): formulas BUSCARX en T-307.
# - 18-19 (R,S): replicas de P,Q (T-307).
MAPEO_VENTAS: dict[str, int] = {
    "CODIGO_AGENCIA": 1,  # A
    "NOMBRE_AGENCIA": 2,  # B
    "NUMERO_IDENTIFICACION": 3,  # C
    "NOMBRE_ASEGURADO": 4,  # D
    "CUENTA_CLIENTE": 5,  # E
    "TRANSACCION2": 6,  # F
    "VALOR_PRIMA": 7,  # G
    "FECHA_TRANSACCION": 8,  # H
    "COD_CAJERO": 9,  # I (con limpieza @)
    "NOMBRE_CAJERO": 11,  # K
}

COL_COD_CAJERO = 9  # Columna I en la salida (1-based).


def _limpiar_cod_cajero(valor: str | None) -> str | None:
    """Quita todo lo que viene después del @ en COD_CAJERO.

    Ejemplos:
        "JENHURTADO"            → "JENHURTADO"
        "USUARIO@DOMINIO"       → "USUARIO"
        "ABC@DEF@GHI"           → "ABC"
        None                    → None
    """
    if not isinstance(valor, str):
        return valor
    if "@" not in valor:
        return valor
    return valor.split("@", 1)[0]


def llenar_ventas(ruta_insumo: Path | str, writer: ExcelWriter) -> int:
    """Lee Ventas del SOY PREVENIDO y llena las columnas de datos en la salida.

    Args:
        ruta_insumo: ruta al archivo SOY PREVENIDO (.xlsx).
        writer: ExcelWriter ya abierto sobre el archivo de salida.

    Returns:
        Cantidad de filas de datos escritas (sin contar encabezados).
    """
    reader = ExcelReader(ruta_insumo)
    try:
        # 1. Leer encabezados del insumo (normalizados).
        headers_insumo = reader.leer_encabezados(
            "Ventas", fila_encabezado=1, normalizar=True
        )

        # 2. Construir mapping: idx_origen (0-based) → col_destino (1-based).
        #    Normalizamos los keys del MAPEO_VENTAS para comparar con los
        #    headers ya normalizados del archivo.
        col_origen_a_destino: dict[int, int] = {}
        for col_insumo_nombre, col_destino in MAPEO_VENTAS.items():
            col_normalizada = normalizar_header(col_insumo_nombre)
            if col_normalizada in headers_insumo:
                idx_origen = headers_insumo.index(col_normalizada)
                col_origen_a_destino[idx_origen] = col_destino

        if not col_origen_a_destino:
            return 0

        # 3. Leer las filas de datos.
        datos = reader.leer_hoja("Ventas", fila_encabezado=1, normalizar=True)

        # 4. Preparar filas para escribir (cada fila ocupa hasta 19 cols).
        filas_para_escribir: list[list] = []
        for fila_dict in datos:
            fila_out: list = [None] * 19
            for idx_origen, col_destino in col_origen_a_destino.items():
                header = headers_insumo[idx_origen]
                valor = fila_dict.get(header)

                # Aplicar limpieza @ en COD_CAJERO.
                if col_destino == COL_COD_CAJERO:
                    valor = _limpiar_cod_cajero(valor)

                fila_out[col_destino - 1] = valor
            filas_para_escribir.append(fila_out)

        # 5. Escribir en la pestaña Ventas (a partir de fila 2).
        if filas_para_escribir:
            writer.escribir_datos(
                hoja="Ventas", fila_inicio=2, datos=filas_para_escribir
            )

        return len(filas_para_escribir)
    finally:
        reader.cerrar()
