"""Panel raíz de la UI.

Compone los 4 tabs y conecta el botón "Iniciar Bot" con ProcesarCiclo.
"""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage

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
from src.ui.tabs import TabArchivos, TabControl, TabErrores, TabLogs


class Panel:
    """Ventana principal de la aplicación."""

    def __init__(self) -> None:
        # Inicializar apariencia y crear ventana.
        ctk.set_appearance_mode("light")
        self.app = ctk.CTk()
        self.app.title("WTW - Control de Automatización")
        self.app.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
        self.app.minsize(ANCHO_VENTANA, ALTO_VENTANA)
        self.app.configure(fg_color=COLOR_FONDO)

        # Logo (si existe).
        self._cargar_logo()

        # Estado del bot.
        self.bot_ejecutando = False

        # Infraestructura (singleton).
        self.config_loader = ConfigLoader(RUTA_CONFIG)
        self.logger = LoggerDiario(RUTA_LOGS)

        # Crear tabs.
        self._crear_tabs()

        # Conectar callbacks.
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
        """Crea el tabview y los 4 tabs."""
        tipos_insumo = [
            TipoInsumo.DIRECTORIO_NACIONAL,
            TipoInsumo.NOVEDADES_SUBGERENTE,
            TipoInsumo.BASE_TEMPORAL,
            TipoInsumo.BASE_BANCO,
            TipoInsumo.BASE_SEGUROS,
            TipoInsumo.SOY_PREVENIDO,
        ]
        self.tabs = ctk.CTkTabview(self.app, fg_color=COLOR_FONDO)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=20)

        tab_archivos_frame = self.tabs.add("Archivos")
        tab_logs_frame = self.tabs.add("Ejecución")
        tab_errores_frame = self.tabs.add("Errores")
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

        self.tab_errores = TabErrores(parent=tab_errores_frame)
        self.tab_errores.frame.pack(fill="both", expand=True)

        self.tab_control = TabControl(parent=tab_control_frame)
        self.tab_control.frame.pack(fill="both", expand=True)

    def _log(self, mensaje: str, nivel: str = "INFO") -> None:
        """Log a UI y archivo."""
        self.tab_logs.agregar(mensaje, nivel)
        self.logger.info(mensaje) if nivel == "INFO" else None

    def _error(self, mensaje: str) -> None:
        """Log error a UI y pestaña de errores."""
        self.tab_errores.agregar(mensaje)
        self.logger.error(mensaje)

    def _on_iniciar_click(self) -> None:
        """Handler del botón Iniciar Bot: ejecuta ProcesarCiclo."""
        if self.bot_ejecutando:
            return
        insumos = self.tab_archivos.obtener_insumos()
        if not insumos:
            self._log("No hay insumos seleccionados.", "WARNING")
            return

        self.bot_ejecutando = True
        self.tab_archivos.set_estado_bot_ejecutando(True)
        self._log("Iniciando procesamiento del ciclo...")

        try:
            procesar = ProcesarCiclo(
                insumos=insumos,
                config_loader=self.config_loader,
                logger=self.logger,
                ruta_plantilla=RUTA_PLANTILLA,
                directorio_salida=RUTA_SALIDA,
            )
            resultado = procesar.ejecutar()

            if resultado.exito and resultado.ruta_salida:
                self._log(f"Archivo generado: {resultado.ruta_salida.name}")
                self._log(f"  Ventas: {resultado.filas_ventas} filas")
                self._log(
                    f"  Base subgerentes: {resultado.filas_base_subgerentes} filas"
                )
                self._log(
                    f"  Base red agencias: {resultado.filas_base_red_agencias} filas"
                )
            else:
                for e in resultado.errores:
                    self._log(e, "ERROR")
                    self._error(e)
        except (OSError, ValueError, RuntimeError) as e:
            self._log(f"Error durante el procesamiento: {e}", "ERROR")
            self._error(str(e))
        finally:
            self.bot_ejecutando = False
            self.tab_archivos.set_estado_bot_ejecutando(False)

    def ejecutar(self) -> None:
        """Inicia el mainloop de la UI."""
        self.app.mainloop()


class _SetupPaths:
    """Helper para resolver paths del proyecto de forma robusta."""


# Asegurar que los directorios de salida/logs existan.
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)
RUTA_LOGS.mkdir(parents=True, exist_ok=True)
