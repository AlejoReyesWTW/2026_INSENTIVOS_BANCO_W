"""Parseo y formato de fechas del dominio (normalización a dd/mm/yyyy).

Centraliza el parseo de fechas para que TODOS los formatos posibles del
insumo se interpreten igual:
  - dd/mm/yyyy   (01/06/2026)
  - d/m/yy       (2/6/26)   ← dígitos sin cero, año de 2 dígitos
  - d/m/yyyy     (2/6/2026)
  - dd-mm-yyyy   (01-06-2026)
  - yyyy-mm-dd   (2026-06-01)
  - yyyy/mm/dd   (2026/06/01)

Y normaliza cualquier fecha a string "dd/mm/yyyy" (con ceros a la izquierda).
"""

from __future__ import annotations

from datetime import date, datetime

# Orden importa: primero los que exigen 4 dígitos de año, luego los de 2.
# strptime con %d/%m acepta dígitos sin cero (ej: "2/6").
FORMATOS_FECHA: tuple[str, ...] = (
    "%d/%m/%Y",  # 01/06/2026  y  2/6/2026
    "%d/%m/%y",  # 2/6/26
    "%Y-%m-%d",  # 2026-06-01
    "%d-%m-%Y",  # 01-06-2026
    "%d-%m-%y",  # 2-6-26
    "%Y/%m/%d",  # 2026/06/01
)


def parsear_fecha(valor) -> date | None:
    """Convierte un valor a date; None si no se puede parsear.

    Acepta date, datetime y strings en todos los formatos de FORMATOS_FECHA.
    Los años de 2 dígitos se interpretan como 20XX (2000-2099).
    """
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto:
        return None
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None


def formatear_fecha(valor) -> str:
    """Normaliza un valor de fecha a string "dd/mm/yyyy".

    Si el valor no se puede parsear, devuelve el texto original (o "").
    """
    fecha = parsear_fecha(valor)
    if fecha is None:
        return str(valor).strip() if valor is not None else ""
    return fecha.strftime("%d/%m/%Y")
