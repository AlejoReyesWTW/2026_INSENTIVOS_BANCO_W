"""Tab "Ejecución" de la UI: muestra el log de la corrida en curso."""

from __future__ import annotations

import customtkinter as ctk

from src.ui.constants import COLOR_TEXTO_SECUNDARIO, COLOR_WTW_HOVER
from src.ui.widgets import LogTextbox


class TabLogs:
    """Tab que muestra el log de ejecución (INFO/WARNING/ERROR)."""

    def __init__(self, parent: ctk.CTk) -> None:
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._crear_widgets()

    def _crear_widgets(self) -> None:
        ctk.CTkLabel(
            self.frame,
            text="Log de ejecución",
            font=("Arial", 24, "bold"),
            text_color=COLOR_TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=25, pady=(25, 10))

        self.log = LogTextbox(
            self.frame,
            fg_color="#101014",
            text_color=COLOR_WTW_HOVER,
            font=("Consolas", 13),
            corner_radius=10,
        )
        self.log.pack(fill="both", expand=True, padx=25, pady=(0, 25))

    def agregar(self, mensaje: str, nivel: str = "INFO") -> None:
        """Agrega una línea al log."""
        self.log.agregar(mensaje, nivel)
