"""Widget: bloque para seleccionar un archivo de insumo.

Layout:
- Fila 1: [Nombre del tipo] ......... [Estado] [Botón]
- Fila 2: Etiqueta dinámica (vacía al inicio; muestra el archivo cargado
  o los errores de validación cuando aplica)

Estados del botón:
    Inicial  → "Buscar"        habilitado
    Validando → "Analizando..."  deshabilitado (gris)
    Válido   → "Buscar"         habilitado (naranja)
    Inválido → "Buscar"         habilitado (naranja) + etiqueta con errores
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
        self._validado: bool = False  # True solo si pasó la validación de estructura

        self._crear_widgets()

    def _crear_widgets(self) -> None:
        # Fila 1: nombre del tipo (izq) + estado + botón (der).
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

        # Botón Buscar (se guarda referencia para poder cambiar texto/estado).
        self.btn_buscar = ctk.CTkButton(
            fila,
            text="Buscar",
            width=110,
            height=35,
            fg_color=COLOR_WTW,
            hover_color=COLOR_WTW_HOVER,
            command=self._on_buscar_click,
        )
        self.btn_buscar.pack(side="right")

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
        # Disparar callback para que el Tab valide la estructura.
        if self._on_change is not None:
            self._on_change(self.tipo, Path(ruta))

    def set_ruta(self, ruta: Path) -> None:
        """Setea la ruta y muestra el nombre del archivo en la etiqueta."""
        self._ruta = ruta
        self._validado = False  # Reset: nuevo archivo, debe re-validarse
        self.label_info.configure(
            text=f"📄 {ruta.name}",
            text_color=COLOR_INPUT_TEXT,
        )
        # Resetear estado y botón.
        self._set_estado("● Pendiente", COLOR_WTW)
        self.btn_buscar.configure(state="normal", text="Buscar")

    def get_ruta(self) -> Path | None:
        """Retorna la ruta seleccionada o None si no hay archivo."""
        return self._ruta

    def is_validado(self) -> bool:
        """Retorna True solo si el archivo pasó la validación de estructura."""
        return self._validado

    def set_estado_validando(self) -> None:
        """Marca el bloque como 'Validando...': botón deshabilitado + texto 'Validando...'."""
        self._validado = False
        self._set_estado("● Validando...", "#F59E0B")
        self.btn_buscar.configure(
            state="disabled",
            text="Validando...",
            fg_color="#9ca3af",
            hover_color="#9ca3af",
        )
        self.label_info.configure(
            text="⏳ Validando estructura del archivo...",
            text_color="#9ca3af",
        )
        # Forzar actualización de pantalla para que se vea el cambio.
        self.update_idletasks()

    def set_estado_valido(self) -> None:
        """Marca el bloque como válido: ✓ verde + 'Analizado y aprobado'."""
        self._validado = True  # ← clave para habilitar el botón INICIAR
        self._set_estado("✓ Archivo válido", COLOR_OK)
        # Restaurar botón Buscar.
        self.btn_buscar.configure(
            state="normal",
            text="Buscar",
            fg_color=COLOR_WTW,
            hover_color=COLOR_WTW_HOVER,
        )
        nombre = self._ruta.name if self._ruta else "archivo"
        self.label_info.configure(
            text=f"✅ {nombre} — Analizado y aprobado",
            text_color=COLOR_OK,
        )
        self.update_idletasks()

    def set_estado_invalido(self, errores: list[str]) -> None:
        """Marca el bloque como inválido: ✗ rojo con la lista de errores."""
        self._validado = False
        self._set_estado("✗ Archivo inválido", COLOR_ERROR)
        # Restaurar botón Buscar (puede reintentar con otro archivo).
        self.btn_buscar.configure(
            state="normal",
            text="Buscar",
            fg_color=COLOR_WTW,
            hover_color=COLOR_WTW_HOVER,
        )
        nombre = self._ruta.name if self._ruta else "archivo"
        if len(errores) == 1:
            texto = f"❌ {nombre} — {errores[0]}"
        else:
            lista = "\n  • ".join(errores)
            texto = f"❌ {nombre} — Errores:\n  • {lista}"
        self.label_info.configure(text=texto, text_color=COLOR_ERROR)
        self.update_idletasks()

    def _set_estado(self, texto: str, color: str) -> None:
        """Cambia el texto y color del label de estado."""
        self.estado.configure(text=texto, text_color=color)
