"""Validación de coherencia de mes en los archivos de insumo.

El mes esperado es el MES ACTUAL DEL SISTEMA (decisión del usuario). Si un
insumo trae un mes en su nombre que NO coincide con el esperado, el proceso
debe bloquearse (evita cruces mal: ej. estamos en septiembre y cargan un
archivo de enero).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from src.domain.ciclo import Periodo, detectar_periodo_de_filename

_MESES_ES_INDEX: tuple[str, ...] = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


@dataclass(frozen=True)
class ResultadoValidacionMes:
    """Resultado de la validación de mes de los insumos."""

    valido: bool
    errores: list[str] = field(default_factory=list)


def mes_esperado_actual() -> Periodo:
    """Devuelve el mes/año actual del sistema como Periodo."""
    hoy = date.today()
    return Periodo(mes=_MESES_ES_INDEX[hoy.month], anio=hoy.year)


def validar_mes_insumos(rutas: list[Path | str]) -> ResultadoValidacionMes:
    """Valida que todos los insumos con mes en el nombre coincidan con el actual.

    Args:
        rutas: lista de rutas de los archivos de insumo.

    Returns:
        ResultadoValidacionMes: valido=False si hay algún insumo con mes
        distinto al esperado (con la lista de errores).
    """
    esperado = mes_esperado_actual()
    errores: list[str] = []
    for ruta in rutas:
        periodo_archivo = detectar_periodo_de_filename(Path(ruta).name)
        if periodo_archivo is None:
            continue  # Sin mes en el nombre: no se puede verificar, no bloquea.
        if periodo_archivo.mes != esperado.mes or (
            esperado.anio is not None
            and periodo_archivo.anio is not None
            and periodo_archivo.anio != esperado.anio
        ):
            errores.append(
                f"El archivo '{Path(ruta).name}' indica el periodo "
                f"'{periodo_archivo}' pero el periodo esperado es "
                f"'{esperado}'. Revise el archivo seleccionado."
            )
    return ResultadoValidacionMes(valido=not errores, errores=errores)
