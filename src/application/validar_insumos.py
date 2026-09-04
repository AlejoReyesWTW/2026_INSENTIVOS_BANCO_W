"""Caso de uso: validar la estructura de los archivos de insumos.

Recibe un dict de {TipoInsumo: ruta} y un ConfigLoader, y verifica que cada
archivo cumpla con la estructura definida en Configuracion.json (hojas y
columnas requeridas). Devuelve un ResultadoValidacion con el detalle.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from src.domain.insumo import TipoInsumo
from src.domain.mapeo import normalizar_header
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.excel_reader import ExcelReader


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
        """Valida cada insumo contra su estructura esperada.

        Args:
            insumos: dict {TipoInsumo: ruta_al_archivo}.

        Returns:
            ResultadoValidacion con valido=True/False y detalle de errores.
            Si un TipoInsumo no tiene estructura definida en Config.json,
            se considera válido (sin reglas para validar).
        """
        errores_por_insumo: dict[TipoInsumo, list[str]] = {}

        for tipo, ruta in insumos.items():
            errores: list[str] = []
            ruta_p = Path(ruta)

            # 1. Verificar que el archivo existe.
            if not ruta_p.exists():
                errores.append(f"El archivo no existe: {ruta_p}")
                errores_por_insumo[tipo] = errores
                continue

            # 2. Verificar que el tipo tiene estructura definida en Config.
            estructura = self._estructuras.get(tipo.value)
            if estructura is None:
                # Sin estructura definida: no se valida, pasa.
                continue

            # 3. Leer el archivo y validar hojas + columnas.
            try:
                reader = ExcelReader(ruta_p)
            except Exception as e:  # noqa: BLE001 - capturamos cualquier error de apertura
                errores.append(f"No se pudo abrir el archivo: {e}")
                errores_por_insumo[tipo] = errores
                continue

            try:
                hojas_requeridas = estructura.get("hojas", {})
                fila_encabezado = estructura.get("fila_encabezado", 1)
                self._validar_hojas_y_columnas(
                    reader,
                    tipo,
                    hojas_requeridas,
                    fila_encabezado,
                    errores,
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
        hojas_requeridas: dict[str, list[str]],
        fila_encabezado: int,
        errores: list[str],
    ) -> None:
        """Valida que las hojas requeridas existan con las columnas correctas.

        Modifica la lista `errores` in-place agregando mensajes por cada issue.
        """
        hojas_existentes = set(reader.listar_hojas())
        for nombre_hoja, columnas_requeridas in hojas_requeridas.items():
            # ¿Existe la hoja?
            if nombre_hoja not in hojas_existentes:
                errores.append(f"No existe la hoja '{nombre_hoja}'.")
                continue

            # Leer SOLO los encabezados (no las filas de datos) para validar.
            try:
                encabezados_presentes = set(
                    reader.leer_encabezados(
                        nombre_hoja,
                        fila_encabezado=fila_encabezado,
                        normalizar=True,
                    )
                )
            except Exception as e:  # noqa: BLE001
                errores.append(f"No se pudo leer la hoja '{nombre_hoja}': {e}")
                continue

            # Comparar contra las columnas requeridas (normalizadas).
            for col_requerida in columnas_requeridas:
                col_normalizada = normalizar_header(col_requerida)
                if col_normalizada not in encabezados_presentes:
                    errores.append(
                        f"Hoja '{nombre_hoja}': falta la columna '{col_requerida}'."
                    )
