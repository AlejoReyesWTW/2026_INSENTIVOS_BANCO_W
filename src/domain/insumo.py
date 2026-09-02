"""Tipos de insumo y mapeo desde Configuracion.json."""

from __future__ import annotations

from enum import Enum

from src.domain.errores import TipoInsumoDesconocidoError


class TipoInsumo(Enum):
    """Los 6 tipos de insumos que el aplicativo consume."""

    DIRECTORIO_NACIONAL = "Directorio Nacional"
    NOVEDADES_SUBGERENTE = "Formato novedades subgerente oficina para seguros"
    BASE_TEMPORAL = "Base Temporal Completa SS"
    BASE_BANCO = "Base Banco Completa SS"
    BASE_SEGUROS = "Base Seguros – Actualizada"
    SOY_PREVENIDO = "Soy Prevenido"


# Alias aceptados para Base Seguros (puede venir con guion normal o en-dash).
_ALIAS_BASE_SEGUROS: set[str] = {
    "Base Seguros – Actualizada",  # en-dash (como está en Config.json v1.1)
    "Base Seguros - Actualizada",  # guion normal
}


def validar_tipo(nombre: str) -> TipoInsumo:
    """Mapea un nombre de insumo (de Config.json) a su TipoInsumo.

    Raises:
        TipoInsumoDesconocidoError: si el nombre no corresponde a ningún tipo.
    """
    if nombre in _ALIAS_BASE_SEGUROS:
        return TipoInsumo.BASE_SEGUROS
    for tipo in TipoInsumo:
        if tipo.value == nombre:
            return tipo
    raise TipoInsumoDesconocidoError(nombre)
