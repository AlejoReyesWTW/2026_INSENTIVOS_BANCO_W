"""Caso de uso: escribir VALORES COMPUTADOS en J, L, M, N, O, P, Q, R, S de Ventas.

Razon: openpyxl escribe formulas de una forma que Excel no parsea
correctamente (causa corrupcion del archivo: "LIBRO REPARADO, Registros
quitados: Formula"). Ademas BUSCARX no existe en Google Sheets (#NAME?).
Solucion: calcular TODO en Python y escribir solo VALORES, no formulas.

Columnas escritas:
  J (10) = CEDULA (lookup en Base red agencias por USUARIO WINDOWS)
  L (12) = CAJERO (137/290/378/658 segun VALOR_PRIMA)
  M (13) = SUBGERENTE (34/72/95/164 segun VALOR_PRIMA)
  N (14) = replica de A (CODIGO AGENCIA)
  O (15) = replica de B (NOMBRE AGENCIA)
  P (16) = CEDULA (lookup en Base subgerentes por COD_AGENCIA en col H)
  Q (17) = NOMBRE (lookup en Base subgerentes por COD_AGENCIA en col H)
  R (18) = replica de P
  S (19) = replica de Q
"""

from __future__ import annotations

# Constantes de columnas (1-based).
_COL_J = 10  # CC_CAJERO
_COL_L = 12  # CAJERO
_COL_M = 13  # SUBGERENTE
_COL_N = 14  # COD (replica de A)
_COL_O = 15  # AGENCIA2 (replica de B)
_COL_P = 16  # CC_SUBGERENTE
_COL_Q = 17  # NOMBRE_SUBGERENTE
_COL_R = 18  # replica de P
_COL_S = 19  # replica de Q


def _diagnosticar_lookups(writer, logger, fila_inicio, fila_fin):
    """Diagnostica si los lookups van a funcionar."""
    try:
        wb = writer._workbook
        if "Ventas" not in wb.sheetnames:
            logger.warning("Hoja Ventas no existe.")
            return
        ws_ventas = wb["Ventas"]
        cod_cajeros = set()
        cod_agencias = set()
        for fila in range(fila_inicio, fila_fin + 1):
            val_i = ws_ventas.cell(row=fila, column=9).value
            if val_i is not None and str(val_i).strip():
                cod_cajeros.add(str(val_i).strip())
            val_a = ws_ventas.cell(row=fila, column=1).value
            if val_a is not None:
                s_a = str(val_a).strip()
                if s_a.isdigit():
                    cod_agencias.add(int(s_a))
        logger.info(
            f"[diagnostico] Ventas: {len(cod_cajeros)} COD_CAJERO unicos, "
            f"{len(cod_agencias)} CODIGO_AGENCIA unicos."
        )
        if "Base red agencias" in wb.sheetnames:
            ws_ra = wb["Base red agencias"]
            usuarios_ra = set()
            for fila in range(2, ws_ra.max_row + 1):
                val = ws_ra.cell(row=fila, column=1).value
                if val is not None and str(val).strip():
                    usuarios_ra.add(str(val).strip())
            logger.info(f"[diagnostico] Base red agencias: {len(usuarios_ra)} usuarios unicos.")
            matches_j = cod_cajeros & usuarios_ra
            no_match_j = cod_cajeros - usuarios_ra
            pct_j = len(matches_j) / len(cod_cajeros) * 100 if cod_cajeros else 0
            logger.info(
                f"[diagnostico] BUSCARX J: {len(matches_j)}/{len(cod_cajeros)} matchean ({pct_j:.1f}%)."
            )
            if no_match_j:
                logger.warning(f"[diagnostico] BUSCARX J: {len(no_match_j)} COD_CAJERO sin match.")
                if len(no_match_j) <= 30:
                    logger.warning(f"[diagnostico] BUSCARX J: lista no-matches: {sorted(no_match_j)}")
                else:
                    logger.warning(f"[diagnostico] BUSCARX J: muestra 30 no-matches: {sorted(no_match_j)[:30]}")
        else:
            logger.error("[diagnostico] Hoja Base red agencias NO EXISTE.")
        if "Base subgerentes" in wb.sheetnames:
            ws_bs = wb["Base subgerentes"]
            cod_agencias_bs = set()
            for fila in range(2, ws_bs.max_row + 1):
                val = ws_bs.cell(row=fila, column=8).value
                if val is not None:
                    s_h = str(val).strip()
                    if s_h.isdigit():
                        cod_agencias_bs.add(int(s_h))
            logger.info(f"[diagnostico] Base subgerentes: {len(cod_agencias_bs)} COD_AGENCIA unicos.")
            matches_pq = cod_agencias & cod_agencias_bs
            no_match_pq = cod_agencias - cod_agencias_bs
            pct_pq = len(matches_pq) / len(cod_agencias) * 100 if cod_agencias else 0
            logger.info(
                f"[diagnostico] BUSCARX P/Q: {len(matches_pq)}/{len(cod_agencias)} matchean ({pct_pq:.1f}%)."
            )
            if no_match_pq:
                logger.warning(f"[diagnostico] BUSCARX P/Q: {len(no_match_pq)} CODIGO_AGENCIA sin match.")
                if len(no_match_pq) <= 30:
                    logger.warning(f"[diagnostico] BUSCARX P/Q: lista no-matches: {sorted(no_match_pq)}")
                else:
                    logger.warning(f"[diagnostico] BUSCARX P/Q: muestra 30 no-matches: {sorted(no_match_pq)[:30]}")
        else:
            logger.error("[diagnostico] Hoja Base subgerentes NO EXISTE.")
    except (AttributeError, KeyError, ValueError) as e:
        logger.warning(f"[diagnostico] No se pudo verificar lookups: {e}")


def _leer_indices_lookups(writer):
    """Lee Base red agencias y Base subgerentes y devuelve dicts para lookup."""
    wb = writer._workbook
    usuarios_ra = {}
    if "Base red agencias" in wb.sheetnames:
        ws_ra = wb["Base red agencias"]
        for fila in range(2, ws_ra.max_row + 1):
            usuario = ws_ra.cell(row=fila, column=1).value
            cedula = ws_ra.cell(row=fila, column=3).value
            if usuario is not None and cedula is not None:
                usuarios_ra[str(usuario).strip()] = cedula
    empleados_bs = {}
    if "Base subgerentes" in wb.sheetnames:
        ws_bs = wb["Base subgerentes"]
        for fila in range(2, ws_bs.max_row + 1):
            cod = ws_bs.cell(row=fila, column=8).value
            cedula = ws_bs.cell(row=fila, column=1).value
            nombre = ws_bs.cell(row=fila, column=2).value
            if cod is not None and (cedula is not None or nombre is not None):
                s = str(cod).strip()
                cod_int = int(s) if s.isdigit() else cod
                empleados_bs[cod_int] = (cedula, nombre)
    return usuarios_ra, empleados_bs


def insertar_formulas_ventas(
    writer, tabla_primas, fila_inicio=2, fila_fin=31362, col_prima="G", logger=None,
):
    """Escribe VALORES COMPUTADOS en J, L, M, N, O, P, Q, R, S de Ventas.

    NO escribe formulas para evitar:
    1. Corrupcion del archivo Excel (openpyxl escribe formulas mal)
    2. Error #NAME? en Google Sheets (BUSCARX no existe ahi)

    Los valores se calculan en Python y se escriben directamente.
    """
    total_filas = fila_fin - fila_inicio + 1

    def _log(msg):
        if logger is not None:
            logger.info(f"[insertar_formulas_ventas] {msg}")

    _log(f"Escribiendo valores en filas {fila_inicio}-{fila_fin} ({total_filas} filas)")

    if logger is not None:
        _diagnosticar_lookups(writer, logger, fila_inicio, fila_fin)

    usuarios_ra, empleados_bs = _leer_indices_lookups(writer)
    if logger is not None:
        logger.info(
            f"[insertar_formulas_ventas] Lookups: "
            f"{len(usuarios_ra)} usuarios en Base red agencias, "
            f"{len(empleados_bs)} COD_AGENCIA en Base subgerentes"
        )

    wb = writer._workbook
    ws = wb["Ventas"]

    for fila in range(fila_inicio, fila_fin + 1):
        i_val = ws.cell(row=fila, column=9).value
        a_val = ws.cell(row=fila, column=1).value
        b_val = ws.cell(row=fila, column=2).value

        # J (10): CEDULA = lookup en Base red agencias por USUARIO WINDOWS
        if i_val is not None and isinstance(i_val, str):
            usuario_buscado = i_val.strip()
            j_valor = usuarios_ra.get(usuario_buscado)
            if j_valor is None:
                # Intentar sin distinguir mayusculas/minusculas
                usuario_lower = usuario_buscado.lower()
                for u, c in usuarios_ra.items():
                    if u.lower() == usuario_lower:
                        j_valor = c
                        break
        else:
            j_valor = None
        ws.cell(row=fila, column=_COL_J).value = j_valor

        # L (12): CAJERO segun VALOR_PRIMA (137/290/378/658)
        l_valor = _calcular_cajero(g_val=ws.cell(row=fila, column=7).value)
        ws.cell(row=fila, column=_COL_L).value = l_valor

        # M (13): SUBGERENTE segun VALOR_PRIMA (34/72/95/164)
        m_valor = _calcular_subgerente(g_val=ws.cell(row=fila, column=7).value)
        ws.cell(row=fila, column=_COL_M).value = m_valor

        # N (14): replica de A (CODIGO AGENCIA)
        ws.cell(row=fila, column=_COL_N).value = a_val

        # O (15): replica de B (NOMBRE AGENCIA)
        ws.cell(row=fila, column=_COL_O).value = b_val

        # P (16): CEDULA = lookup en Base subgerentes por COD_AGENCIA
        if a_val is not None:
            try:
                cod_int = int(a_val)
            except (TypeError, ValueError):
                cod_int = a_val
            p_valor = empleados_bs.get(cod_int, (None, None))[0]
        else:
            p_valor = None
        ws.cell(row=fila, column=_COL_P).value = p_valor

        # Q (17): NOMBRE = lookup en Base subgerentes por COD_AGENCIA
        if a_val is not None:
            try:
                cod_int = int(a_val)
            except (TypeError, ValueError):
                cod_int = a_val
            q_valor = empleados_bs.get(cod_int, (None, None))[1]
        else:
            q_valor = None
        ws.cell(row=fila, column=_COL_Q).value = q_valor

        # R (18): replica de P
        ws.cell(row=fila, column=_COL_R).value = p_valor

        # S (19): replica de Q
        ws.cell(row=fila, column=_COL_S).value = q_valor

    _log(f"Valores escritos en {total_filas} filas")
    _log("Total: 9 columnas (J, L, M, N, O, P, Q, R, S) con valores computados")


def _calcular_cajero(g_val):
    """Calcula el incentivo de cajero segun VALOR_PRIMA."""
    if g_val is None:
        return None
    try:
        g = int(g_val)
    except (TypeError, ValueError):
        return None
    tabla = {2414: 137, 5072: 290, 6644: 378, 11597: 658}
    return tabla.get(g, 0)


def _calcular_subgerente(g_val):
    """Calcula el incentivo de subgerente segun VALOR_PRIMA."""
    if g_val is None:
        return None
    try:
        g = int(g_val)
    except (TypeError, ValueError):
        return None
    tabla = {2414: 34, 5072: 72, 6644: 95, 11597: 164}
    return tabla.get(g, 0)
