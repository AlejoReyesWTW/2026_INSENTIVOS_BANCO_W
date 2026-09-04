"""Tabla de referencia de primas y generación de fórmulas SI anidadas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prima:
    """Una entrada de la tabla de primas: prima → incentivo cajero/subgerente."""

    valor: int
    cajero: int
    subgerente: int


@dataclass(frozen=True)
class TablaPrimas:
    """Tabla de referencia de primas, configurable desde Configuracion.json.

    Se usa para generar fórmulas SI anidadas en las columnas L (cajero) y M
    (subgerente) de la pestaña Ventas de la salida.
    """

    primas: tuple[Prima, ...]

    def _formula_si(self, columna: str, premio_attr: str, fila: int) -> str:
        """Genera una fórmula SI anidada para el atributo de premio dado.

        Si la tabla está vacía, devuelve "0" (siempre retorna 0).

        Args:
            columna: letra de la columna donde está el VALOR PRIMA (ej: "G").
            premio_attr: "cajero" o "subgerente".
            fila: número de fila en la planilla de salida (>= 2).
        """
        if not self.primas:
            return "0"

        # Construir las anidaciones desde el final hacia el inicio.
        # Iteramos en orden inverso para construir la cadena de SI anidados.
        ref = f"${columna}{fila}"
        partes: list[str] = []
        acumulado = "0"
        for prima in reversed(self.primas):
            premio = getattr(prima, premio_attr)
            condicion = f"SI({ref}={prima.valor};{premio};{acumulado})"
            partes.append(condicion)
            acumulado = condicion
        # `acumulado` ahora contiene toda la cadena de SI anidados.
        return f"={acumulado}"

    def formula_cajero(self, col_prima: str, fila: int) -> str:
        """Genera la fórmula SI para la columna L (premio cajero).

        Args:
            col_prima: letra de la columna donde está VALOR PRIMA (ej: "G").
            fila: número de fila en la planilla de salida.
        """
        return self._formula_si(col_prima, "cajero", fila)

    def formula_subgerente(self, col_prima: str, fila: int) -> str:
        """Genera la fórmula SI para la columna M (premio subgerente).

        Args:
            col_prima: letra de la columna donde está VALOR PRIMA (ej: "G").
            fila: número de fila en la planilla de salida.
        """
        return self._formula_si(col_prima, "subgerente", fila)
