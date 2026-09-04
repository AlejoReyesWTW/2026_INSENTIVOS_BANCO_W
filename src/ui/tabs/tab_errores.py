"""Tab "Errores" de la UI: muestra errores de validación/validación."""

from __future__ import annotations

import customtkinter as ctk

from src.ui.constants import COLOR_ERROR, COLOR_TEXTO_SECUNDARIO


class TabErrores:
    """Tab que muestra el registro de errores."""

    def __init__(self, parent: ctk.CTk) -> None:
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._crear_widgets()

    def _crear_widgets(self) -> None:
        ctk.CTkLabel(
            self.frame,
            text="Registro de errores",
            font=("Arial", 24, "bold"),
            text_color=COLOR_TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=25, pady=(25, 10))

        self.errores_text = ctk.CTkTextbox(
            self.frame,
            fg_color="#101014",
            text_color=COLOR_ERROR,
            font=("Consolas", 13),
            corner_radius=10,
        )
        self.errores_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def agregar(self, mensaje: str) -> None:
        """Agrega una línea al registro de errores con timestamp."""
        from datetime import datetime

        hora = datetime.now().strftime("%H:%M:%S")
        self.errores_text.configure(state="normal")
        self.errores_text.insert("end", f"[{hora}] {mensaje}\n")
        self.errores_text.see("end")
        self.errores_text.configure(state="disabled")
