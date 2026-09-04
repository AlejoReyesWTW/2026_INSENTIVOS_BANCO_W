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
        """Devuelve la tabla de primas como TablaPrimas (tupla de Prima)."""
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

    def cargar_filtros_cargo(self) -> FiltrosCargo:
        """Devuelve los filtros de CARGO para las pestañas de soporte."""
        filtros_raw = self._datos.get("filtros_cargo", {})
        subgerente = filtros_raw.get("subgerente_oficina", "SUBGERENTE DE OFICINA")
        red = tuple(filtros_raw.get("red_agencias", []))
        return FiltrosCargo(subgerente_oficina=subgerente, red_agencias=red)
