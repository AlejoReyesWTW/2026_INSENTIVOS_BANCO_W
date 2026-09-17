"""Caso de uso: rellenar P/Q vacías de Ventas usando Directorio Nacional.

Flujo (2ª pasada de cruce P/Q):
1. Detectar filas de Ventas donde P (CC_SUBGERENTE) quedó vacía.
2. Extraer códigos únicos de la columna N (COD) de esas filas.
3. Filtrar Directorio Nacional por su columna B (COD) con esa lista.
4. Copiar col B (COD) y col F (SUBGERENTE=nombre) del directorio.
5. Pegar en "Base subgerentes" debajo de la última fila: COD→col H, nombre→col B.
6. Refrescar el cruce P/Q con la base actualizada (se vuelve a calcular
   P/Q/R/S para las filas que estaban vacías).
"""

from __future__ import annotations

from pathlib import Path

from src.domain.mapeo import normalizar_header
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.excel_writer import ExcelWriter

# Columnas de Ventas (1-based).
_COL_P = 16  # CC_SUBGERENTE
_COL_Q = 17  # NOMBRE_SUBGERENTE
_COL_R = 18  # CC_NOVEDAD_SUBGERENTE (replica P)
_COL_S = 19  # NOMBRE_NOVEDAD_SUBGERENTE (replica Q)
_COL_N = 14  # COD (replica de A)

# Columnas de Base subgerentes (1-based).
_BS_COL_CEDULA = 1  # A
_BS_COL_NOMBRE = 2  # B
_BS_COL_COD = 8  # H (COD AGENCIA)

# Columnas de Directorio Nacional (1-based).
_DIR_COD = 2  # B
_DIR_SUBGERENTE = 6  # F


def codigos_pq_vacios(
    writer: ExcelWriter,
    fila_inicio: int = 2,
    fila_fin: int | None = None,
) -> list:
    """Códigos únicos de la columna N (COD) en filas donde P está vacía.

    Args:
        writer: ExcelWriter abierto sobre el archivo de salida.
        fila_inicio: primera fila de datos (default 2).
        fila_fin: última fila a revisar (default = max_row de Ventas).

    Returns:
        Lista de códigos únicos (int/str), en orden de aparición.
    """
    ws = writer._workbook["Ventas"]
    if fila_fin is None:
        fila_fin = ws.max_row

    vistos: set = set()
    codigos: list = []
    for fila in range(fila_inicio, fila_fin + 1):
        p_valor = ws.cell(row=fila, column=_COL_P).value
        if p_valor is not None and str(p_valor).strip():
            continue  # P ya llena, no aporta código.
        n_valor = ws.cell(row=fila, column=_COL_N).value
        if n_valor is None:
            continue
        clave = n_valor
        try:
            clave = int(n_valor)
        except (TypeError, ValueError):
            clave = str(n_valor).strip()
        if clave not in vistos:
            vistos.add(clave)
            codigos.append(clave)
    return codigos


def leer_directorio_por_codigos(
    ruta_directorio: Path | str,
    codigos: list,
) -> list[tuple]:
    """Filtra Directorio Nacional (hoja DIRECTORIO ACT) por col B (COD).

    Args:
        ruta_directorio: ruta al archivo Directorio Nacional (xls/xlsx).
        codigos: lista de códigos a buscar (int o str).

    Returns:
        Lista de tuplas (cod, nombre_subgerente) únicas, en orden del archivo.
        El nombre viene de la columna F (SUBGERENTE).
    """
    if not codigos:
        return []

    set_codigos = set(codigos)

    reader = ExcelReader(ruta_directorio)
    try:
        # Buscar la hoja DIRECTORIO ACT (o la primera disponible).
        hojas = reader.listar_hojas()
        if not hojas:
            return []
        nombre_hoja = next(
            (
                h
                for h in hojas
                if normalizar_header(h) == normalizar_header("DIRECTORIO ACT")
            ),
            hojas[0],
        )
        headers = reader.leer_encabezados(
            nombre_hoja, fila_encabezado=1, normalizar=True
        )
        idx_cod = None
        idx_sub = None
        for i, h in enumerate(headers):
            if h == normalizar_header("COD"):
                idx_cod = i
            if h == normalizar_header("SUBGERENTE"):
                idx_sub = i
        if idx_cod is None or idx_sub is None:
            return []

        filas = reader.leer_hoja(nombre_hoja, fila_encabezado=1, normalizar=True)
        resultados: list[tuple] = []
        vistos: set = set()
        for fila_dict in filas:
            clave = fila_dict.get(headers[idx_cod])
            nombre = fila_dict.get(headers[idx_sub])
            if clave is None or nombre is None:
                continue
            try:
                clave_norm = int(clave)
            except (TypeError, ValueError):
                clave_norm = str(clave).strip()
            if clave_norm not in set_codigos:
                continue
            if clave_norm in vistos:
                continue
            vistos.add(clave_norm)
            resultados.append((clave_norm, str(nombre).strip()))
        return resultados
    finally:
        reader.cerrar()


def refrescar_pq(
    writer: ExcelWriter,
    fila_inicio: int = 2,
    fila_fin: int | None = None,
) -> int:
    """Re-cruza P/Q/R/S de Ventas contra la Base subgerentes actualizada.

    P = cédula (col A de base) por código en col H. Q = nombre (col B).
    R/S réplicas de P/Q. Si no hay cédula, P queda vacía (no se rellena
    con el nombre: la cédula es un dato distinto).

    Args:
        writer: ExcelWriter abierto sobre el archivo de salida.
        fila_inicio: primera fila de datos (default 2).
        fila_fin: última fila (default = max_row de Ventas).

    Returns:
        Cantidad de filas con P/Q llenas tras el refresco.
    """
    ws = writer._workbook["Ventas"]
    ws_b = writer._workbook["Base subgerentes"]
    if fila_fin is None:
        fila_fin = ws.max_row

    # Indexar Base subgerentes: cod (col H=8) -> (cedula col A, nombre col B).
    indice: dict = {}
    for fila in range(2, ws_b.max_row + 1):
        cod = ws_b.cell(row=fila, column=_BS_COL_COD).value
        if cod is None:
            continue
        cedula = ws_b.cell(row=fila, column=_BS_COL_CEDULA).value
        nombre = ws_b.cell(row=fila, column=_BS_COL_NOMBRE).value
        clave = _normalizar_valor(cod)
        if clave in indice:
            continue
        indice[clave] = (cedula, nombre)

    llenas = 0
    for fila in range(fila_inicio, fila_fin + 1):
        n_valor = ws.cell(row=fila, column=_COL_N).value
        if n_valor is None:
            continue
        clave = _normalizar_valor(n_valor)
        cedula, nombre = indice.get(clave, (None, None))

        # P = cédula solamente (puede quedar vacía si no hay cédula).
        p_valor = cedula if cedula not in (None, "") else None
        # Q = nombre solamente.
        q_valor = nombre if nombre not in (None, "") else None
        if p_valor is None and q_valor is None:
            continue

        ws.cell(row=fila, column=_COL_P).value = p_valor
        ws.cell(row=fila, column=_COL_Q).value = q_valor
        ws.cell(row=fila, column=_COL_R).value = p_valor
        ws.cell(row=fila, column=_COL_S).value = q_valor
        llenas += 1
    return llenas


def pegar_subgerentes_en_base(
    writer: ExcelWriter,
    pares: list[tuple],
) -> int:
    """Pega (cod, nombre) al final de Base subgerentes.

    COD → columna H (COD AGENCIA), nombre → columna B (EMPLEADO).

    Args:
        writer: ExcelWriter abierto sobre el archivo de salida.
        pares: lista de tuplas (cod, nombre_subgerente).

    Returns:
        Cantidad de filas pegadas.
    """
    if not pares:
        return 0
    ws_b = writer._workbook["Base subgerentes"]
    fila = ws_b.max_row + 1
    for cod, nombre in pares:
        ws_b.cell(row=fila, column=_BS_COL_COD, value=cod)
        ws_b.cell(row=fila, column=_BS_COL_NOMBRE, value=nombre)
        fila += 1
    return len(pares)


def corregir_nombres_en_base(
    writer: ExcelWriter,
    ruta_correcciones: Path | str,
    fila_inicio: int = 2,
) -> int:
    """Corrige nombres en Base subgerentes usando el archivo de correcciones.

    Lee `Correccion_nombres_base_subgerentes.xlsx` (formato real):
      F1: título "Base Subgerentes"
      F2: encabezados "NOMBRE ERRONEO" | "NOMBRE CORRECTO A CAMBIAR"
      F3+: pares (erróneo, correcto)  <- solo desde acá se procesa

    Para cada fila de Base subgerentes desde `fila_inicio`, si el nombre
    (col B) coincide con un erróneo de la lista, se reemplaza por el
    correcto. Así la búsqueda de cédulas por nombre funciona después.

    Args:
        writer: ExcelWriter abierto sobre el archivo de salida.
        ruta_correcciones: ruta al archivo de correcciones de nombres.
        fila_inicio: primera fila de datos a revisar en la base (default 2).

    Returns:
        Cantidad de reemplazos realizados.
    """
    pares_correcciones = _leer_correcciones(ruta_correcciones)
    if not pares_correcciones:
        return 0

    # Índice: nombre erróneo normalizado -> nombre correcto.
    correcciones: dict[str, str] = {}
    for erroneo, correcto in pares_correcciones:
        clave = _normalizar_nombre(erroneo)
        if clave:
            correcciones[clave] = correcto

    ws_b = writer._workbook["Base subgerentes"]
    reemplazos = 0
    for fila in range(fila_inicio, ws_b.max_row + 1):
        nombre = ws_b.cell(row=fila, column=_BS_COL_NOMBRE).value
        if nombre is None:
            continue
        clave = _normalizar_nombre(nombre)
        correcto = correcciones.get(clave)
        if correcto is None:
            continue
        ws_b.cell(row=fila, column=_BS_COL_NOMBRE, value=correcto)
        reemplazos += 1
    return reemplazos


def _leer_correcciones(
    ruta_correcciones: Path | str,
) -> list[tuple[str, str]]:
    """Lee el archivo de correcciones de nombres.

    Returns:
        Lista de tuplas (nombre_erroneo, nombre_correcto) desde la fila 3.
    """
    reader = ExcelReader(ruta_correcciones)
    try:
        hojas = reader.listar_hojas()
        if not hojas:
            return []
        filas = reader.leer_hoja(hojas[0], fila_encabezado=2, normalizar=True)
        pares: list[tuple[str, str]] = []
        for fila_dict in filas:
            erroneo = fila_dict.get("nombre erroneo")
            correcto = fila_dict.get("nombre correcto a cambiar")
            if erroneo is None or correcto is None:
                continue
            erroneo_s = str(erroneo).strip()
            correcto_s = str(correcto).strip()
            if erroneo_s and correcto_s:
                pares.append((erroneo_s, correcto_s))
        return pares
    finally:
        reader.cerrar()


def completar_cedulas_en_base(
    writer: ExcelWriter,
    fila_inicio: int | None = None,
) -> int:
    """Busca la cédula (col A) de los subgerentes recién pegados.

        Los datos pegados desde Directorio Nacional solo traen nombre (col B)
        y código (col H), sin cédula. Este paso busca, para cada fila nueva
        (desde `fila_inicio` si se indica, o la última fila hacia arriba), el
        NOMBRE en la columna B (EMPLEADO) de las filas ANTERIORES (que sí
        tienen cédula en col A) y copia la cédula encontrada al frente.

        Args:
            writer: ExcelWriter abierto sobre el archivo de salida.
            fila_inicio: primera fila de las nuevas (default = última en
    orden de aparición de nombres sin cédula).

        Returns:
            Cantidad de cédulas completadas.
    """
    ws_b = writer._workbook["Base subgerentes"]
    if fila_inicio is None:
        fila_inicio = ws_b.max_row

    # Construir índice nombre (col B normalizado, sin espacios extra)
    # -> (fila, cedula) solo de las filas anteriores a las nuevas.
    indice_nombres: dict[str, tuple[int, str | int | None]] = {}
    for fila in range(2, fila_inicio):
        nombre = ws_b.cell(row=fila, column=_BS_COL_NOMBRE).value
        cedula = ws_b.cell(row=fila, column=_BS_COL_CEDULA).value
        if nombre is None:
            continue
        clave = _normalizar_nombre(nombre)
        if clave and clave not in indice_nombres:
            indice_nombres[clave] = (fila, cedula)

    completadas = 0
    for fila in range(fila_inicio, ws_b.max_row + 1):
        nombre = ws_b.cell(row=fila, column=_BS_COL_NOMBRE).value
        # Solo completar filas que tienen nombre pero NO cédula.
        cedula_actual = ws_b.cell(row=fila, column=_BS_COL_CEDULA).value
        if nombre is None or cedula_actual not in (None, ""):
            continue
        clave = _normalizar_nombre(nombre)
        match = indice_nombres.get(clave)
        if match is None:
            continue
        _fila_origen, cedula_origen = match
        if cedula_origen in (None, ""):
            continue
        ws_b.cell(row=fila, column=_BS_COL_CEDULA, value=cedula_origen)
        completadas += 1
    return completadas


def _normalizar_nombre(valor) -> str:
    """Normaliza un nombre para comparación exacta (quita espacios extra)."""
    if valor is None:
        return ""
    return " ".join(str(valor).upper().split())


def _normalizar_valor(valor):
    """Normaliza un valor de celda para usarlo como clave de lookup."""
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return str(valor).strip()
