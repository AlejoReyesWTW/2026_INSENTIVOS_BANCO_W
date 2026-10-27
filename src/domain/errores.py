"""Excepciones custom del dominio."""

from __future__ import annotations


class DominioError(Exception):
    """Excepción base para todos los errores del dominio."""


class ConfiguracionInvalidaError(DominioError):
    """El archivo de configuración es inválido o está corrupto."""


class ArchivoNoEncontradoError(DominioError):
    """El archivo esperado no existe en el sistema de archivos."""


class EstructuraInvalidaError(DominioError):
    """La estructura interna del archivo no coincide con la esperada."""


class ColumnaFaltanteError(EstructuraInvalidaError):
    """Falta una columna requerida en la hoja del archivo."""


class HojaFaltanteError(EstructuraInvalidaError):
    """Falta una hoja requerida en el archivo."""


class TipoInsumoDesconocidoError(DominioError):
    """El nombre del insumo no corresponde a ningún TipoInsumo conocido."""

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        super().__init__(f"Tipo de insumo desconocido: {nombre!r}")


class MesAnioNoDetectadoError(DominioError):
    """No se pudo detectar mes/año del nombre del archivo."""


class PlantillaNoEncontradaError(DominioError):
    """La plantilla de salida no existe en la ruta esperada."""
