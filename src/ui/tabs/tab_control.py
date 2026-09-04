"""Tab "Control" de la UI: botones Pausar / Reanudar / Detener + estado del bot."""

from __future__ import annotations

import customtkinter as ctk

from src.ui.constants import (
    COLOR_ERROR,
    COLOR_PANEL,
    COLOR_TEXTO_SECUNDARIO,
    COLOR_WARNING,
    COLOR_WTW,
    COLOR_WTW_HOVER,
)


class TabControl:
    """Tab con botones de control del bot y un label de estado."""

    def __init__(self, parent: ctk.CTk) -> None:
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._crear_widgets()

    def _crear_widgets(self) -> None:
        ctk.CTkLabel(
            self.frame,
            text="Control del asistente",
            font=("Arial", 24, "bold"),
            text_color=COLOR_TEXTO_SECUNDARIO,
        ).pack(pady=(30, 20))

        # Botones (Pausar/Reanudar no implementados en v1 pero los dejo por layout).
        ctk.CTkButton(
            self.frame,
            text="Ⅱ  PAUSAR ASISTENTE",
            width=280,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color=COLOR_WARNING,
            hover_color="#D97706",
            command=lambda: None,  # noqa: ARG005 - placeholder
        ).pack(pady=8)

        ctk.CTkButton(
            self.frame,
            text="▶  REANUDAR ASISTENTE",
            width=280,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color=COLOR_WTW,
            hover_color=COLOR_WTW_HOVER,
            command=lambda: None,  # noqa: ARG005 - placeholder
        ).pack(pady=8)

        ctk.CTkButton(
            self.frame,
            text="■  DETENER BOT",
            width=280,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color=COLOR_ERROR,
            hover_color="#DC2626",
            command=lambda: None,  # noqa: ARG005 - placeholder
        ).pack(pady=8)

        # Info box con estado.
        info_frame = ctk.CTkFrame(self.frame, fg_color=COLOR_PANEL, corner_radius=10)
        info_frame.pack(fill="x", padx=80, pady=30)

        self.info_label = ctk.CTkLabel(
            info_frame,
            text="Registros procesados: 0    |    Errores: 0    |    Tiempo: 00:00:00",
            font=("Consolas", 14),
            text_color="#ffffff",
        )
        self.info_label.pack(pady=20)
