"""Cargador de Configuracion.json.

Expone el contenido validado del archivo de configuración a través de métodos
tipados (cargar_estructuras, cargar_tabla_primas, cargar_filtros_cargo).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.domain.errores import ConfiguracionInvalidaError
from src.domain.tabla_primas import Prima, TablaPrimas


@dataclass(frozen=True)
class FiltrosCargo:
    """Filtros de CARGO usados al poblar pestañas de soporte."""

    subgerente_oficina: str
    red_agencias: tuple[str, ...]


class ConfigLoader:
    """Carga y valida el archivo Configuracion.json del proyecto."""

    def __init__(self, ruta: Path | str) -> None:
        self.ruta = Path(ruta)
        self._datos: dict = self._cargar_y_validar()

    def _cargar_y_validar(self) -> dict:
        """Lee el JSON y valida que tenga las claves mínimas."""
        if not self.ruta.exists():
            raise ConfiguracionInvalidaError(
                f"No se encontró el archivo de configuración: {self.ruta}"
            )
        try:
            contenido = self.ruta.read_text(encoding="utf-8")
            datos = json.loads(contenido)
        except json.JSONDecodeError as e:
            raise ConfiguracionInvalidaError(
                f"El archivo {self.ruta} tiene un formato JSON inválido: {e}"
            ) from e
        except OSError as e:
            raise ConfiguracionInvalidaError(f"No se pudo leer {self.ruta}: {e}") from e
        if "estructuras_requeridas" not in datos:
            raise ConfiguracionInvalidaError(
                f"El archivo {self.ruta} no contiene la clave 'estructuras_requeridas'."
            )
        return datos

    def cargar_estructuras(self) -> dict:
        """Devuelve el dict de estructuras requeridas (por tipo de insumo).

        Cada valor es un dict con claves:
            - 'hojas': dict[nombre_hoja, list[str]] de columnas requeridas.
            - 'fila_encabezado': int opcional (default 1).
        """
        return self._datos["estructuras_requeridas"]

    def cargar_tabla_primas(self) -> TablaPrimas:
        """Devuelve la tabla de primas como TablaPrimas (tupla de Prima).

        Prioridad:
          1. Archivo Base_Comisiones_Insentivos.xlsx (si está configurado
             en `tabla_comisiones.path` y existe).
          2. Sección `tabla_primas` del Configuracion.json (fallback).

        Si el banco cambia la tabla en el xlsx, los cálculos se ajustan
        automáticamente sin tocar código.
        """
        tabla_xlsx = self._cargar_tabla_primas_desde_xlsx()
        if tabla_xlsx is not None:
            return tabla_xlsx

        primas_raw = self._datos.get("tabla_primas", [])
        primas: list[Prima] = []
        for idx, entry in enumerate(primas_raw):
            try:
                primas.append(
                    Prima(
                        valor=int(entry["prima"]),
                        cajero=int(entry["cajero"]),
                        subgerente=int(entry["subgerente"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as e:
                raise ConfiguracionInvalidaError(
                    f"Entrada inválida en tabla_primas[{idx}]: {e}"
                ) from e
        return TablaPrimas(tuple(primas))

    def _cargar_tabla_primas_desde_xlsx(self) -> TablaPrimas | None:
        """Lee la tabla desde el xlsx de comisiones si está disponible."""
        path_rel = self._datos.get("tabla_comisiones", {}).get("path")
        if not path_rel:
            return None
        ruta_xlsx = Path(path_rel)
        if not ruta_xlsx.is_absolute():
            ruta_xlsx = self.ruta.parent / ruta_xlsx
        if not ruta_xlsx.exists():
            return None
        try:
            from src.infrastructure.comisiones_reader import (
                leer_tabla_comisiones,
            )

            return leer_tabla_comisiones(ruta_xlsx)
        except (OSError, ValueError, KeyError) as e:
            raise ConfiguracionInvalidaError(
                f"No se pudo leer la tabla de comisiones desde {ruta_xlsx}: {e}"
            ) from e

    def cargar_filtros_cargo(self) -> FiltrosCargo:
        """Devuelve los filtros de CARGO para las pestañas de soporte."""
        filtros_raw = self._datos.get("filtros_cargo", {})
        subgerente = filtros_raw.get("subgerente_oficina", "SUBGERENTE DE OFICINA")
        red = tuple(filtros_raw.get("red_agencias", []))
        return FiltrosCargo(subgerente_oficina=subgerente, red_agencias=red)

    def cargar_correcciones_nombres_path(self) -> str | None:
        """Devuelve la ruta al archivo de correcciones de nombres si está configurado.

        Se lee de la sección `correcciones_nombres.path` (ruta relativa al
        directorio del Configuracion.json). Devuelve None si no está.
        """
        path_rel = self._datos.get("correcciones_nombres", {}).get("path")
        if not path_rel:
            return None
        ruta = Path(path_rel)
        if not ruta.is_absolute():
            ruta = self.ruta.parent / ruta
        return str(ruta)
