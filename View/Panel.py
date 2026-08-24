import customtkinter as ctk

from tkinter import filedialog

from datetime import datetime
 
# COLORES
 
COLOR_WTW = "#6F2CFF"

COLOR_WTW_HOVER = "#8248FF"
 
COLOR_FONDO = "#15151A"

COLOR_PANEL = "#202027"

COLOR_PANEL_2 = "#292931"
 
COLOR_TEXTO = "#FFFFFF"

COLOR_TEXTO_SECUNDARIO = "#B8B8C2"
 
COLOR_OK = "#22C55E"

COLOR_WARNING = "#F59E0B"

COLOR_ERROR = "#EF4444"
 
# CONFIGURACIÓN
 
ctk.set_appearance_mode("dark")
 
app = ctk.CTk()

app.title("Banco W - Control de Automatización")

app.geometry("1200x700")

app.minsize(1000, 600)
 
app.configure(fg_color=COLOR_FONDO)
 
# VARIABLES
 
archivos = []
 
# FUNCIONES
 
 
def seleccionar_archivo(entry, estado_label):
 
    archivo = filedialog.askopenfilename(

        title="Seleccionar archivo",

        filetypes=[

            ("Todos los archivos", "*.*"),

            ("Excel", "*.xlsx *.xls"),

            ("CSV", "*.csv")

        ]

    )
 
    if archivo:
 
        entry.delete(0, "end")

        entry.insert(0, archivo)
 
        estado_label.configure(

            text="● Pendiente de validación",

            text_color=COLOR_WARNING

        )
 
 
def validar_archivos():
 
    # AQUÍ IRÁ TU CÓDIGO REAL DE VALIDACIÓN
 
    for entry, estado in archivos:
 
        if entry.get():
 
            estado.configure(

                text="● Correcto",

                text_color=COLOR_OK

            )
 
        else:
 
            estado.configure(

                text="● Archivo no seleccionado",

                text_color=COLOR_ERROR

            )
 
 
def agregar_log(mensaje, tipo="INFO"):
 
    timestamp = datetime.now().strftime("%H:%M:%S")
 
    log_text.configure(state="normal")
 
    if tipo == "ERROR":
 
        log_text.insert(

            "end",

            f"[{timestamp}] ERROR  |  {mensaje}\n",

            "error"

        )
 
    elif tipo == "WARNING":
 
        log_text.insert(

            "end",

            f"[{timestamp}] WARNING |  {mensaje}\n",

            "warning"

        )
 
    else:
 
        log_text.insert(

            "end",

            f"[{timestamp}] INFO   |  {mensaje}\n",

            "info"

        )
 
    log_text.see("end")

    log_text.configure(state="disabled")
 
 
def agregar_error(mensaje):
 
    timestamp = datetime.now().strftime("%H:%M:%S")
 
    errores_text.configure(state="normal")
 
    errores_text.insert(

        "end",

        f"[{timestamp}] {mensaje}\n"

    )
 
    errores_text.see("end")
 
    errores_text.configure(state="disabled")
 
 
def iniciar_bot():
 
    estado_bot.configure(

        text="● Ejecutando",

        text_color=COLOR_OK

    )
 
    agregar_log("Bot iniciado")
 
 
def pausar_bot():
 
    estado_bot.configure(

        text="● Pausado",

        text_color=COLOR_WARNING

    )
 
    agregar_log(

        "Bot pausado",

        "WARNING"

    )
 
 
def reanudar_bot():
 
    estado_bot.configure(

        text="● Ejecutando",

        text_color=COLOR_OK

    )
 
    agregar_log("Bot reanudado")
 
 
def detener_bot():
 
    estado_bot.configure(

        text="● Detenido",

        text_color=COLOR_ERROR

    )
 
    agregar_log(

        "Bot detenido",

        "WARNING"

    )
 
 
# ENCABEZADO
 
header = ctk.CTkFrame(

    app,

    height=80,

    fg_color=COLOR_PANEL,

    corner_radius=0

)
 
header.pack(

    fill="x"

)
 
header.pack_propagate(False)
 
 
titulo = ctk.CTkLabel(

    header,

    text="Banco W",

    font=("Arial", 28, "bold"),

    text_color=COLOR_WTW

)
 
titulo.pack(

    side="left",

    padx=30

)
 
 
subtitulo = ctk.CTkLabel(

    header,

    text="Control de Automatización",

    font=("Arial", 18),

    text_color=COLOR_TEXTO

)
 
subtitulo.pack(

    side="left"

)
 
# ESTADO DEL BOT
 
estado_bot = ctk.CTkLabel(

    header,

    text="● Detenido",

    font=("Arial", 15, "bold"),

    text_color=COLOR_ERROR

)
 
estado_bot.pack(

    side="right",

    padx=30

)
 
# TABS
 
tabs = ctk.CTkTabview(

    app,

    fg_color=COLOR_FONDO,

    segmented_button_fg_color=COLOR_PANEL,

    segmented_button_selected_color=COLOR_WTW,

    segmented_button_selected_hover_color=COLOR_WTW_HOVER,

    segmented_button_unselected_color=COLOR_PANEL,

    segmented_button_unselected_hover_color=COLOR_PANEL_2

)
 
tabs.pack(

    fill="both",

    expand=True,

    padx=20,

    pady=20

)
 
 
tab_archivos = tabs.add("Archivos")

tab_logs = tabs.add("Ejecución")

tab_errores = tabs.add("Errores")

tab_control = tabs.add("Control")
 
# TAB 1 - ARCHIVOS
 
titulo_archivos = ctk.CTkLabel(

    tab_archivos,

    text="Archivos de entrada",

    font=("Arial", 24, "bold"),

    text_color=COLOR_TEXTO

)
 
titulo_archivos.pack(

    anchor="w",

    padx=25,

    pady=(25, 5)

)
 
 
descripcion_archivos = ctk.CTkLabel(

    tab_archivos,

    text="Seleccione los archivos requeridos para ejecutar el bot.",

    font=("Arial", 14),

    text_color=COLOR_TEXTO_SECUNDARIO

)
 
descripcion_archivos.pack(

    anchor="w",

    padx=25,

    pady=(0, 20)

)
 
 
# FUNCIÓN PARA CREAR BLOQUE DE ARCHIVO
 
def crear_bloque_archivo(parent, nombre):
 
    frame = ctk.CTkFrame(

        parent,

        fg_color=COLOR_PANEL,

        corner_radius=10

    )
 
    frame.pack(

        fill="x",

        padx=25,

        pady=7

    )
 
    label = ctk.CTkLabel(

        frame,

        text=nombre,

        width=150,

        anchor="w",

        font=("Arial", 14, "bold")

    )
 
    label.pack(

        side="left",

        padx=(20, 10)

    )
 
    entry = ctk.CTkEntry(

        frame,

        height=38,

        placeholder_text="Seleccione un archivo...",

        fg_color=COLOR_PANEL_2,

        border_color=COLOR_PANEL_2

    )
 
    entry.pack(

        side="left",

        fill="x",

        expand=True,

        padx=10

    )
 
    estado = ctk.CTkLabel(

        frame,

        text="● Pendiente",

        width=140,

        text_color=COLOR_TEXTO_SECUNDARIO

    )
 
    estado.pack(

        side="left",

        padx=10

    )
 
    boton = ctk.CTkButton(

        frame,

        text="Buscar",

        width=100,

        height=35,

        fg_color=COLOR_WTW,

        hover_color=COLOR_WTW_HOVER,

        command=lambda: seleccionar_archivo(

            entry,

            estado

        )

    )
 
    boton.pack(

        side="left",

        padx=(5, 20)

    )
 
    archivos.append(

        (entry, estado)

    )
 
    return entry
 
# ARCHIVOS
 
archivo_1 = crear_bloque_archivo(

    tab_archivos,

    "Archivo 1"

)
 
archivo_2 = crear_bloque_archivo(

    tab_archivos,

    "Archivo 2"

)
 
archivo_3 = crear_bloque_archivo(

    tab_archivos,

    "Archivo 3"

)
 
 
# BOTÓN VALIDAR

btn_validar = ctk.CTkButton(

    tab_archivos,

    text="✓  VALIDAR ARCHIVOS",

    width=220,

    height=45,

    font=("Arial", 14, "bold"),

    fg_color=COLOR_WTW,

    hover_color=COLOR_WTW_HOVER,

    command=validar_archivos

)
 
btn_validar.pack(

    pady=25

)
 
 
# TAB 2 - LOG DE EJECUCIÓN
 
titulo_logs = ctk.CTkLabel(

    tab_logs,

    text="Log de ejecución",

    font=("Arial", 24, "bold")

)
 
titulo_logs.pack(

    anchor="w",

    padx=25,

    pady=(25, 10)

)
 
 
log_text = ctk.CTkTextbox(

    tab_logs,

    fg_color="#101014",

    text_color=COLOR_TEXTO,

    font=("Consolas", 13),

    corner_radius=10

)
 
log_text.pack(

    fill="both",

    expand=True,

    padx=25,

    pady=(0, 25)

)
 
 
# Colores del log
 
log_text.tag_config(

    "info",

    foreground=COLOR_TEXTO

)
 
log_text.tag_config(

    "warning",

    foreground=COLOR_WARNING

)
 
log_text.tag_config(

    "error",

    foreground=COLOR_ERROR

)
 
 
# TAB 3 - ERRORES
 
titulo_errores = ctk.CTkLabel(

    tab_errores,

    text="Registro de errores",

    font=("Arial", 24, "bold")

)
 
titulo_errores.pack(

    anchor="w",

    padx=25,

    pady=(25, 10)

)
 
 
errores_text = ctk.CTkTextbox(

    tab_errores,

    fg_color="#101014",

    text_color=COLOR_ERROR,

    font=("Consolas", 13),

    corner_radius=10

)
 
errores_text.pack(

    fill="both",

    expand=True,

    padx=25,

    pady=(0, 15)

)
 
 
errores_text.configure(

    state="disabled"

)
 
 
btn_exportar = ctk.CTkButton(

    tab_errores,

    text="Exportar Log",

    width=160,

    fg_color=COLOR_WTW,

    hover_color=COLOR_WTW_HOVER

)
 
btn_exportar.pack(

    pady=(0, 20)

)
 
 
# TAB 4 - CONTROL
 
titulo_control = ctk.CTkLabel(

    tab_control,

    text="Control del asistente",

    font=("Arial", 24, "bold")

)
 
titulo_control.pack(

    pady=(30, 20)

)
 
 
btn_iniciar = ctk.CTkButton(

    tab_control,

    text="▶  INICIAR BOT",

    width=280,

    height=45,

    font=("Arial", 14, "bold"),

    fg_color=COLOR_OK,

    hover_color="#16A34A",

    command=iniciar_bot

)
 
btn_iniciar.pack(

    pady=8

)
 
 
btn_pausar = ctk.CTkButton(

    tab_control,

    text="Ⅱ  PAUSAR ASISTENTE",

    width=280,

    height=45,

    font=("Arial", 14, "bold"),

    fg_color=COLOR_WARNING,

    hover_color="#D97706",

    command=pausar_bot

)
 
btn_pausar.pack(

    pady=8

)
 
 
btn_reanudar = ctk.CTkButton(

    tab_control,

    text="▶  REANUDAR ASISTENTE",

    width=280,

    height=45,

    font=("Arial", 14, "bold"),

    fg_color=COLOR_WTW,

    hover_color=COLOR_WTW_HOVER,

    command=reanudar_bot

)
 
btn_reanudar.pack(

    pady=8

)
 
 
btn_detener = ctk.CTkButton(

    tab_control,

    text="■  DETENER BOT",

    width=280,

    height=45,

    font=("Arial", 14, "bold"),

    fg_color=COLOR_ERROR,

    hover_color="#DC2626",

    command=detener_bot

)
 
btn_detener.pack(

    pady=8

)
 
# INFORMACIÓN DEL BOT
 
info = ctk.CTkFrame(

    tab_control,

    fg_color=COLOR_PANEL,

    corner_radius=10

)
 
info.pack(

    fill="x",

    padx=80,

    pady=30

)
 
 
info_label = ctk.CTkLabel(

    info,

    text="Registros procesados: 0    |    Errores: 0    |    Tiempo: 00:00:00",

    font=("Consolas", 14),

    text_color=COLOR_TEXTO_SECUNDARIO

)
 
info_label.pack(

    pady=20

)

# LOGS DE PRUEBA

agregar_log("Sistema iniciado")

agregar_log("Interfaz lista")

agregar_log("Esperando archivos...")
 
# INICIAR APLICACIÓN

app.mainloop()
 