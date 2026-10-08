"""Caso de uso: llenar la pestaña Base red agencias del archivo de salida.

Lee las pestañas "BANCO" y "TEMPORAL" de "Base Seguros – Actualizada", filtra
las filas donde CARGO está en la lista de cargos permitidos, y mapea 5
columnas a la salida.

Nota: la columna CARGO está en E en la pestaña BANCO y en F en TEMPORAL, pero
el mapeo se hace por NOMBRE de encabezado (normalizado), no por posición, así
que ambas pestañas se procesan igual.

Optimización: los archivos reales pueden tener ~1 millón de filas "vacías"
(con formato aplicado) y solo cientos de filas con datos. Se usa iter_rows
con early-stop (10.000 filas vacías consecutivas → fin de datos) para no
recorrer el millón de filas.
"""

from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import Any

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
    "AUXILIAR INTEGRAL",
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

# Pestañas del archivo Base Seguros que alimentan la Base red agencias.
HOJAS_FUENTE: tuple[str, ...] = ("BANCO", "TEMPORAL")

# Nº de filas vacías consecutivas que indican "fin de datos".
_MAX_FILAS_VACIAS = 10_000


def llenar_base_red_agencias(
    ruta_insumo: Path | str,
    writer: ExcelWriter,
    logger: Any = None,  # type: ignore[type-arg]
    ruta_subgerentes: Path | str | None = None,
) -> int:
    """Filtra Base Seguros por CARGO y llena la pestaña Base red agencias.

    Lee AMBAS pestañas (BANCO y TEMPORAL) con el filtro de cargos, y además
    (si se pasa ruta_subgerentes) la pestaña "Subgerentes" del archivo de
    correcciones, SIN filtro (son los cajeros que faltan).

    Args:
        ruta_insumo: ruta al archivo "Base Seguros – Actualizada" (.xlsx).
        writer: ExcelWriter ya abierto sobre el archivo de salida.
        logger: opcional, para registrar auditoría detallada.
        ruta_subgerentes: opcional, ruta al archivo de correcciones con la
            pestaña "Subgerentes" (fuente extra, sin filtro de cargo).

    Returns:
        Cantidad de filas escritas.
    """

    def _log(msg: str) -> None:
        if logger is not None:
            logger.info(f"[llenar_base_red_agencias] {msg}")

    _log(f"Inicio. Input: {ruta_insumo}, Hojas: {HOJAS_FUENTE}")

    cargos_norm = {normalizar_header(c) for c in CARGOS_FILTRO}
    filas_para_escribir: list[list] = []

    reader = ExcelReader(ruta_insumo)
    try:
        hojas_existentes = set(reader.listar_hojas())

        for nombre_hoja in HOJAS_FUENTE:
            if nombre_hoja not in hojas_existentes:
                _log(f"ADVERTENCIA: no existe la hoja '{nombre_hoja}' (se omite).")
                continue

            t0 = monotonic()
            filas_hoja = _leer_hoja_filtrada(
                reader, nombre_hoja, cargos_norm, _log
            )
            dt = monotonic() - t0
            _log(
                f"Hoja '{nombre_hoja}': {len(filas_hoja)} filas filtradas "
                f"({dt:.1f}s)."
            )
            filas_para_escribir.extend(filas_hoja)

        _log(
            f"Total filas (BANCO+TEMPORAL) que pasaron el filtro CARGO: "
            f"{len(filas_para_escribir)}"
        )

        # Fuente extra: pestaña "Subgerentes" del archivo de correcciones
        # (SIN filtro de cargos; son los cajeros que faltan).
        if ruta_subgerentes is not None:
            filas_sub = _leer_subgerentes(ruta_subgerentes, _log)
            _log(f"Pestaña 'Subgerentes' (extra): {len(filas_sub)} filas.")
            filas_para_escribir.extend(filas_sub)

        # Escribir en la pestaña "Base red agencias" (a partir de fila 2).
        if filas_para_escribir:
            writer.escribir_datos(
                hoja="Base red agencias",
                fila_inicio=2,
                datos=filas_para_escribir,
            )
            _log(
                f"Escritura completada: {len(filas_para_escribir)} filas en 'Base red agencias'"
            )
        else:
            _log("ADVERTENCIA: ninguna fila pasó el filtro CARGO.")

        return len(filas_para_escribir)
    finally:
        reader.cerrar()


def _leer_hoja_filtrada(
    reader: ExcelReader,
    nombre_hoja: str,
    cargos_norm: set[str],
    _log,
) -> list[list]:
    """Lee una hoja fuente, filtra por CARGO y devuelve las filas mapeadas.

    Usa iter_rows con early-stop: si se encuentran _MAX_FILAS_VACIAS filas
    vacías consecutivas, se asume que los datos terminaron (los archivos
    reales tienen ~1M de filas con formato pero solo cientos con datos).
    """
    headers = reader.leer_encabezados(
        nombre_hoja, fila_encabezado=1, normalizar=True
    )
    headers_idx: dict[str, int] = {h: i for i, h in enumerate(headers)}

    # Columna CARGO (por nombre normalizado, no por posición).
    cargo_idx = headers_idx.get(normalizar_header("CARGO"))
    if cargo_idx is None:
        _log(f"ERROR: no se encontró la columna CARGO en '{nombre_hoja}'.")
        return []

    # Mapping: idx_input → pos_salida (1-based).
    input_a_salida: dict[int, int] = {}
    for pos_salida, (col_input, _col_output) in enumerate(
        MAPEO_BASE_RED_AGENCIAS, start=1
    ):
        col_norm = normalizar_header(col_input)
        if col_norm in headers_idx:
            input_a_salida[headers_idx[col_norm]] = pos_salida

    if not input_a_salida:
        _log(f"ERROR: ninguna columna del mapeo encontrada en '{nombre_hoja}'.")
        return []

    # Nº máximo de columna que necesitamos leer (para no traer columnas extra).
    max_col = max(headers_idx[normalizar_header(col)] for col, _ in MAPEO_BASE_RED_AGENCIAS if normalizar_header(col) in headers_idx)
    max_col = max(max_col, cargo_idx) + 1

    hoja = reader._workbook[nombre_hoja]
    filas: list[list] = []
    vacias_consecutivas = 0

    for fila_tuple in hoja.iter_rows(
        min_row=2, max_col=max_col, values_only=True
    ):
        # Fila completamente vacía (todos None).
        if all(v is None for v in fila_tuple):
            vacias_consecutivas += 1
            if vacias_consecutivas >= _MAX_FILAS_VACIAS:
                # Fin de datos: el resto del archivo es formato vacío.
                break
            continue
        vacias_consecutivas = 0

        valor_cargo = fila_tuple[cargo_idx] if cargo_idx < len(fila_tuple) else None
        if valor_cargo is None:
            continue
        if normalizar_header(str(valor_cargo)) not in cargos_norm:
            continue

        fila_out: list = [None] * len(MAPEO_BASE_RED_AGENCIAS)
        for idx_input, pos_salida in input_a_salida.items():
            valor = fila_tuple[idx_input] if idx_input < len(fila_tuple) else None
            # Col 1 (USUARIO WINDOWS): mayúsculas y sin espacios al final.
            if pos_salida == 1 and isinstance(valor, str):
                valor = valor.strip().upper()
            # Col 4 (EMPLEADO): sin espacios al final (fallback por nombre).
            if pos_salida == 4 and isinstance(valor, str):
                valor = valor.strip()
            fila_out[pos_salida - 1] = valor
        filas.append(fila_out)

    return filas


def _leer_subgerentes(ruta: Path | str, _log) -> list[list]:
    """Lee la pestaña "Subgerentes" del archivo de correcciones (SIN filtro).

    Son los cajeros que faltan: se agregan tal cual, sin aplicar el filtro
    de cargos. El mapeo de columnas es por nombre (CEDULA, USUARIO WINDOWS,
    INICIALES, COLABORADOR -> EMPLEADO, CARGO).
    """
    if not Path(ruta).exists():
        _log(f"ADVERTENCIA: no existe el archivo de correcciones {ruta}.")
        return []

    try:
        reader = ExcelReader(ruta)
    except (OSError, ValueError, KeyError) as e:
        _log(f"ADVERTENCIA: no se pudo abrir {ruta}: {e}")
        return []

    try:
        if "Subgerentes" not in reader.listar_hojas():
            _log("ADVERTENCIA: no existe la pestaña 'Subgerentes' (se omite).")
            return []

        headers = reader.leer_encabezados(
            "Subgerentes", fila_encabezado=1, normalizar=True
        )
        headers_idx: dict[str, int] = {h: i for i, h in enumerate(headers)}

        input_a_salida: dict[int, int] = {}
        for pos_salida, (col_input, _col_output) in enumerate(
            MAPEO_BASE_RED_AGENCIAS, start=1
        ):
            col_norm = normalizar_header(col_input)
            if col_norm in headers_idx:
                input_a_salida[headers_idx[col_norm]] = pos_salida

        if not input_a_salida:
            _log("ERROR: ninguna columna del mapeo encontrada en 'Subgerentes'.")
            return []

        max_col = max(input_a_salida.keys()) + 1
        hoja = reader._workbook["Subgerentes"]
        filas: list[list] = []
        vacias_consecutivas = 0
        for fila_tuple in hoja.iter_rows(
            min_row=2, max_col=max_col, values_only=True
        ):
            if all(v is None for v in fila_tuple):
                vacias_consecutivas += 1
                if vacias_consecutivas >= _MAX_FILAS_VACIAS:
                    break
                continue
            vacias_consecutivas = 0

            fila_out: list = [None] * len(MAPEO_BASE_RED_AGENCIAS)
            tiene_dato = False
            for idx_input, pos_salida in input_a_salida.items():
                valor = fila_tuple[idx_input] if idx_input < len(fila_tuple) else None
                if pos_salida == 1 and isinstance(valor, str):
                    valor = valor.strip().upper()
                if pos_salida == 4 and isinstance(valor, str):
                    valor = valor.strip()
                if valor is not None and str(valor).strip() != "":
                    tiene_dato = True
                fila_out[pos_salida - 1] = valor
            if tiene_dato:
                filas.append(fila_out)

        return filas
    finally:
        reader.cerrar()
