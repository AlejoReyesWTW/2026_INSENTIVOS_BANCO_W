"""Caso de uso: llenar la pestaña Base subgerentes del archivo de salida.

Lee la primera pestaña de "Base Banco Completa SS", filtra las filas donde
CARGO == "SUBGERENTE DE OFICINA", y mapea 11 columnas a la pestaña de salida.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.mapeo import normalizar_header
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.excel_writer import ExcelWriter


# Mapeo de columnas: tuplas (nombre_input, nombre_output).
# El orden en la lista define la posición en la salida (1-based).
MAPEO_BASE_SUBGERENTES: list[tuple[str, str]] = [
    ("CEDULA", "CEDULA"),
    ("COLABORADOR", "EMPLEADO"),
    ("CARGO", "CARGO"),
    ("VICEPRESIDENCIA", "NOM_VICE"),
    ("GERENCIA", "NOM_GER"),
    ("CENTRO DE COSTOS", "CENCOS_NOM"),
    ("LOCALIDAD", "NOM_LOCALIDAD"),
    ("COD OFIC", "COD AGENCIA"),
    ("OFICINA", "NOMBRE OFICINA"),
    ("LOCALIDA PAGO", "CIUDAD DE PAGO"),
    ("SEXO", "SEX"),
]

CARGO_FILTRO = "SUBGERENTE DE OFICINA"


def llenar_base_subgerentes(
    ruta_insumo: Path | str,
    writer: ExcelWriter,
) -> int:
    """Filtra Base Banco Completa SS por CARGO y llena la pestaña Base subgerentes.

    Args:
        ruta_insumo: ruta al archivo "Base Banco Completa SS" (.xlsx).
        writer: ExcelWriter ya abierto sobre el archivo de salida.

    Returns:
        Cantidad de filas escritas (solo subgerentes de oficina).
    """
    reader = ExcelReader(ruta_insumo)
    try:
        # 1. Tomar la primera pestaña del archivo.
        hojas = reader.listar_hojas()
        if not hojas:
            return 0
        nombre_hoja = hojas[0]

        # 2. Leer encabezados (normalizados) y construir índice rápido.
        headers = reader.leer_encabezados(
            nombre_hoja, fila_encabezado=1, normalizar=True
        )
        headers_idx: dict[str, int] = {h: i for i, h in enumerate(headers)}

        # 3. Encontrar la columna CARGO (necesaria para filtrar).
        cargo_idx = headers_idx.get(normalizar_header("CARGO"))
        if cargo_idx is None:
            return 0  # Sin columna CARGO no podemos filtrar.

        # 4. Construir mapping: idx_input → pos_salida (1-based).
        input_a_salida: dict[int, int] = {}
        for pos_salida, (col_input, _col_output) in enumerate(
            MAPEO_BASE_SUBGERENTES, start=1
        ):
            col_norm = normalizar_header(col_input)
            if col_norm in headers_idx:
                input_a_salida[headers_idx[col_norm]] = pos_salida

        if not input_a_salida:
            return 0

        # 5. Leer filas y filtrar por CARGO.
        datos = reader.leer_hoja(nombre_hoja, fila_encabezado=1, normalizar=True)
        cargo_filtro_norm = normalizar_header(CARGO_FILTRO)

        filas_para_escribir: list[list] = []
        for fila_dict in datos:
            valor_cargo = fila_dict.get(headers[cargo_idx])
            if valor_cargo is None:
                continue
            if normalizar_header(str(valor_cargo)) != cargo_filtro_norm:
                continue

            fila_out: list = [None] * len(MAPEO_BASE_SUBGERENTES)
            for idx_input, pos_salida in input_a_salida.items():
                header = headers[idx_input]
                fila_out[pos_salida - 1] = fila_dict.get(header)
            filas_para_escribir.append(fila_out)

        # 6. Escribir en la pestaña "Base subgerentes" (a partir de fila 2).
        if filas_para_escribir:
            writer.escribir_datos(
                hoja="Base subgerentes",
                fila_inicio=2,
                datos=filas_para_escribir,
            )

        return len(filas_para_escribir)
    finally:
        reader.cerrar()
