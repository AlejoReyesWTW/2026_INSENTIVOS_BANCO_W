"""Caso de uso: llenar la pestaña Base red agencias del archivo de salida.

Lee la pestaña "BANCO" de "Base Seguros – Actualizada", filtra las filas donde
CARGO está en la lista de 6 cargos permitidos, y mapea 5 columnas a la salida.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.mapeo import normalizar_header
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.excel_writer import ExcelWriter


# Lista de CARGOS que se incluyen en la pestaña Base red agencias.
CARGOS_FILTRO: tuple[str, ...] = (
    "CAJERO(A) AUXILIAR",
    "CAJERO(A) PRINCIPAL",
    "SUBGERENTE DE OFICINA",
    "AUXILIAR OPERATIVO",
    "AUXILIAR OPERATIVO DE PLANTA",
    "CAJERO(A) PRINCIPAL  DE PLANTA",
)

# Mapeo de columnas: tuplas (nombre_input, nombre_output).
# El orden define la posición en la salida (1-based).
MAPEO_BASE_RED_AGENCIAS: list[tuple[str, str]] = [
    ("USUARIO WINDOWS", "USUARIO WINDOWS"),
    ("INICIALES", "INICIALES"),
    ("CEDULA", "CEDULA"),
    ("COLABORADOR", "EMPLEADO"),
    ("CARGO", "CARGO"),
]

NOMBRE_HOJA = "BANCO"


def llenar_base_red_agencias(
    ruta_insumo: Path | str,
    writer: ExcelWriter,
) -> int:
    """Filtra Base Seguros por CARGO y llena la pestaña Base red agencias.

    Args:
        ruta_insumo: ruta al archivo "Base Seguros – Actualizada" (.xlsx).
        writer: ExcelWriter ya abierto sobre el archivo de salida.

    Returns:
        Cantidad de filas escritas (con CARGO en CARGOS_FILTRO).
    """
    reader = ExcelReader(ruta_insumo)
    try:
        # 1. Leer encabezados (normalizados) de la hoja BANCO.
        headers = reader.leer_encabezados(
            NOMBRE_HOJA, fila_encabezado=1, normalizar=True
        )
        headers_idx: dict[str, int] = {h: i for i, h in enumerate(headers)}

        # 2. Encontrar la columna CARGO (necesaria para filtrar).
        cargo_idx = headers_idx.get(normalizar_header("CARGO"))
        if cargo_idx is None:
            return 0

        # 3. Construir mapping: idx_input → pos_salida (1-based).
        input_a_salida: dict[int, int] = {}
        for pos_salida, (col_input, _col_output) in enumerate(
            MAPEO_BASE_RED_AGENCIAS, start=1
        ):
            col_norm = normalizar_header(col_input)
            if col_norm in headers_idx:
                input_a_salida[headers_idx[col_norm]] = pos_salida

        if not input_a_salida:
            return 0

        # 4. Pre-normalizar la lista de cargos a filtrar.
        cargos_norm = {normalizar_header(c) for c in CARGOS_FILTRO}

        # 5. Leer filas y filtrar por CARGO.
        datos = reader.leer_hoja(NOMBRE_HOJA, fila_encabezado=1, normalizar=True)

        filas_para_escribir: list[list] = []
        for fila_dict in datos:
            valor_cargo = fila_dict.get(headers[cargo_idx])
            if valor_cargo is None:
                continue
            if normalizar_header(str(valor_cargo)) not in cargos_norm:
                continue

            fila_out: list = [None] * len(MAPEO_BASE_RED_AGENCIAS)
            for idx_input, pos_salida in input_a_salida.items():
                header = headers[idx_input]
                fila_out[pos_salida - 1] = fila_dict.get(header)
            filas_para_escribir.append(fila_out)

        # 6. Escribir en la pestaña "Base red agencias" (a partir de fila 2).
        if filas_para_escribir:
            writer.escribir_datos(
                hoja="Base red agencias",
                fila_inicio=2,
                datos=filas_para_escribir,
            )

        return len(filas_para_escribir)
    finally:
        reader.cerrar()
