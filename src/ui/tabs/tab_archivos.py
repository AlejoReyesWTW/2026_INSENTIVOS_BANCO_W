"""Tab "Archivos" de la UI.

Layout (ambos colapsables):
  [▼ Archivos de entrada]
    - Scroll con los bloques de selección
  [Estado general + Botón INICIAR]
  [▼ Archivos de salida]  ← solo visible cuando mostrar_salida=True
    - 2 cards con icono Excel verde + botón Descargar

Bandera: self.mostrar_salida: bool (False por defecto).
Cuando el proceso termina, el Panel llama mostrar_archivos_salida(paths).
"""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

import customtkinter as ctk

from src.application.validar_insumos import ValidadorInsumos
from src.domain.insumo import TipoInsumo
from src.infrastructure.config_loader import ConfigLoader
from src.ui.constants import (
    COLOR_ERROR,
    COLOR_OK,
    COLOR_TEXTO_SECUNDARIO,
    COLOR_WHITE,
    COLOR_WTW_HOVER,
    COLOR_WTW_SECONDARY,
)
from src.ui.widgets import ArchivoGeneradoCard, BloqueArchivo, SeccionColapsable


class TabArchivos:
    """Tab con 2 secciones colapsables: entrada y salida."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        tipos_insumo: list[TipoInsumo],
        config_loader: ConfigLoader,
        on_log: callable = None,  # type: ignore[type-arg]
        on_error: callable = None,  # type: ignore[type-arg]
    ) -> None:
        self.tipos = tipos_insumo
        self.config_loader = config_loader
        self._on_log = on_log or (lambda m, n="INFO": None)
        self._on_error = on_error or (lambda m: None)
        self._on_iniciar_signal = None
        self._on_limpiar_signal = None
        self.validador = ValidadorInsumos(config_loader)
        self.bloques: dict[TipoInsumo, BloqueArchivo] = {}

        # Bandera: controla si la sección "Archivos de salida" se muestra.
        self.mostrar_salida: bool = False

        # Frame principal del tab.
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._crear_secciones()

    def _crear_secciones(self) -> None:
        """Crea las 2 secciones colapsables + botón Iniciar.

        Layout (pack secuencial dentro de un scroll global):
          [Scroll global del tab]
            [▼ Archivos de entrada]
            [Estado + Botón INICIAR]
            [▼ Archivos de salida]  ← visible cuando mostrar_salida=True

        El scroll global permite bajar y ver las cards de salida sin
        colapsar la sección de entrada.
        """
        # Scroll global del tab: permite bajar y ver todo el contenido.
        self.scroll_global = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.scroll_global.pack(fill="both", expand=True)

        # Crear las secciones y widgets primero (sin empacar).
        self.seccion_entrada = SeccionColapsable(
            self.scroll_global,
            titulo="📁 Archivos de entrada",
            expandido=True,
        )
        self.seccion_salida = SeccionColapsable(
            self.scroll_global,
            titulo="📤 Archivos de salida",
            expandido=False,
        )

        # Botón Iniciar + estado.
        frame_iniciar = ctk.CTkFrame(self.scroll_global, fg_color="transparent")
        self.estado_general = ctk.CTkLabel(
            frame_iniciar,
            text="● Esperando archivos válidos",
            font=("Arial", 14, "bold"),
            text_color=COLOR_WTW_SECONDARY,
        )
        self.estado_general.pack(pady=(5, 5))
        self.btn_iniciar = ctk.CTkButton(
            frame_iniciar,
            text="INICIAR",
            width=240,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color=COLOR_WTW_SECONDARY,
            hover_color=COLOR_WTW_SECONDARY,
            command=self._on_iniciar_click,
            state="disabled",
            text_color=COLOR_WHITE,
        )
        self.btn_iniciar.pack(pady=(0, 5))
        # Botón "Limpiar todo": se habilita al terminar el proceso.
        self.btn_limpiar = ctk.CTkButton(
            frame_iniciar,
            text="🧹 LIMPIAR TODO",
            width=240,
            height=38,
            font=("Arial", 13, "bold"),
            fg_color=COLOR_WTW_SECONDARY,
            hover_color=COLOR_WTW_HOVER,
            command=self._on_limpiar_click,
            state="disabled",
            text_color=COLOR_WHITE,
        )
        self.btn_limpiar.pack(pady=(0, 10))

        # Empacar en orden (todos top, dentro del scroll).
        # 1. Entrada (arriba).
        self.seccion_entrada.pack(fill="x", padx=15, pady=(15, 5))
        self._poblar_seccion_entrada(self.seccion_entrada.contenido)
        # 2. Iniciar (al medio).
        frame_iniciar.pack(fill="x", padx=15, pady=5)
        # 3. Salida: NO se empaca aquí. Solo se muestra cuando
        #    mostrar_archivos_salida() lo pide (tras generar archivos).
        self._poblar_seccion_salida(self.seccion_salida.contenido)

    def _poblar_seccion_entrada(self, parent: ctk.CTkFrame | ctk.CTk) -> None:
        """Llena la sección de entrada con los bloques de selección."""
        ctk.CTkLabel(
            parent,
            text="Seleccione los archivos requeridos. "
            "La estructura será validada automáticamente.",
            font=("Arial", 12),
            text_color=COLOR_TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(5, 10))

        # Scroll que se expande moderado para llenar el espacio vertical
        # disponible dentro de la sección (sin expand infinito).
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5, ipady=4)

        for tipo in self.tipos:
            bloque = BloqueArchivo(scroll, tipo=tipo, on_change=self._on_bloque_change)
            bloque.pack(fill="x", padx=10, pady=6)
            self.bloques[tipo] = bloque

    def _poblar_seccion_salida(self, parent: ctk.CTkFrame | ctk.CTk) -> None:
        """Llena la sección de salida con 2 cards (placeholder)."""
        ctk.CTkLabel(
            parent,
            text="✅ Archivos generados correctamente",
            font=("Arial", 14, "bold"),
            text_color=COLOR_OK,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 2))

        # Tiempo de ejecución (se actualiza al terminar el proceso).
        self.label_tiempo = ctk.CTkLabel(
            parent,
            text="⏱️ —",
            font=("Arial", 12, "bold"),
            text_color=COLOR_TEXTO_SECUNDARIO,
            anchor="w",
        )
        self.label_tiempo.pack(fill="x", padx=10, pady=(0, 8))

        # Frame horizontal para las 2 cards.
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=5)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        # 2 cards (mismo tamaño). Las creamos vacías; se actualizan al final.
        self.card_1 = ArchivoGeneradoCard(
            cards_frame,
            ruta=Path("Pendiente"),
            titulo="Base incentivos (mes/año)",
            on_descargar=self._abrir_carpeta,
        )
        self.card_1.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

        self.card_2 = ArchivoGeneradoCard(
            cards_frame,
            ruta=Path("Pendiente"),
            titulo="Planilla de pago (mes/año)",
            on_descargar=self._abrir_carpeta,
        )
        self.card_2.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")

    def set_tiempo_ejecucion(self, segundos: float) -> None:
        """Muestra el tiempo que tardó la ejecución arriba de las cards."""
        self.label_tiempo.configure(text=f"⏱️ Tiempo de ejecución: {segundos:.1f}s")

    def _abrir_carpeta(self, ruta: Path) -> None:
        """Abre el archivo o la carpeta que lo contiene."""
        try:
            if platform.system() == "Windows":
                # En Windows, os.startfile abre el archivo con su app default.
                if ruta.is_file():
                    subprocess.Popen(["explorer", str(ruta.parent)])
                else:
                    subprocess.Popen(["explorer", str(ruta)])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(ruta)])
            else:
                subprocess.Popen(["xdg-open", str(ruta)])
        except (OSError, FileNotFoundError) as e:
            self._on_log(f"No se pudo abrir el archivo: {e}", "ERROR")

    def mostrar_archivos_salida(self, archivos: list[Path]) -> None:
        """Muestra la sección de salida con los archivos generados.

        Args:
            archivos: lista de hasta 2 Paths generados por ProcesarCiclo.
        """
        self.mostrar_salida = True

        # Actualizar las 2 cards con los archivos generados.
        cards = [self.card_1, self.card_2]
        for i, ruta in enumerate(archivos[:2]):
            if i < len(cards):
                cards[i].set_ruta(ruta)

        # Empacar la sección de salida (si ya estaba empacada, no se
        # vuelve a empaquetar para evitar error de doble pack).
        if not self.mostrar_salida or self.seccion_salida.winfo_manager() != "pack":
            self.seccion_salida.pack(fill="x", padx=15, pady=(5, 15))
        # Expandir para que las cards queden visibles.
        self.seccion_salida.expandir()
        # Habilitar el botón Limpiar todo (ya terminó el proceso).
        self.btn_limpiar.configure(state="normal", fg_color=COLOR_WTW_HOVER)
        # Mover el scroll al final para que las cards queden visibles sin
        # necesidad de colapsar la sección de entrada.
        self.scroll_global.after(100, self._scroll_al_final)

    def _scroll_al_final(self) -> None:
        """Mueve el scroll global hacia abajo (ver las cards de salida)."""
        try:
            canvas = self.scroll_global._parent_canvas
            canvas.yview_moveto(1.0)
        except (AttributeError, KeyError, ValueError):
            self._on_log("No se pudo mover el scroll al final.", "WARNING")

    def ocultar_archivos_salida(self) -> None:
        """Oculta la sección de salida."""
        self.mostrar_salida = False
        self.seccion_salida.pack_forget()
        # Deshabilitar Limpiar (no hay proceso terminado).
        self.btn_limpiar.configure(state="disabled", fg_color=COLOR_WTW_SECONDARY)

    def _on_bloque_change(self, tipo: TipoInsumo, ruta) -> None:
        """Callback cuando el operador selecciona un archivo en un bloque."""
        bloque = self.bloques[tipo]
        bloque.set_estado_validando()

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
        """Habilita INICIAR solo cuando TODOS los bloques tienen ruta Y están validados."""
        todos_listos = all(
            bloque.get_ruta() is not None and bloque.is_validado()
            for bloque in self.bloques.values()
        )
        if todos_listos:
            self.estado_general.configure(
                text="● Todos los archivos están listos y validados",
                text_color=COLOR_OK,
            )
            self.btn_iniciar.configure(state="normal", fg_color=COLOR_OK)
        else:
            sin_ruta = [
                t.value
                for t, bloque in self.bloques.items()
                if bloque.get_ruta() is None
            ]
            sin_validar = [
                t.value
                for t, bloque in self.bloques.items()
                if bloque.get_ruta() is not None and not bloque.is_validado()
            ]
            if sin_ruta:
                msg = f"● Faltan archivos: {', '.join(sin_ruta)}"
            elif sin_validar:
                msg = f"● Archivos con errores: {', '.join(sin_validar)}"
            else:
                msg = "● Esperando archivos válidos"
            self.estado_general.configure(text=msg, text_color=COLOR_ERROR)
            self.btn_iniciar.configure(state="disabled", fg_color=COLOR_WTW_SECONDARY)

    def _on_iniciar_click(self) -> None:
        """Callback al hacer clic en INICIAR."""
        if self._on_iniciar_signal is not None:
            self._on_iniciar_signal()

    def set_on_iniciar(self, callback: callable) -> None:  # type: ignore[type-arg]
        """Registra el callback que se dispara al hacer clic en Iniciar."""
        self._on_iniciar_signal = callback

    def _on_limpiar_click(self) -> None:
        """Callback al hacer clic en Limpiar todo."""
        if self._on_limpiar_signal is not None:
            self._on_limpiar_signal()

    def set_on_limpiar(self, callback: callable) -> None:  # type: ignore[type-arg]
        """Registra el callback del botón Limpiar todo."""
        self._on_limpiar_signal = callback

    def limpiar_entradas(self) -> None:
        """Limpia solo los archivos de entrada y sus estados."""
        for bloque in self.bloques.values():
            bloque.limpiar()
        self.estado_general.configure(
            text="● Esperando archivos válidos",
            text_color=COLOR_WTW_SECONDARY,
        )
        self.btn_iniciar.configure(
            state="disabled",
            fg_color=COLOR_WTW_SECONDARY,
        )

    def limpiar_todo(self) -> None:
        """Limpia insumos, estados, salida y botón de procesamiento."""
        self.limpiar_entradas()
        self.ocultar_archivos_salida()
        self.estado_general.configure(
            text="● Esperando archivos válidos",
            text_color=COLOR_WTW_SECONDARY,
        )
        self.btn_iniciar.configure(
            state="disabled",
            fg_color=COLOR_WTW_SECONDARY,
        )

    def obtener_insumos(self) -> dict[TipoInsumo, Path]:
        """Retorna los insumos seleccionados."""
        resultado: dict[TipoInsumo, Path] = {}
        for tipo, bloque in self.bloques.items():
            ruta = bloque.get_ruta()
            if ruta is not None:
                resultado[tipo] = ruta
        return resultado

    def set_estado_bot_ejecutando(self, ejecutando: bool) -> None:
        """Habilita/deshabilita el botón Iniciar según estado del bot."""
        if ejecutando:
            self.btn_iniciar.configure(state="disabled", fg_color=COLOR_WTW_SECONDARY)
        else:
            self._actualizar_estado_general()
