"""Widget: bloque para seleccionar un archivo de insumo.

Cada bloque muestra:
- Nombre del tipo de insumo (ej: "Soy Prevenido")
- Entry con la ruta seleccionada (readonly)
- Estado (Pendiente / Validando / Válido / Inválido)
- Botón "Buscar" (filedialog)
- Mensaje de error o éxito
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from src.domain.insumo import TipoInsumo
from src.ui.constants import (
    COLOR_ERROR,
    COLOR_OK,
    COLOR_PANEL,
    COLOR_PANEL_2,
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
        super().__init__(parent, fg_color=COLOR_PANEL, corner_radius=10)
        self.tipo = tipo
        self._on_change = on_change
        self._ruta: Path | None = None

        # Fila principal.
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=15, pady=(12, 5))

        # Label con nombre del tipo.
        ctk.CTkLabel(
            fila,
            text=tipo.value,
            width=200,
            anchor="w",
            font=("Arial", 14, "bold"),
        ).pack(side="left")

        # Entry con la ruta.
        self.entry = ctk.CTkEntry(
            fila,
            height=38,
            placeholder_text="Seleccione un archivo .xlsx...",
            fg_color=COLOR_PANEL_2,
            border_color=COLOR_PANEL_2,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=10)

        # Estado.
        self.estado = ctk.CTkLabel(
            fila, text="● Pendiente", width=130, text_color=COLOR_WTW
        )
        self.estado.pack(side="left")

        # Botón Buscar.
        ctk.CTkButton(
            fila,
            text="Buscar",
            width=100,
            height=35,
            fg_color=COLOR_WTW,
            hover_color=COLOR_WTW_HOVER,
            command=self._on_buscar_click,
        ).pack(side="left", padx=(10, 5))

        # Mensaje.
        self.mensaje = ctk.CTkLabel(self, text="", anchor="w", font=("Arial", 12))
        self.mensaje.pack(fill="x", padx=215, pady=(0, 10))

    def _on_buscar_click(self) -> None:
        """Abre el filedialog y filtra archivos temporales."""
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
        """Setea la ruta manualmente (sin disparar callback)."""
        self._ruta = ruta
        self.entry.delete(0, "end")
        self.entry.insert(0, str(ruta))
        self._set_estado("● Pendiente", COLOR_WTW)
        self.mensaje.configure(text="")

    def get_ruta(self) -> Path | None:
        """Retorna la ruta seleccionada o None si no hay archivo."""
        return self._ruta

    def set_estado_validando(self) -> None:
        """Marca el bloque como 'Validando...'."""
        self._set_estado("● Validando...", "#F59E0B")  # amarillo

    def set_estado_valido(
        self, mensaje: str = "Estructura validada correctamente."
    ) -> None:
        """Marca el bloque como válido."""
        self._set_estado("● Archivo válido", COLOR_OK)
        self.mensaje.configure(text=mensaje, text_color=COLOR_OK)

    def set_estado_invalido(self, errores: list[str]) -> None:
        """Marca el bloque como inválido."""
        self._set_estado("● Archivo inválido", COLOR_ERROR)
        # Mostrar solo el primer error en el label (los demás van al log).
        primer_error = errores[0] if errores else "Error desconocido"
        self.mensaje.configure(text=primer_error, text_color=COLOR_ERROR)
