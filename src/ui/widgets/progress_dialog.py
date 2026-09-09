"""Widget: diálogo modal con barra de progreso, paso actual y tiempo transcurrido."""

from __future__ import annotations

import contextlib
import time

import customtkinter as ctk

from src.ui.constants import COLOR_OK, COLOR_WTW_SECONDARY


class ProgressDialog(ctk.CTkToplevel):
    """Diálogo modal que muestra el avance del procesamiento.

    Layout:
      ⏳ Procesando ciclo...

      [Paso actual]

      [████████░░░░░░░░░░] 45%

      Tiempo: 0:23
    """

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Procesando...")
        self.geometry("520x220")
        self.resizable(False, False)
        # Modal: bloquea la ventana padre hasta cerrarse.
        self.transient(parent)
        self.grab_set()
        # Centrar sobre el padre.
        self.update_idletasks()
        with contextlib.suppress(AttributeError, ValueError):
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 260
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 110
            self.geometry(f"+{x}+{y}")

        # Estado interno.
        self._start_time = time.monotonic()
        self._cerrado = False

        self._crear_widgets()
        self._actualizar_tiempo()

    def _crear_widgets(self) -> None:
        # Título.
        ctk.CTkLabel(
            self,
            text="⏳ Procesando ciclo...",
            font=("Arial", 18, "bold"),
            text_color=COLOR_WTW_SECONDARY,
        ).pack(pady=(20, 5))

        # Paso actual.
        self._label_paso = ctk.CTkLabel(
            self,
            text="Iniciando...",
            font=("Arial", 13),
            text_color="#374151",
        )
        self._label_paso.pack(pady=(5, 10))

        # Barra de progreso.
        self._progress = ctk.CTkProgressBar(self, height=18, progress_color=COLOR_OK)
        self._progress.set(0)
        self._progress.pack(fill="x", padx=30, pady=(0, 5))

        # Porcentaje.
        self._label_pct = ctk.CTkLabel(
            self, text="0%", font=("Arial", 14, "bold"), text_color=COLOR_OK
        )
        self._label_pct.pack()

        # Tiempo transcurrido.
        self._label_tiempo = ctk.CTkLabel(
            self, text="Tiempo: 0s", font=("Arial", 12), text_color="#6b7280"
        )
        self._label_tiempo.pack(pady=(5, 20))

    def update_progress(self, percent: int, mensaje: str) -> None:
        """Actualiza el avance y el mensaje del paso actual.

        Args:
            percent: 0-100.
            mensaje: descripción del paso actual.
        """
        if self._cerrado:
            return
        self._progress.set(percent / 100.0)
        self._label_paso.configure(text=mensaje)
        self._label_pct.configure(text=f"{percent}%")
        self.update_idletasks()

    def _actualizar_tiempo(self) -> None:
        """Actualiza el label de tiempo cada 1 segundo mientras esté abierto."""
        if self._cerrado:
            return
        try:
            elapsed = time.monotonic() - self._start_time
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
        except (ValueError, TypeError, OverflowError):
            return
        tiempo = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"
        self._label_tiempo.configure(text=f"Tiempo: {tiempo}")
        # Programar próxima actualización.
        self.after(500, self._actualizar_tiempo)

    def cerrar(self) -> None:
        """Cierra el diálogo de progreso."""
        if self._cerrado:
            return
        self._cerrado = True
        with contextlib.suppress(AttributeError, ValueError):
            self.grab_release()
        self.destroy()
