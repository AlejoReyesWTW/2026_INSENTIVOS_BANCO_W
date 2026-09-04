"""Widget: bloque para seleccionar un archivo de insumo.

Layout:
- Fila 1: [Nombre del tipo] ......... [Estado] [Buscar]
- Fila 2: Etiqueta dinámica (vacía al inicio; muestra el archivo cargado
  o los errores de validación cuando aplica)
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from src.domain.insumo import TipoInsumo
from src.ui.constants import (
    COLOR_ERROR,
    COLOR_INPUT_BG,
    COLOR_INPUT_BORDER,
    COLOR_INPUT_TEXT,
    COLOR_OK,
    COLOR_WTW,
    COLOR_WTW_HOVER,
)


class BloqueArchivo(ctk.CTkFrame):
    """Bloque de selección de archivo para un tipo de insumo."""

    def __init__(
        self,
        parent: ctk.CTk,
        tipo: TipoInsumo,
        on_change: callable = None,  # type: ignore[type-arg]
    ) -> None:
        super().__init__(
            parent,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.tipo = tipo
        self._on_change = on_change
        self._ruta: Path | None = None

        self._crear_widgets()

    def _crear_widgets(self) -> None:
        # Fila 1: nombre del tipo (izq) + estado + botón Buscar (der).
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            fila,
            text=self.tipo.value,
            width=250,
            anchor="w",
            font=("Arial", 14, "bold"),
            text_color=COLOR_INPUT_TEXT,
        ).pack(side="left")

        self.estado = ctk.CTkLabel(
            fila, text="● Pendiente", width=140, text_color=COLOR_WTW
        )
        self.estado.pack(side="left", padx=(20, 0))

        ctk.CTkButton(
            fila,
            text="Buscar",
            width=110,
            height=35,
            fg_color=COLOR_WTW,
            hover_color=COLOR_WTW_HOVER,
            command=self._on_buscar_click,
        ).pack(side="right")

        # Fila 2: etiqueta dinámica (vacía inicialmente).
        self.label_info = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            font=("Arial", 11),
            text_color=COLOR_INPUT_TEXT,
            wraplength=900,
            justify="left",
        )
        self.label_info.pack(fill="x", padx=15, pady=(2, 10))

    def _on_buscar_click(self) -> None:
        """Abre el filedialog para seleccionar el archivo."""
        ruta = filedialog.askopenfilename(
            title=f"Seleccionar {self.tipo.value}",
            filetypes=[("Archivos Excel", "*.xlsx")],
        )
        if not ruta:
            return
        self.set_ruta(Path(ruta))
        if self._on_change is not None:
            self._on_change(self.tipo, Path(ruta))

    def set_ruta(self, ruta: Path) -> None:
        """Setea la ruta y muestra el nombre del archivo en la etiqueta."""
        self._ruta = ruta
        # Mostrar nombre del archivo en la etiqueta dinámica.
        self.label_info.configure(
            text=f"📄 {ruta.name}",
            text_color=COLOR_INPUT_TEXT,
        )
        self._set_estado("● Pendiente", COLOR_WTW)

    def get_ruta(self) -> Path | None:
        """Retorna la ruta seleccionada o None si no hay archivo."""
        return self._ruta

    def set_estado_validando(self) -> None:
        """Marca el bloque como 'Validando...'."""
        self._set_estado("● Validando...", "#F59E0B")
        self.label_info.configure(
            text="Validando estructura del archivo...",
            text_color="#9ca3af",
        )

    def set_estado_valido(
        self, mensaje: str = "Estructura validada correctamente."
    ) -> None:
        """Marca el bloque como válido y muestra mensaje de éxito."""
        self._set_estado("● Archivo válido", COLOR_OK)
        nombre = self._ruta.name if self._ruta else "archivo"
        self.label_info.configure(
            text=f"✓ {nombre} — {mensaje}",
            text_color=COLOR_OK,
        )

    def set_estado_invalido(self, errores: list[str]) -> None:
        """Marca el bloque como inválido y muestra los errores."""
        self._set_estado("● Archivo inválido", COLOR_ERROR)
        # Mostrar TODOS los errores en la etiqueta dinámica (no solo el primero).
        if len(errores) == 1:
            texto = f"✗ {errores[0]}"
        else:
            texto = "✗ Errores:\n  • " + "\n  • ".join(errores)
        self.label_info.configure(text=texto, text_color=COLOR_ERROR)
