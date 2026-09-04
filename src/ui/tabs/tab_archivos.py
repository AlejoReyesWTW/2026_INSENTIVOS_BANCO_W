"""Tab "Archivos" de la UI.

Contiene 6 bloques de selección (uno por tipo de insumo), un indicador de
estado general y el botón "Iniciar Bot" que dispara ProcesarCiclo.
"""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from src.application.validar_insumos import ValidadorInsumos
from src.domain.insumo import TipoInsumo
from src.infrastructure.config_loader import ConfigLoader
from src.ui.constants import (
    COLOR_DESHABILITADO,
    COLOR_OK,
    COLOR_TEXTO_SECUNDARIO,
    COLOR_WARNING,
    COLOR_WTW_HOVER,
)
from src.ui.widgets import BloqueArchivo


class TabArchivos:
    """Tab que gestiona los 6 bloques de selección de archivos."""

    def __init__(
        self,
        parent: ctk.CTk,
        tipos_insumo: list[TipoInsumo],
        config_loader: ConfigLoader,
        on_log: callable = None,  # type: ignore[type-arg]
        on_error: callable = None,  # type: ignore[type-arg]
    ) -> None:
        self.tipos = tipos_insumo
        self.config_loader = config_loader
        self._on_log = on_log or (lambda m, n="INFO": None)
        self._on_error = on_error or (lambda m: None)
        self.validador = ValidadorInsumos(config_loader)
        self.bloques: dict[TipoInsumo, BloqueArchivo] = {}

        # Frame principal del tab.
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._crear_widgets()
        self._crear_bloques()

    def _crear_widgets(self) -> None:
        """Crea el título, descripción, scroll, estado general y botón Iniciar."""
        ctk.CTkLabel(
            self.frame,
            text="Archivos de entrada",
            font=("Arial", 24, "bold"),
            text_color=COLOR_WTW_HOVER,
        ).pack(anchor="w", padx=25, pady=(25, 5))

        ctk.CTkLabel(
            self.frame,
            text=(
                "Seleccione los archivos requeridos. "
                "La estructura será validada automáticamente."
            ),
            font=("Arial", 14),
            text_color=COLOR_TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=25, pady=(0, 15))

        # Scroll con bloques.
        self.scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Estado general + botón Iniciar.
        self.estado_general = ctk.CTkLabel(
            self.frame,
            text="● Esperando archivos válidos",
            font=("Arial", 14, "bold"),
            text_color=COLOR_WARNING,
        )
        self.estado_general.pack(pady=(15, 10))

        self.btn_iniciar = ctk.CTkButton(
            self.frame,
            text="INICIAR",
            width=240,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color=COLOR_DESHABILITADO,
            hover_color=COLOR_DESHABILITADO,
            command=self._on_iniciar_click,
            state="disabled",
            text_color=COLOR_TEXTO_SECUNDARIO,
        )
        self.btn_iniciar.pack(pady=10)

    def _crear_bloques(self) -> None:
        """Crea un BloqueArchivo por cada tipo de insumo."""
        for tipo in self.tipos:
            # archivo_esperado="" -> no muestra label rojo (comentado en widget).
            bloque = BloqueArchivo(
                self.scroll, tipo=tipo, on_change=self._on_bloque_change
            )
            bloque.pack(fill="x", padx=25, pady=8)
            self.bloques[tipo] = bloque

    def _on_bloque_change(self, tipo: TipoInsumo, ruta) -> None:
        """Callback cuando el usuario selecciona un archivo en un bloque."""
        bloque = self.bloques[tipo]
        bloque.set_estado_validando()

        # Validar estructura usando ValidadorInsumos.
        resultado = self.validador.validar({tipo: ruta})
        if resultado.valido:
            bloque.set_estado_valido()
            self._on_log(f"{tipo.value}: archivo validado correctamente.")
        else:
            errores = resultado.errores.get(tipo, ["Error desconocido"])
            bloque.set_estado_invalido(errores)
            for e in errores:
                self._on_log(f"{tipo.value}: {e}", "ERROR")
                self._on_error(f"{tipo.value} → {e}")

        self._actualizar_estado_general()

    def _actualizar_estado_general(self) -> None:
        """Actualiza el indicador y el botón según cuántos bloques están válidos."""
        todos_validos = all(
            bloque.get_ruta() is not None for bloque in self.bloques.values()
        )
        # Para considerar "listo para iniciar", todos deben tener archivo seleccionado.
        # (Ya validamos estructura al seleccionar.)
        if todos_validos:
            self.estado_general.configure(
                text="● Todos los archivos están listos", text_color=COLOR_OK
            )
            self.btn_iniciar.configure(state="normal", fg_color=COLOR_OK)
        else:
            self.estado_general.configure(
                text="● Esperando archivos válidos", text_color=COLOR_WARNING
            )
            self.btn_iniciar.configure(state="disabled", fg_color=COLOR_DESHABILITADO)

    def _on_iniciar_click(self) -> None:
        """Callback al hacer clic en Iniciar Bot. Emite señal para que el Panel procese."""
        # El Panel se suscribe a este método via on_iniciar_signal.
        if self._on_iniciar_signal is not None:
            self._on_iniciar_signal()

    def set_on_iniciar(self, callback: callable) -> None:  # type: ignore[type-arg]
        """Registra el callback que se dispara al hacer clic en Iniciar."""
        self._on_iniciar_signal = callback
        self._on_iniciar_signal = callback

    def obtener_insumos(self) -> dict[TipoInsumo, Path]:
        """Retorna los insumos seleccionados (filtra los que no tienen ruta)."""
        resultado: dict[TipoInsumo, Path] = {}
        for tipo, bloque in self.bloques.items():
            ruta = bloque.get_ruta()
            if ruta is not None:
                resultado[tipo] = ruta
        return resultado

    def set_estado_bot_ejecutando(self, ejecutando: bool) -> None:
        """Habilita/deshabilita el botón Iniciar según estado del bot."""
        if ejecutando:
            self.btn_iniciar.configure(state="disabled", fg_color=COLOR_DESHABILITADO)
        else:
            self._actualizar_estado_general()
