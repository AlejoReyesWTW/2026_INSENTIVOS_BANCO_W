"""Logger que escribe a un archivo por día en `directorio/YYYY-MM-DD.log`.

Cada línea tiene el formato:
    [YYYY-MM-DD HH:MM:SS] [NIVEL] mensaje

Niveles soportados: INFO, WARNING, ERROR.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path


class NivelLog(Enum):
    """Niveles de severidad soportados por el logger."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LoggerDiario:
    """Logger simple que escribe a un archivo por día.

    Uso:
        logger = LoggerDiario("Logs/")
        logger.info("Iniciando procesamiento...")
        logger.warning("Fila 123 sin match en BUSCARX")
        logger.error("No se pudo leer el archivo X")
    """

    def __init__(self, directorio: Path | str) -> None:
        self.directorio = Path(directorio)
        # Crea el directorio (y padres) si no existe. Idempotente.
        self.directorio.mkdir(parents=True, exist_ok=True)

    def _ruta_archivo_del_dia(self) -> Path:
        """Devuelve la ruta del archivo .log del día actual."""
        nombre = f"{datetime.now().date().isoformat()}.log"
        return self.directorio / nombre

    def _log(self, nivel: NivelLog, mensaje: str) -> None:
        """Escribe una línea en el archivo del día con el nivel dado."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] [{nivel.value}] {mensaje}\n"
        # Append mode ('a') para no sobrescribir entradas previas del mismo día.
        # errors="replace" por si llega un carácter raro.
        with self._ruta_archivo_del_dia().open("a", encoding="utf-8") as f:
            f.write(linea)

    def info(self, mensaje: str) -> None:
        """Registra un mensaje informativo."""
        self._log(
            NivelLog.LINFO if hasattr(NivelLog, "LINFO") else NivelLog.INFO, mensaje
        )

    def warning(self, mensaje: str) -> None:
        """Registra una advertencia."""
        self._log(NivelLog.WARNING, mensaje)

    def error(self, mensaje: str) -> None:
        """Registra un error."""
        self._log(NivelLog.ERROR, mensaje)
