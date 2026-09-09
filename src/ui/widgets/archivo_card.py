"""Widget: card que muestra un archivo generado con icono Excel y botón Descargar."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from src.ui.constants import COLOR_OK, COLOR_WHITE


class ArchivoGeneradoCard(ctk.CTkFrame):
    """Card verde-blanco que muestra un archivo generado (.xlsx).

    Layout:
        ┌──────────────────────┐
        │         📊           │  ← Icono Excel (emoji)
        │                      │
        │   nombre.xlsx        │  ← Nombre del archivo
        │                      │
        │   [ Descargar ]      │  ← Botón
        └──────────────────────┘
    """

    def __init__(
        self,
        parent: ctk.CTk,
        ruta: Path,
        titulo: str = "",
        on_descargar: callable = None,  # type: ignore[type-arg]
    ) -> None:
        super().__init__(
            parent,
            fg_color=COLOR_WHITE,
            border_color=COLOR_OK,
            border_width=2,
            corner_radius=10,
        )
        self._ruta = ruta
        self._titulo = titulo
        self._on_descargar = on_descargar

        self._crear_widgets()

    def _crear_widgets(self) -> None:
        # Icono Excel (emoji grande, verde).
        self.icono = ctk.CTkLabel(
            self,
            text="📊",
            font=("Arial", 56),
            text_color=COLOR_OK,
        )
        self.icono.pack(pady=(20, 5))

        # Título (opcional, ej: "Base incentivos (mes/año)").
        if self._titulo:
            self.label_titulo = ctk.CTkLabel(
                self,
                text=self._titulo,
                font=("Arial", 11),
                text_color="#6b7280",
                wraplength=180,
                justify="center",
            )
            self.label_titulo.pack(pady=(0, 2))

        # Nombre del archivo.
        self.label_nombre = ctk.CTkLabel(
            self,
            text=self._ruta.name,
            font=("Arial", 12, "bold"),
            text_color="#181818",
            wraplength=180,
            justify="center",
        )
        self.label_nombre.pack(pady=(2, 10))

        # Botón Descargar.
        self.btn_descargar = ctk.CTkButton(
            self,
            text="📥 Descargar",
            command=self._on_click_descargar,
            fg_color=COLOR_OK,
            hover_color="#16a34a",
            text_color=COLOR_WHITE,
            width=130,
            height=32,
            font=("Arial", 12, "bold"),
        )
        self.btn_descargar.pack(pady=(5, 15))

    def set_ruta(self, ruta: Path) -> None:
        """Actualiza el archivo que muestra el card."""
        self._ruta = ruta
        self.label_nombre.configure(text=ruta.name)

    def _on_click_descargar(self) -> None:
        """Llama al callback de descarga."""
        if self._on_descargar is not None:
            self._on_descargar(self._ruta)
