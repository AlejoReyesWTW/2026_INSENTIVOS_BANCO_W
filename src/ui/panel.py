"""Panel raíz de la UI.

Compone los 3 tabs (Archivos, Ejecución, Control) y conecta el botón
"Iniciar" con ProcesarCiclo. El tab Ejecución contiene log + errores
apilados verticalmente en la misma vista.

El procesamiento corre en un HILO SEPARADO (threading) para no congelar
la UI: la barra de progreso, los logs y las cards se actualizan desde el
hilo principal mediante self.app.after (nunca se tocan widgets desde el
hilo de trabajo directamente).
"""

from __future__ import annotations

import queue
import threading
import time
from queue import Empty as ColaVacia

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
    RUTA_CONFIG,
    RUTA_INTERNA,
    RUTA_LOGO_EXE,
    RUTA_LOGS,
    RUTA_PLANTILLA,
    RUTA_SALIDA_BASE,
)
from src.ui.tabs import TabArchivos, TabLogs
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
        self._cargar_icono_ventana()

        self._cargar_logo()

        self.bot_ejecutando = False

        self.config_loader = ConfigLoader(RUTA_CONFIG)
        self.logger = LoggerDiario(RUTA_LOGS)

        self._crear_tabs()

        self.tab_archivos.set_on_iniciar(self._on_iniciar_click)

    def _cargar_icono_ventana(self) -> None:
        """Pone el logo como icono de la ventana (barra de tareas)."""
        try:
            if RUTA_LOGO_EXE.exists():
                self.app.iconbitmap(str(RUTA_LOGO_EXE))
        except (OSError, ValueError, TypeError):
            # Si el icono no se puede cargar, se sigue sin él.
            pass

    def _cargar_logo(self) -> None:
        """Carga el logo si existe en IMG/."""
        ruta_logo = RUTA_INTERNA / "IMG" / "imagen (1).png"
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
        """Crea el tabview con 2 tabs (Archivos, Ejecución)."""
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

        self.tab_archivos = TabArchivos(
            parent=tab_archivos_frame,
            tipos_insumo=tipos_insumo,
            config_loader=self.config_loader,
            on_log=self._log,
            on_error=self._error,
        )
        self.tab_archivos.frame.pack(fill="both", expand=True)
        self.tab_archivos.set_on_limpiar(self._on_limpiar_click)

        self.tab_logs = TabLogs(parent=tab_logs_frame)
        self.tab_logs.frame.pack(fill="both", expand=True)

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
        """Handler del botón INICIAR: ejecuta ProcesarCiclo en un hilo aparte.

        El procesamiento corre en un threading.Thread para no bloquear el
        mainloop de la UI. El hilo de trabajo NO toca widgets directamente:
        deposita mensajes en una queue.Queue y el hilo principal los drena
        con self.app.after(0, ...) programado desde acá (Tkinter solo permite
        after() desde el hilo principal).
        """
        if self.bot_ejecutando:
            return
        insumos = self.tab_archivos.obtener_insumos()
        if not insumos:
            self._log("No hay insumos seleccionados.", "WARNING")
            return

        self.bot_ejecutando = True
        self.tab_archivos.set_estado_bot_ejecutando(True)
        # Reset: ocultar archivos de salida previos antes de empezar.
        self._tiempo_inicio = time.monotonic()
        self.tab_archivos.ocultar_archivos_salida()
        self._log("Iniciando procesamiento del ciclo...")

        # Crear diálogo de progreso modal.
        progress_dialog = ProgressDialog(self.app)

        # Cola de mensajes hilo-de-trabajo -> hilo-principal.
        cola = queue.Queue()

        def _paso(tipo: str, *args) -> None:
            """Deposita un mensaje en la cola (seguro desde cualquier hilo)."""
            cola.put((tipo, args))

        def _drenar_cola() -> None:
            """Procesa los mensajes pendientes. Se programa desde el hilo mainloop."""
            while True:
                try:
                    tipo, args = cola.get_nowait()
                except ColaVacia:
                    break
                if tipo == "progreso":
                    progress_dialog.update_progress(args[0], args[1])
                    # También al log visual del panel (etapas del proceso).
                    self._log(f"[{args[0]}%] {args[1]}")
                elif tipo == "log":
                    self._log(args[0], args[1])
                elif tipo == "error":
                    self._error(args[0])
                elif tipo == "fin":
                    self._mostrar_resultado_hilo(args[0], progress_dialog)
                    return  # el último mensaje: no reprogramar
            # Programar el siguiente drenaje (0ms → next idle).
            self.app.after(50, _drenar_cola)

        def progress_cb(percent: int, mensaje: str) -> None:
            """Callback del proceso (hilo de trabajo → cola)."""
            _paso("progreso", percent, mensaje)

        def _trabajo() -> None:
            """Cuerpo del hilo: ejecuta ProcesarCiclo y encola el resultado.

            Nunca toca widgets: todo va a la cola. Las excepciones también.
            """
            try:
                procesar = ProcesarCiclo(
                    insumos=insumos,
                    config_loader=self.config_loader,
                    logger=self.logger,
                    ruta_plantilla=RUTA_PLANTILLA,
                    directorio_salida=RUTA_SALIDA_BASE,
                )
                resultado = procesar.ejecutar(progress_callback=progress_cb)
                _paso("fin", resultado)
            except (OSError, ValueError, RuntimeError) as e:
                _paso("error", f"Error durante el procesamiento: {e}")
                _paso("fin", None)
            except Exception as e:  # noqa: BLE001
                _paso("error", f"Error inesperado: {e}")
                _paso("fin", None)

        hilo = threading.Thread(target=_trabajo, name="proceso-ciclo", daemon=True)
        hilo.start()
        # Arrancar el drenaje desde el hilo principal (after es thread-safe acá).
        self.app.after(0, _drenar_cola)

    def _mostrar_resultado_hilo(self, resultado, progress_dialog) -> None:
        """Muestra el resultado final en las cards (hilo principal)."""
        if progress_dialog is not None:
            progress_dialog.cerrar()
        self.bot_ejecutando = False
        self.tab_archivos.set_estado_bot_ejecutando(False)

        if resultado is not None and resultado.exito and resultado.ruta_salida:
            segundos = time.monotonic() - getattr(
                self, "_tiempo_inicio", time.monotonic()
            )
            ruta_carpeta = resultado.ruta_salida.parent.resolve()
            self._log(f"⏱️ Tiempo de ejecución: {segundos:.1f}s")
            self._log(f"📁 Archivos guardados en: {ruta_carpeta}")
            self._log(f"  Ventas: {resultado.filas_ventas} filas")
            self._log(f"  Base subgerentes: {resultado.filas_base_subgerentes} filas")
            self._log(f"  Base red agencias: {resultado.filas_base_red_agencias} filas")
            archivos_salida = [resultado.ruta_salida]
            if resultado.ruta_planilla_pago is not None:
                archivos_salida.append(resultado.ruta_planilla_pago)
                self._log(f"  Planilla de pago: {resultado.ruta_planilla_pago.name}")
            self.tab_archivos.mostrar_archivos_salida(archivos_salida)
            self.tab_archivos.set_tiempo_ejecucion(segundos)
            self.tab_archivos.limpiar_entradas()
            self.tab_archivos.btn_limpiar.configure(state="normal")
        elif resultado is not None:
            segundos = time.monotonic() - getattr(
                self, "_tiempo_inicio", time.monotonic()
            )
            self._log(f"⏱️ Tiempo hasta el error: {segundos:.1f}s", "ERROR")
            for e in resultado.errores:
                self._log(e, "ERROR")
                self._error(e)

    def _on_limpiar_click(self) -> None:
        """Limpia los campos de insumos y oculta las salidas anteriores."""
        self.tab_archivos.limpiar_todo()
        self._log("🧹 Campos limpiados.")

    def ejecutar(self) -> None:
        """Inicia el mainloop de la UI."""
        self.app.mainloop()


# Asegurar que los directorios de salida/logs existan.
RUTA_SALIDA_BASE.mkdir(parents=True, exist_ok=True)
RUTA_LOGS.mkdir(parents=True, exist_ok=True)
