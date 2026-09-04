"""Tab "Ejecución" de la UI.

Contiene DOS vistas apiladas en la misma pestaña:
- Arriba: Log de ejecución (LogTextbox con colores INFO/WARNING/ERROR)
- Abajo: Registro de errores (textbox rojo)
"""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from src.ui.constants import COLOR_ERROR, COLOR_TEXTO_SECUNDARIO, COLOR_WTW_HOVER
from src.ui.widgets import LogTextbox


class TabLogs:
    """Tab que muestra log de ejecución y registro de errores en la misma vista."""

    def __init__(self, parent: ctk.CTk) -> None:
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._crear_widgets()

    def _crear_widgets(self) -> None:
        # Título principal.
        ctk.CTkLabel(
            self.frame,
            text="Ejecución",
            font=("Arial", 24, "bold"),
            text_color=COLOR_TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=25, pady=(20, 10))

        # --- Vista superior: Log de ejecución ---
        seccion_log = ctk.CTkFrame(self.frame, fg_color="transparent")
        seccion_log.pack(fill="both", expand=True, padx=25, pady=(0, 5))

        ctk.CTkLabel(
            seccion_log,
            text="Log de ejecución",
            font=("Arial", 13, "bold"),
            text_color=COLOR_TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.log = LogTextbox(
            seccion_log,
            fg_color="#101014",
            text_color=COLOR_WTW_HOVER,
            font=("Consolas", 12),
            corner_radius=8,
        )
        self.log.pack(fill="both", expand=True)

        # --- Vista inferior: Registro de errores ---
        seccion_errores = ctk.CTkFrame(self.frame, fg_color="transparent")
        seccion_errores.pack(fill="both", expand=True, padx=25, pady=(5, 15))

        ctk.CTkLabel(
            seccion_errores,
            text="Registro de errores",
            font=("Arial", 13, "bold"),
            text_color=COLOR_ERROR,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.errores_text = ctk.CTkTextbox(
            seccion_errores,
            fg_color="#101014",
            text_color=COLOR_ERROR,
            font=("Consolas", 12),
            corner_radius=8,
        )
        self.errores_text.pack(fill="both", expand=True)

    def agregar(self, mensaje: str, nivel: str = "INFO") -> None:
        """Agrega una línea al log de ejecución."""
        self.log.agregar(mensaje, nivel)

    def agregar_error(self, mensaje: str) -> None:
        """Agrega una línea al registro de errores (vista inferior)."""
        hora = datetime.now().strftime("%H:%M:%S")
        self.errores_text.configure(state="normal")
        self.errores_text.insert("end", f"[{hora}] {mensaje}\n")
        self.errores_text.see("end")
        self.errores_text.configure(state="disabled")
