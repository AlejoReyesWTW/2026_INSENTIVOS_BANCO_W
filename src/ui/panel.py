"""Panel raíz de la UI.

Compone los 3 tabs (Archivos, Ejecución, Control) y conecta el botón
"Iniciar" con ProcesarCiclo. El tab Ejecución contiene log + errores
apilados verticalmente en la misma vista.
"""

from __future__ import annotations

import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image

from src.application.procesar_ciclo import ProcesarCiclo
from src.domain.insumo import TipoInsumo
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.logger import LoggerDiario
from src.ui.constants import (
    ALTO_VENTANA,
    ANCHO_VENTANA,
    COLOR_FONDO,
    COLOR_PANEL,
    RUTA_BASE,
    RUTA_CONFIG,
    RUTA_LOGS,
    RUTA_PLANTILLA,
    RUTA_SALIDA,
)
from src.ui.tabs import TabArchivos, TabControl, TabLogs
from src.ui.widgets import ProgressDialog


class Panel:
    """Ventana principal de la aplicación."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        self.app = ctk.CTk()
        self.app.title("WTW - Control de Automatización")
        self.app.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
        self.app.minsize(ANCHO_VENTANA, ALTO_VENTANA)
        self.app.configure(fg_color=COLOR_FONDO)

        self._cargar_logo()

        self.bot_ejecutando = False

        self.config_loader = ConfigLoader(RUTA_CONFIG)
        self.logger = LoggerDiario(RUTA_LOGS)

        self._crear_tabs()

        self.tab_archivos.set_on_iniciar(self._on_iniciar_click)

    def _cargar_logo(self) -> None:
        """Carga el logo si existe en IMG/."""
        ruta_logo = RUTA_BASE / "IMG" / "imagen (1).png"
        if not ruta_logo.exists():
            return
        try:
            logo_img = Image.open(ruta_logo)
            self.logo_ctk = CTkImage(
                light_image=logo_img,
                dark_image=logo_img,
                size=(120, 50),
            )
            header = ctk.CTkFrame(
                self.app, height=80, fg_color=COLOR_PANEL, corner_radius=0
            )
            header.pack(fill="x")
            header.pack_propagate(False)
            ctk.CTkLabel(header, image=self.logo_ctk, text="").pack(
                side="left", padx=30
            )
            ctk.CTkLabel(
                header,
                text="Control de Automatización",
                font=("Arial", 18),
                text_color=COLOR_FONDO,
            ).pack(side="left")
        except (OSError, ValueError) as e:
            self.logger.warning(f"No se pudo cargar el logo: {e}")

    def _crear_tabs(self) -> None:
        """Crea el tabview con 3 tabs (Archivos, Ejecución, Control)."""
        # BASE_TEMPORAL queda fuera por ahora (no se usa en el procesamiento).
        tipos_insumo = [
            TipoInsumo.SOY_PREVENIDO,
            TipoInsumo.BASE_BANCO,
            TipoInsumo.BASE_SEGUROS,
            TipoInsumo.DIRECTORIO_NACIONAL,
            TipoInsumo.NOVEDADES_SUBGERENTE,
        ]
        self.tabs = ctk.CTkTabview(self.app, fg_color=COLOR_FONDO)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=20)

        tab_archivos_frame = self.tabs.add("Archivos")
        tab_logs_frame = self.tabs.add("Ejecución")
        tab_control_frame = self.tabs.add("Control")

        self.tab_archivos = TabArchivos(
            parent=tab_archivos_frame,
            tipos_insumo=tipos_insumo,
            config_loader=self.config_loader,
            on_log=self._log,
            on_error=self._error,
        )
        self.tab_archivos.frame.pack(fill="both", expand=True)

        self.tab_logs = TabLogs(parent=tab_logs_frame)
        self.tab_logs.frame.pack(fill="both", expand=True)

        self.tab_control = TabControl(parent=tab_control_frame)
        self.tab_control.frame.pack(fill="both", expand=True)

    def _log(self, mensaje: str, nivel: str = "INFO") -> None:
        """Log a UI (log de ejecución + registro de errores) y a archivo."""
        self.tab_logs.agregar(mensaje, nivel)
        if nivel == "ERROR":
            self.tab_logs.agregar_error(mensaje)
            self.logger.error(mensaje)
        elif nivel == "WARNING":
            self.logger.warning(mensaje)
        else:
            self.logger.info(mensaje)

    def _error(self, mensaje: str) -> None:
        """Log error a UI (registro de errores) y a archivo."""
        self.tab_logs.agregar_error(mensaje)
        self.logger.error(mensaje)

    def _on_iniciar_click(self) -> None:
        """Handler del botón INICIAR: ejecuta ProcesarCiclo con barra de progreso."""
        if self.bot_ejecutando:
            return
        insumos = self.tab_archivos.obtener_insumos()
        if not insumos:
            self._log("No hay insumos seleccionados.", "WARNING")
            return

        self.bot_ejecutando = True
        self.tab_archivos.set_estado_bot_ejecutando(True)
        # Reset: ocultar archivos de salida previos antes de empezar.
        self.tab_archivos.ocultar_archivos_salida()
        self._log("Iniciando procesamiento del ciclo...")

        # Crear diálogo de progreso modal.
        progress_dialog = ProgressDialog(self.app)

        def progress_cb(percent: int, mensaje: str) -> None:
            """Callback invocado por ProcesarCiclo en cada paso."""
            progress_dialog.update_progress(percent, mensaje)

        try:
            procesar = ProcesarCiclo(
                insumos=insumos,
                config_loader=self.config_loader,
                logger=self.logger,
                ruta_plantilla=RUTA_PLANTILLA,
                directorio_salida=RUTA_SALIDA,
            )
            resultado = procesar.ejecutar(progress_callback=progress_cb)

            if resultado.exito and resultado.ruta_salida:
                self._log(f"Archivo generado: {resultado.ruta_salida.name}")
                self._log(f"  Ventas: {resultado.filas_ventas} filas")
                self._log(
                    f"  Base subgerentes: {resultado.filas_base_subgerentes} filas"
                )
                self._log(
                    f"  Base red agencias: {resultado.filas_base_red_agencias} filas"
                )
                # Mostrar la sección de salida con el archivo generado.
                self.tab_archivos.mostrar_archivos_salida([resultado.ruta_salida])
            else:
                for e in resultado.errores:
                    self._log(e, "ERROR")
                    self._error(e)
        except (OSError, ValueError, RuntimeError) as e:
            self._log(f"Error durante el procesamiento: {e}", "ERROR")
            self._error(str(e))
        finally:
            # Cerrar diálogo de progreso y resetear estado del bot.
            progress_dialog.cerrar()
            self.bot_ejecutando = False
            self.tab_archivos.set_estado_bot_ejecutando(False)

    def ejecutar(self) -> None:
        """Inicia el mainloop de la UI."""
        self.app.mainloop()


# Asegurar que los directorios de salida/logs existan.
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)
RUTA_LOGS.mkdir(parents=True, exist_ok=True)
