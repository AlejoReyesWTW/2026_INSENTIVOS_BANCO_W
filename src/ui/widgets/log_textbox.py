"""Widget: textbox con formato de log (INFO/WARNING/ERROR con colores)."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from src.ui.constants import COLOR_ERROR, COLOR_TEXTO, COLOR_WARNING


class LogTextbox(ctk.CTkTextbox):
    """Textbox que muestra logs con tags de color para cada nivel."""

    def __init__(self, parent: ctk.CTk, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        # Configurar tags de color.
        self.tag_config("info", foreground=COLOR_TEXTO)
        self.tag_config("warning", foreground=COLOR_WARNING)
        self.tag_config("error", foreground=COLOR_ERROR)

    def agregar(self, mensaje: str, nivel: str = "INFO") -> None:
        """Agrega una línea con timestamp y nivel."""
        hora = datetime.now().strftime("%H:%M:%S")
        nivel_padded = f"{nivel:<7}"  # INFO   / WARNING / ERROR
        self.configure(state="normal")
        self.insert("end", f"[{hora}] {nivel_padded} | {mensaje}\n", nivel.lower())
        self.see("end")
        self.configure(state="disabled")
