"""Widget: sección colapsable con header clickeable.

Permite mostrar/ocultar contenido con un click en el header.
El contenido se expande verticalmente para llenar el espacio disponible.
"""

from __future__ import annotations

import customtkinter as ctk

from src.ui.constants import COLOR_WHITE, COLOR_WTW_HOVER, COLOR_WTW_SECONDARY


class SeccionColapsable(ctk.CTkFrame):
    """Frame con un header (botón) que expande/colapsa el contenido."""

    def __init__(
        self,
        parent: ctk.CTk,
        titulo: str,
        expandido: bool = True,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._titulo = titulo
        self._expandido = expandido

        # Header (botón para toggle).
        self.header = ctk.CTkButton(
            self,
            text=self._texto_header(),
            command=self._toggle,
            fg_color=COLOR_WTW_SECONDARY,
            hover_color=COLOR_WTW_HOVER,
            text_color=COLOR_WHITE,
            anchor="w",
            height=40,
            font=("Arial", 14, "bold"),
            corner_radius=6,
        )
        self.header.pack(fill="x", padx=2, pady=2)

        # Contenido (se muestra solo si está expandido).
        self.contenido = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        if expandido:
            self.contenido.pack(fill="both", expand=True, padx=2, pady=(2, 8))

    def _texto_header(self) -> str:
        """Texto del header con flecha indicadora."""
        flecha = "▼" if self._expandido else "▶"
        return f"{flecha}  {self._titulo}"

    def _toggle(self) -> None:
        """Expande o colapsa el contenido."""
        if self._expandido:
            self.contenido.pack_forget()
            self._expandido = False
        else:
            self.contenido.pack(fill="both", expand=True, padx=2, pady=(2, 8))
            self._expandido = True
        self.header.configure(text=self._texto_header())

    def expandir(self) -> None:
        """Fuerza la expansión de la sección."""
        if not self._expandido:
            self._toggle()

    def colapsar(self) -> None:
        """Fuerza el colapso de la sección."""
        if self._expandido:
            self._toggle()
