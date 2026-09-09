"""Caso de uso: llenar la pestaña Ventas del archivo de salida.

Lee la hoja del archivo SOY PREVENIDO (insumo principal) y mapea 10 columnas
específicas a las posiciones correctas en la pestaña Ventas de la salida.

La hoja se auto-detecta: puede llamarse "Ventas" (clásico) o tener un nombre
dinámico como "Soy Prevenido 06_2026". La detección se hace buscando las
columnas esperadas en cada hoja del archivo.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.mapeo import normalizar_header
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.excel_writer import ExcelWriter  # noqa: I001


# Mapeo de columnas: clave = nombre normalizado de la columna en el insumo,
# valor = número de columna en la salida (1-based, A=1, B=2, ..., S=19).
#
# Las columnas NO listadas (10, 12-19) se llenan en otra fase:
# - 10 (J=CC_CAJERO): formula BUSCARX.
# - 12 (L=CAJERO), 13 (M=SUBGERENTE): formulas SI anidadas.
# - 14-15 (N=COD, O=AGENCIA2): replicas de A y B.
# - 16-17 (P,Q): formulas BUSCARX.
# - 18-19 (R,S): replicas de P,Q.
MAPEO_VENTAS: dict[str, int] = {
    "CODIGO_AGENCIA": 1,  # A
    "NOMBRE_AGENCIA": 2,  # B
    "NUMERO_IDENTIFICACION": 3,  # C
    "NOMBRE_ASEGURADO": 4,  # D
    "CUENTA_CLIENTE": 5,  # E
    "FECHA_TRANSACCION": 6,  # F ← V (FECHA_TRANSACCION del input)
    "VALOR_PRIMA": 7,  # G
    "TRANSACCION2": 8,  # H ← Q (TRANSACCION2 del input)
    "COD_CAJERO": 9,  # I (con limpieza @)
    "NOMBRE_CAJERO": 11,  # K
}

COL_COD_CAJERO = 9  # Columna I en la salida (1-based).

# Filas a probar para encontrar los encabezados (caso común: título en fila 1).
_FILAS_ENCABEZADO_A_INTENTAR = (1, 2, 3, 4, 5)


def _limpiar_cod_cajero(valor: Any) -> Any:
    """Quita todo lo que viene después del @ en COD_CAJERO.

    Si el valor no es string (ej: None, date, número), lo retorna tal cual.
    Tambien quita espacios al inicio/final para que BUSCARX matchee.

    NOTA: NO convierte a mayusculas/minusculas. El case matching se hace
    en Base red agencias (donde uppercased USUARIO WINDOWS) para que
    matchee con el COD_CAJERO del input (que viene en mayusculas).

    Ejemplos:
        "JENHURTADO"            → "JENHURTADO"
        "JENHURTADO   "          → "JENHURTADO"  (sin espacios)
        "USUARIO@DOMINIO"       → "USUARIO"
        "USUARIO@DOMINIO   "     → "USUARIO"      (sin espacios)
        "ABC@DEF@GHI"           → "ABC"
        None                    → None
    """
    if not isinstance(valor, str):
        return valor
    valor = valor.strip()
    if "@" not in valor:
        return valor
    return valor.split("@", 1)[0]


def _detectar_hoja_y_fila(reader: ExcelReader) -> tuple[str, int] | None:
    """Detecta la hoja y fila que contienen las columnas esperadas del mapeo.

    Returns:
        Tupla (nombre_hoja, fila_encabezado) o None si no se encuentra.
    """
    hojas = reader.listar_hojas()
    if not hojas:
        return None

    cols_objetivo = {normalizar_header(c) for c in MAPEO_VENTAS}

    for hoja in hojas:
        for fila in _FILAS_ENCABEZADO_A_INTENTAR:
            try:
                encs = set(
                    reader.leer_encabezados(hoja, fila_encabezado=fila, normalizar=True)
                )
            except Exception:  # noqa: BLE001
                continue
            # Si al menos 1 columna objetivo está presente, esta es la hoja correcta.
            if encs & cols_objetivo:
                return hoja, fila

    return None


def llenar_ventas(ruta_insumo: Path | str, writer: ExcelWriter) -> int:
    """Lee el SOY PREVENIDO y llena las columnas de datos en la salida.

    Args:
        ruta_insumo: ruta al archivo SOY PREVENIDO (.xlsx).
        writer: ExcelWriter ya abierto sobre el archivo de salida.

    Returns:
        Cantidad de filas de datos escritas (sin contar encabezados).
    """
    reader = ExcelReader(ruta_insumo)
    try:
        # 1. Auto-detectar hoja + fila de encabezados.
        deteccion = _detectar_hoja_y_fila(reader)
        if deteccion is None:
            return 0
        nombre_hoja, fila_encabezado = deteccion

        # 2. Leer encabezados del insumo (normalizados).
        headers_insumo = reader.leer_encabezados(
            nombre_hoja,
            fila_encabezado=fila_encabezado,
            normalizar=True,
        )

        # 3. Construir mapping: idx_origen (0-based) → col_destino (1-based).
        col_origen_a_destino: dict[int, int] = {}
        for col_insumo_nombre, col_destino in MAPEO_VENTAS.items():
            col_normalizada = normalizar_header(col_insumo_nombre)
            if col_normalizada in headers_insumo:
                idx_origen = headers_insumo.index(col_normalizada)
                col_origen_a_destino[idx_origen] = col_destino

        if not col_origen_a_destino:
            return 0

        # 4. Leer las filas de datos (a partir de fila_encabezado + 1).
        datos = reader.leer_hoja(
            nombre_hoja, fila_encabezado=fila_encabezado, normalizar=True
        )

        # 5. Preparar filas para escribir (sin filtros: se copian todas las filas).
        filas_para_escribir: list[list] = []
        for fila_dict in datos:
            fila_out: list = [None] * 19
            for idx_origen, col_destino in col_origen_a_destino.items():
                header = headers_insumo[idx_origen]
                valor = fila_dict.get(header)

                # Si es datetime (openpyxl lee fechas como datetime con hora 00:00:00),
                # convertir a date (sin hora) para que Excel muestre solo la fecha.
                if isinstance(valor, datetime):
                    valor = valor.date()

                # Aplicar limpieza @ en COD_CAJERO.
                if col_destino == COL_COD_CAJERO:
                    valor = _limpiar_cod_cajero(valor)

                fila_out[col_destino - 1] = valor
            filas_para_escribir.append(fila_out)

        # 6. Escribir en la pestaña Ventas (a partir de fila 2).
        if filas_para_escribir:
            writer.escribir_datos(
                hoja="Ventas", fila_inicio=2, datos=filas_para_escribir
            )
            # FECHA_TRANSACCION (col 6 = F): formato solo fecha dd/mm/yyyy.
            # Si el formato default incluye hora ('yyyy-mm-dd h:mm:ss'),
            # Excel mostraría la fecha CON hora. Forzamos formato solo fecha.
            writer.set_number_format(
                hoja="Ventas",
                fila_inicio=2,
                fila_fin=len(filas_para_escribir) + 1,
                col=6,
                formato="dd/mm/yyyy",
            )

        return len(filas_para_escribir)
    finally:
        reader.cerrar()
