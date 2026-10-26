"""Caso de uso: llenar la pestaña Ventas del archivo de salida.

Lee la hoja del archivo SOY PREVENIDO (insumo principal) y mapea 10 columnas
específicas a las posiciones correctas en la pestaña Ventas de la salida.

La hoja se auto-detecta: puede llamarse "Ventas" (clásico) o tener un nombre
dinámico como "Soy Prevenido 06_2026". La detección se hace buscando las
columnas esperadas en cada hoja del archivo.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl

from src.domain.fecha import parsear_fecha
from src.domain.mapeo import normalizar_header
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.excel_writer import ExcelWriter


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
COL_NOMBRE_CAJERO = 11  # Columna K en la salida (1-based).
COL_FECHA_TRANSACCION = 6  # Columna F en la salida (1-based).

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


def _normalizar_fecha(valor):
    """Convierte un valor de fecha a date (normalizado a dd/mm/yyyy).

    Acepta strings en cualquier formato (2/6/26, 2/6/2026, 01/06/2026, etc.),
    date y datetime. Si no se puede parsear, devuelve el valor original.
    """
    fecha = parsear_fecha(valor)
    return fecha if fecha is not None else valor


def _clave_orden_fecha(fila: list) -> tuple:
    """Clave de orden para la columna F (índice 5 en la lista de la fila).

    Devuelve una tupla comparable para ordenar de más antigua a más
    reciente. Las fechas que no se pueden parsear (None, texto inválido)
    quedan al final (segundo elemento 1 + algo grande).
    """
    valor = fila[5] if len(fila) > 5 else None
    fecha = parsear_fecha(valor)
    if fecha is not None:
        return (0, fecha)
    # No parseable (None, texto inválido) → al final.
    return (1, 0)


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
            encs: set[str] = set()
            try:
                encs = set(
                    reader.leer_encabezados(hoja, fila_encabezado=fila, normalizar=True)
                )
            except Exception:  # noqa: BLE001
                # Fila no legible: se prueba con la siguiente.
                encs = set()
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

                # FECHA_TRANSACCION (col F): normalizar a date para que todos
                # los formatos (2/6/26, 2/6/2026, etc.) se vean dd/mm/yyyy.
                if col_destino == COL_FECHA_TRANSACCION:
                    valor = _normalizar_fecha(valor)

                # Aplicar limpieza @ en COD_CAJERO.
                if col_destino == COL_COD_CAJERO:
                    valor = _limpiar_cod_cajero(valor)

                # Quitar espacios al final del NOMBRE_CAJERO (col K) para que
                # la búsqueda de cédula por nombre matchee exacto.
                if col_destino == COL_NOMBRE_CAJERO and isinstance(valor, str):
                    valor = valor.strip()

                fila_out[col_destino - 1] = valor
            filas_para_escribir.append(fila_out)

        # 5b. Ordenar las filas por FECHA_TRANSACCION (col F, índice 5)
        #     de más antigua a más reciente.
        filas_para_escribir.sort(key=_clave_orden_fecha)

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


# ---------------------------------------------------------------------------
# Verificación de copiado: insumo → pestaña Ventas
# ---------------------------------------------------------------------------

# Columnas de la salida (1-based) que forman la huella de cada venta.
_COL_HUELLA_ID = 3  # C IDENTIFICACION
_COL_HUELLA_CUENTA = 5  # E CUENTA CLIENTE
_COL_HUELLA_PRIMA = 7  # G VALOR PRIMA

# Nombres de columna del insumo que forman la misma huella.
_HUELLA_INSUMOS = ("NUMERO_IDENTIFICACION", "CUENTA_CLIENTE", "VALOR_PRIMA")


def _clave_texto(valor: Any) -> str:
    """Normaliza un valor a texto comparable (123.0 → '123')."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def _clave_prima(valor: Any) -> str:
    """Normaliza el valor de prima a texto entero (11597.0 → '11597')."""
    texto = _clave_texto(valor)
    try:
        return str(int(float(texto)))
    except (TypeError, ValueError):
        return texto


def _huella(identificacion: Any, cuenta: Any, prima: Any) -> tuple[str, str, str]:
    """Arma la huella de una venta: (identificación, cuenta, prima)."""
    return (
        _clave_texto(identificacion),
        _clave_texto(cuenta),
        _clave_prima(prima),
    )


def _huellas_insumo(ruta_insumo: Path | str) -> Counter:
    """Lee el insumo y devuelve el multiconjunto de huellas de sus ventas."""
    reader = ExcelReader(ruta_insumo)
    try:
        deteccion = _detectar_hoja_y_fila(reader)
        if deteccion is None:
            return Counter()
        nombre_hoja, fila_encabezado = deteccion
        datos = reader.leer_hoja(
            nombre_hoja, fila_encabezado=fila_encabezado, normalizar=True
        )
        claves = [normalizar_header(c) for c in _HUELLA_INSUMOS]
        huellas: Counter = Counter()
        for fila in datos:
            if not all(clave in fila for clave in claves):
                continue
            huellas[
                _huella(fila[claves[0]], fila[claves[1]], fila[claves[2]])
            ] += 1
        return huellas
    finally:
        reader.cerrar()


def _huellas_salida(ruta_salida: Path | str, fila_fin: int) -> Counter:
    """Lee la pestaña Ventas y devuelve el multiconjunto de huellas."""
    wb = openpyxl.load_workbook(ruta_salida, data_only=True, read_only=True)
    try:
        ws = wb["Ventas"]
        huellas: Counter = Counter()
        for fila in ws.iter_rows(min_row=2, max_row=fila_fin, values_only=True):
            if fila is None:
                continue
            valores = (
                fila[_COL_HUELLA_ID - 1] if len(fila) >= _COL_HUELLA_ID else None,
                fila[_COL_HUELLA_CUENTA - 1]
                if len(fila) >= _COL_HUELLA_CUENTA
                else None,
                fila[_COL_HUELLA_PRIMA - 1]
                if len(fila) >= _COL_HUELLA_PRIMA
                else None,
            )
            if all(v is None for v in valores):
                continue
            huellas[_huella(*valores)] += 1
        return huellas
    finally:
        wb.close()


def _ejemplo_diferencia(esperado: Counter, obtenido: Counter):
    """Devuelve (id, cuenta, prima_insumo, prima_archivo) de una diferencia."""
    for huella, cantidad in esperado.items():
        if obtenido.get(huella, 0) < cantidad:
            identificacion, cuenta, prima_insumo = huella
            candidatas = sorted(
                {h[2] for h in obtenido if h[0] == identificacion and h[1] == cuenta}
            )
            prima_archivo = ", ".join(candidatas) if candidatas else "(no está)"
            return identificacion, cuenta, prima_insumo, prima_archivo
    for huella, cantidad in obtenido.items():
        if esperado.get(huella, 0) < cantidad:
            identificacion, cuenta, prima_archivo = huella
            candidatas = sorted(
                {h[2] for h in esperado if h[0] == identificacion and h[1] == cuenta}
            )
            prima_insumo = ", ".join(candidatas) if candidatas else "(no está)"
            return identificacion, cuenta, prima_insumo, prima_archivo
    return None


def verificar_copiado_ventas(
    ruta_insumo: Path | str,
    ruta_salida: Path | str,
    fila_fin: int,
) -> None:
    """Verifica que la pestaña Ventas copió fielmente (id, cuenta, prima).

    Compara el multiconjunto de huellas del insumo contra el de la pestaña
    Ventas generada. No le importa el orden de las filas (Ventas se ordena
    por fecha), solo que exista la misma cantidad de cada venta.

    Args:
        ruta_insumo: ruta al archivo SOY PREVENIDO usado como entrada.
        ruta_salida: ruta al archivo generado.
        fila_fin: última fila de datos de Ventas (1-based, inclusiva).

    Raises:
        CruceDatosInsumoError: si las huellas no coinciden. El mensaje indica
            cuántas filas difieren y un ejemplo concreto.
    """
    from src.domain.errores import CruceDatosInsumoError

    esperado = _huellas_insumo(ruta_insumo)
    obtenido = _huellas_salida(ruta_salida, fila_fin)
    if esperado == obtenido:
        return

    faltantes = sum((esperado - obtenido).values())
    sobrantes = sum((obtenido - esperado).values())
    diferencia = _ejemplo_diferencia(esperado, obtenido)
    detalle = ""
    if diferencia is not None:
        identificacion, cuenta, prima_insumo, prima_archivo = diferencia
        detalle = (
            f" Ejemplo: asegurado {identificacion or '(vacío)'} / "
            f"cuenta {cuenta or '(vacía)'} -> "
            f"prima en el insumo {prima_insumo or '(vacía)'}; "
            f"prima en el archivo {prima_archivo}."
        )

    raise CruceDatosInsumoError(
        "El copiado a la pestaña Ventas NO coincide con el insumo: "
        f"{faltantes} fila(s) del insumo no están en el generado y "
        f"{sobrantes} fila(s) del generado no están en el insumo."
        f"{detalle} Revise que el archivo de entrada no tenga columnas "
        "desordenadas (agencia, asegurado, cuenta y prima de la misma fila)."
    )
