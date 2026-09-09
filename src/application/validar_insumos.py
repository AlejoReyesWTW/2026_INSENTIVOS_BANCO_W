"""Caso de uso: validar la estructura de los archivos de insumos.

Recibe un dict de {TipoInsumo: ruta} y un ConfigLoader, y verifica que cada
archivo cumpla con la estructura definida en Configuracion.json (hojas y
columnas requeridas). Devuelve un ResultadoValidacion con el detalle.

Soporta dos estilos de estructura en el config:
  1. Estilo clásico: "hojas": {"NombreHoja": [cols]}
     → La hoja debe llamarse exactamente así.
  2. Estilo dinámico: "hoja_patron": "regex" + "columnas": [cols]
     → Busca la primera hoja que matchee la regex (útil para tabs con
       nombres que cambian, ej: "Soy Prevenido MM_YYYY").

También valida que la extensión del archivo sea .xlsx o .xls.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from src.domain.insumo import TipoInsumo
from src.domain.mapeo import normalizar_header
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.excel_reader import ExcelReader

# Extensiones válidas para archivos Excel.
EXTENSIONES_VALIDAS = (".xlsx", ".xls")


@dataclass
class ResultadoValidacion:
    """Resultado agregado de validar N insumos.

    Attributes:
        valido: True si todos los insumos pasaron la validación.
        errores: dict de TipoInsumo -> lista de mensajes de error.
                Solo incluye los insumos con errores.
    """

    valido: bool
    errores: dict[TipoInsumo, list[str]] = field(default_factory=dict)

    @property
    def total_errores(self) -> int:
        """Suma total de errores en todos los insumos."""
        return sum(len(errs) for errs in self.errores.values())


class ValidadorInsumos:
    """Valida que los archivos de insumos cumplan la estructura esperada."""

    def __init__(self, config_loader: ConfigLoader) -> None:
        self.config = config_loader
        self._estructuras = config_loader.cargar_estructuras()

    def validar(self, insumos: Mapping[TipoInsumo, Path | str]) -> ResultadoValidacion:
        """Valida cada insumo contra su estructura esperada."""
        errores_por_insumo: dict[TipoInsumo, list[str]] = {}

        for tipo, ruta in insumos.items():
            errores: list[str] = []
            ruta_p = Path(ruta)

            # 1. Verificar que el archivo existe.
            if not ruta_p.exists():
                errores.append(f"El archivo no existe: {ruta_p}")
                errores_por_insumo[tipo] = errores
                continue

            # 2. Verificar extensión del archivo (.xlsx o .xls).
            extension = ruta_p.suffix.lower()
            if extension not in EXTENSIONES_VALIDAS:
                errores.append(
                    f"Tipo de archivo no soportado: '{extension}'. "
                    f"Se esperaba {', '.join(EXTENSIONES_VALIDAS)}."
                )
                errores_por_insumo[tipo] = errores
                continue

            # 3. Verificar que el tipo tiene estructura definida en Config.
            estructura = self._estructuras.get(tipo.value)
            if estructura is None:
                continue  # Sin estructura: pasa.

            # 4. Leer el archivo y validar hojas + columnas.
            try:
                reader = ExcelReader(ruta_p)
            except Exception as e:  # noqa: BLE001
                errores.append(f"No se pudo abrir el archivo: {e}")
                errores_por_insumo[tipo] = errores
                continue

            try:
                fila_encabezado = estructura.get("fila_encabezado", 1)
                self._validar_hojas_y_columnas(
                    reader, tipo, estructura, fila_encabezado, errores
                )
            finally:
                reader.cerrar()

            if errores:
                errores_por_insumo[tipo] = errores

        valido = len(errores_por_insumo) == 0
        return ResultadoValidacion(valido=valido, errores=errores_por_insumo)

    def _validar_hojas_y_columnas(
        self,
        reader: ExcelReader,
        tipo: TipoInsumo,
        estructura: dict,
        fila_encabezado: int,
        errores: list[str],
    ) -> None:
        """Valida que la(s) hoja(s) requerida(s) exista(n) con las columnas correctas.

        Soporta dos estilos de estructura:
        1. {"hojas": {"Nombre": [cols]}}  → hojas exactas
        2. {"hoja_patron": "regex", "columnas": [cols]}  → regex match
        """
        hojas_existentes = set(reader.listar_hojas())

        # Estilo 2: hoja_patron (regex) + columnas a nivel raíz.
        hoja_patron = estructura.get("hoja_patron")
        if hoja_patron:
            columnas_requeridas = estructura.get("columnas", [])
            self._validar_con_patron(
                reader,
                tipo,
                hoja_patron,
                columnas_requeridas,
                hoja_patron,
                fila_encabezado,
                hojas_existentes,
                errores,
            )
            return

        # Estilo 1: hojas exactas (clásico).
        hojas_requeridas = estructura.get("hojas", {})
        if not hojas_requeridas:
            errores.append(
                f"Estructura para '{tipo.value}' no tiene 'hojas' ni 'hoja_patron' definidos."
            )
            return

        for nombre_hoja, columnas_requeridas in hojas_requeridas.items():
            if nombre_hoja not in hojas_existentes:
                errores.append(f"No existe la hoja '{nombre_hoja}'.")
                continue

            self._validar_columnas_de_hoja(
                reader,
                tipo,
                nombre_hoja,
                columnas_requeridas,
                fila_encabezado,
                errores,
            )

    def _validar_con_patron(
        self,
        reader: ExcelReader,
        tipo: TipoInsumo,
        patron: str,
        columnas_requeridas: list[str],
        nombre_logico: str,
        fila_encabezado: int,
        hojas_existentes: set[str],
        errores: list[str],
    ) -> None:
        """Valida buscando la primera hoja que matchee el regex."""
        try:
            regex = re.compile(patron)
        except re.error as e:
            errores.append(f"Patrón regex inválido '{patron}': {e}")
            return

        hoja_match = None
        for hoja in hojas_existentes:
            if regex.match(hoja):
                hoja_match = hoja
                break

        if hoja_match is None:
            disponibles = (
                ", ".join(sorted(hojas_existentes)) if hojas_existentes else "(ninguna)"
            )
            errores.append(
                f"No se encontró una hoja que coincida con el patrón '{patron}'. "
                f"Hojas disponibles: {disponibles}"
            )
            return

        # Validar columnas en la hoja encontrada.
        self._validar_columnas_de_hoja(
            reader,
            tipo,
            hoja_match,
            columnas_requeridas,
            fila_encabezado,
            errores,
        )

    def _validar_columnas_de_hoja(
        self,
        reader: ExcelReader,
        tipo: TipoInsumo,
        nombre_hoja: str,
        columnas_requeridas: list[str],
        fila_encabezado: int,
        errores: list[str],
    ) -> None:
        """Lee los encabezados de una hoja y compara contra las columnas requeridas.

        Auto-detecta la fila de encabezados probando varias filas si la indicada
        no contiene las columnas esperadas (útil para archivos con título previo).
        """
        # Filas a intentar: la configurada + las siguientes (hasta 5).
        filas_a_intentar = list(range(fila_encabezado, max(fila_encabezado + 5, 6)))

        encabezados_encontrados: set[str] | None = None
        fila_usada = fila_encabezado

        for fila in filas_a_intentar:
            try:
                encs = set(
                    reader.leer_encabezados(
                        nombre_hoja,
                        fila_encabezado=fila,
                        normalizar=True,
                    )
                )
            except Exception:  # noqa: BLE001
                continue

            # Verificar si al menos UNA columna esperada está en esta fila.
            if any(normalizar_header(c) in encs for c in columnas_requeridas):
                encabezados_encontrados = encs
                fila_usada = fila
                break

        if encabezados_encontrados is None:
            errores.append(
                f"Hoja '{nombre_hoja}': no se encontraron los encabezados esperados "
                f"en ninguna de las filas {filas_a_intentar}. "
                f"Verificá que la fila de encabezados sea alguna de esas."
            )
            return

        # Validar cada columna requerida contra los encabezados encontrados.
        for col_requerida in columnas_requeridas:
            col_normalizada = normalizar_header(col_requerida)
            if col_normalizada not in encabezados_encontrados:
                errores.append(
                    f"Hoja '{nombre_hoja}' (fila {fila_usada}): "
                    f"falta la columna '{col_requerida}'."
                )
