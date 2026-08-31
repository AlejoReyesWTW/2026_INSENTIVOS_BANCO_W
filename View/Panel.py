import customtkinter as ctk
from customtkinter import CTkImage
from tkinter import filedialog
from datetime import datetime
from PIL import Image
import openpyxl
import os
import sys

# CONFIGURACIÓN GENERAL
ctk.set_appearance_mode("dark")
# COLORES
COLOR_WTW = "#FF6900"
COLOR_WTW_HOVER = "#00A3AD"
COLOR_FONDO = "#ffffff"
COLOR_PANEL = "#202027"
COLOR_PANEL_2 = "#292931"

COLOR_TEXTO = "#1F7797"
COLOR_TEXTO_SECUNDARIO = "#181818"

COLOR_OK = "#22C55E"
COLOR_WARNING = "#F59E0B"
COLOR_ERROR = "#EF4444"

COLOR_DESHABILITADO = "#7F33CF"

BASE_DIR= os.path.dirname(os.path.abspath(__file__))

# ESTRUCTURA DE LOS ARCHIVOS
#
# IMPORTANTE:
#
# Aquí NO ponemos el nombre físico del archivo.
#
# Por ejemplo:
#
# Agosto.xlsx
# Septiembre.xlsx
# Octubre.xlsx
#
# Todos pueden ser válidos.
#
# Lo que se valida es la estructura interna del Excel.

ESTRUCTURAS_REQUERIDAS = {
    "Directorio Nacional": {
        "hojas": {
            "DIRECTORIO ACT": ["OFICINA", "COD", "R", "Z", "COORD RED ASIGNADO", "SUBGERENTE", "SUBGERENTE REEMPLAZO", "AUXILIAR OPERATIVO DE OFICINA",
                            "OFICINA CUENTA CON CAN", "MUNICIPIO DE UBICACION CAN", "SUBGERENTE COMERCIAL DE EXPANSION  ( CAN)", "GERENTE DE OFICINA", "GERENTE DE ZONA", "GERENTE REGIONAL"]
        }
    },
    "Formato novedades subgerente oficina para seguros": { "fila_encabezado": 3,
        "hojas": {"Hoja1": ["CEDULA", "NOMBRE", "CARGO", "CODIGO OFICINA", "OFICINA", "USUARIO (Iniciales de 3 letras)", "INICIO (DD/MM/AAAA)", "FIN (DD/MM/AAAA)", "DIAS", "CEDULA", "NOMBRE", "CARGO", "CODIGO OFICINA", "OFICINA", "MOTIVO DE REEMPLAZO", "USUARIO (Iniciales de 3 letras)"],
    }},
    
    "Base Temporal Completa SS": {"hojas": {"Activos Jun 2026": ["CEDULA", "COLABORADOR", "CARGO", "FECHA INGRESO", "VICEPRESIDENCIA", "REGIONAL", "ZONA", "CENTRO DE COSTOS", "COD OFIC", "OFICINA","LOCA", "LOCALIDAD PAGO", "TELEFONO", "EMAIL", "FECHA NACIMIENTO", "SEXO", "ENTIDAD DE SALUD", "FONDO DE PENSIONES", "CAJA DE COMPENSACIÓN"],       
    "Ingresos Jun": ["CEDULA", "COLABORADOR", "CARGO", "FECHA INGRESO", "VICEPRESIDENCIA", "REGIONAL", "ZONA", "CENTRO DE COSTOS" , "COD OFIC", "OFICINA", "LOCA", "LOCALIDAD PAGO", "TELEFONO", "EMAIL", "FECHA NACIMIENTO", "SEXO", "ENTIDAD DE SALUD", "FONDO DE PENSIONES", "CAJA DE COMPENSACION"],
    "Retirados Jun": ["CEDULA", "COLABORADOR", "CARGO", "FECHA INGRESO", "VICEPRESIDENCIA", "REGIONAL", "ZONA", "CENTRO DE COSTO" , "COD OFIC", "OFICINA", "LOCA", "LOCALIDAD PAGO", "TELEFONO", "EMAIL", "FECHA NACIMIENTO", "SEXO", "ENTIDAD DE SALUD", "FONDO DE PENSIONES", "CAJA DE COMPENSACION"]}},
    
    "Base Banco Completa SS": {"hojas": {"Base Banco Activos al 31 Jun": ["CEDULA", "CUENTA CLIENTE", "COLABORADOR", "COD CARGO", "COD GRADO", "CARGO", "FECHA INGRESO", "FECHA FIN CONTRATO", "VICEPRESIDENCIA", "GERENCIA","AREA", "ESTADO", "TIPO NOMINA", "CENTRO DE COSTOS", "LOCALIDAD", "COD OFIC", "OFICINA", "LOCA", "LOCALIDA PAGO", "CODIGO JEFE", "JEFE INMEDIATO", "EMAIL", "TELEFONO", "FECHA NACIMIENTO", "SEXO", "ENTIDAD DE SALUD", "FONDO DE PENSIONES", "FONDO DE CESANTIAS", "CAJA DE COMPENSACIÓN FAMILIAR"],       
    "Ingresos Jun 2026": ["CEDULA", "CUENTA CLIENTE", "COLABORADOR", "COD CARGO", "COD GRADO", "CARGO", "FECHA INGRESO", "FECHA FIN CONTRATO", "VICEPRESIDENCIA", "GERENCIA","AREA", "ESTADO", "TIPO NOMINA", "CENTRO DE COSTOS", "LOCALIDAD", "COD OFIC", "OFICINA", "LOCA", "LOCALIDA PAGO", "CODIGO JEFE", "JEFE INMEDIATO", "EMAIL", "TELEFONO", "FECHA NACIMIENTO", "SEXO", "ENTIDAD DE SALUD", "FONDO DE PENSIONES", "FONDO DE CESANTIAS", "CAJA DE COMPENSACIÓN FAMILIAR"],
    "Retiros Jun 2026": ["CEDULA", "CUENTA CLIENTE", "COLABORADOR", "COD CARGO", "COD GRADO", "CARGO", "FECHA INGRESO", "FECHA RETIRO", "VICEPRESIDENCIA", "GERENCIA","AREA", "ESTADO", "TIPO NOMINA", "CENTRO DE COSTOS", "LOCALIDAD", "COD OFC", "OFICINA", "LOCA", "LOCALIDAD PAGO", "CODIGO JEFE", "JEFE INMEDIATO", "EMAIL", "TELEFONO", "FECHA NACIMIENTO", "SEXO", "ENTIDAD DE SALUD", "FONDO DE PENSIONES", "FONDO DE CESANTÍAS", "CAJAS DE COMPENSACIÓN"]}},
    
    "Base Seguros – Actualizada": {"hojas": {"Registros": ["ID", "Estado", "Fecha"]}},
}

# VARIABLES GLOBALES

archivos = {}
bot_ejecutando = False
bot_pausado = False

# CREAR VENTANA PRINCIPAL
app = ctk.CTk()
app.title("WTW - Control de Automatización")
app.geometry("1000x600")
app.minsize(1050, 650)
app.configure(fg_color=COLOR_FONDO)

# FUNCIONES DE LOG


def agregar_log(mensaje, tipo="INFO"):
    hora = datetime.now().strftime("%H:%M:%S")
    log_text.configure(state="normal")
    if tipo == "ERROR":
        log_text.insert("end", f"[{hora}] ERROR   | {mensaje}\n", "error")
    elif tipo == "WARNING":
        log_text.insert("end", f"[{hora}] WARNING | {mensaje}\n", "warning")
    else:
        log_text.insert("end", f"[{hora}] INFO    | {mensaje}\n", "info")
    log_text.see("end")
    log_text.configure(state="disabled")


def agregar_error(mensaje):
    hora = datetime.now().strftime("%H:%M:%S")
    errores_text.configure(state="normal")
    errores_text.insert("end", f"[{hora}] {mensaje}\n")
    errores_text.see("end")
    errores_text.configure(state="disabled")

# VALIDAR EXTENSIÓN

def validar_extension(ruta):
    return ruta.lower().endswith(".xlsx")

# VALIDAR ESTRUCTURA DEL EXCEL

def validar_excel(ruta, tipo_archivo):

    errores = []
    try:
        # VALIDAR EXTENSIÓN
        if not validar_extension(ruta):
            errores.append("El archivo debe tener extensión .xlsx")
            return False, errores
        # VALIDAR QUE EXISTA
        if not os.path.exists(ruta):
            errores.append("El archivo seleccionado no existe.")
            return False, errores
        # ABRIR EXCEL

        libro = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
        # OBTENER ESTRUCTURA ESPERADA

        estructura = ESTRUCTURAS_REQUERIDAS[tipo_archivo]
        hojas_requeridas = estructura["hojas"]

        # VALIDAR HOJAS

        hojas_existentes = libro.sheetnames
        for nombre_hoja, columnas_requeridas in hojas_requeridas.items():
            # ¿EXISTE LA HOJA?
            if nombre_hoja not in hojas_existentes:
                errores.append(f"No existe la hoja '{nombre_hoja}'.")
                continue
            # OBTENER HOJA
            hoja = libro[nombre_hoja]

            # LEER PRIMERA FILA
            fila_encabezado = estructura.get("fila_encabezado", 1)

            primera_fila = next(
                hoja.iter_rows(
                    min_row=fila_encabezado,
                    max_row=fila_encabezado,
                    values_only=True
                ),
                None
            )
            if primera_fila is None:
                errores.append(f"La hoja '{nombre_hoja}' está vacía.")
                continue

            # LIMPIAR ENCABEZADOS

            encabezados = []
            for valor in primera_fila:
                if valor is not None:
                    encabezado = str(valor).strip()
                    encabezados.append(encabezado)

            # VALIDAR COLUMNAS

            for columna in columnas_requeridas:
                if columna not in encabezados:
                    errores.append(
                        f"Hoja '{nombre_hoja}': " f"falta la columna '{columna}'."
                    )

        libro.close()

        # RESULTADO
        if errores:
            return False, errores
        return True, []
    except Exception as error:
        errores.append(f"No fue posible leer el archivo: {error}")
        return False, errores


# ACTUALIZAR ESTADO DEL


def comprobar_archivos_completos():
    todos_validos = True
    for tipo, datos in archivos.items():
        if datos["valido"] is not True:
            todos_validos = False
            break
    if todos_validos:
        btn_iniciar.configure(state="normal", fg_color=COLOR_OK, hover_color="#16A34A")
        estado_general.configure(
            text="● Todos los archivos están listos", text_color=COLOR_OK
        )

    else:
        btn_iniciar.configure(
            state="disabled",
            fg_color=COLOR_DESHABILITADO,
            hover_color=COLOR_DESHABILITADO,
        )
        estado_general.configure(
            text="● Esperando archivos válidos", text_color=COLOR_WARNING
        )

# SELECCIONAR

def seleccionar_archivo(tipo_archivo):
    datos = archivos[tipo_archivo]
    entry = datos["entry"]
    estado = datos["estado"]
    mensaje = datos["mensaje"]

    # SELECCIONAR SOLO XLSX
    ruta = filedialog.askopenfilename(
        title=f"Seleccionar {tipo_archivo}", filetypes=[("Archivos Excel", "*.xlsx")]
    )
    if not ruta:
        return
    # MOSTRAR RUTA

    entry.delete(0, "end")
    entry.insert(0, ruta)

    # ESTADO VALIDANDO

    estado.configure(text="● Validando...", text_color=COLOR_WARNING)
    mensaje.configure(text="")
    datos["valido"] = False
    comprobar_archivos_completos()
    app.update_idletasks()

    # VALIDAR

    valido, errores = validar_excel(ruta, tipo_archivo)
    # ARCHIVO VÁLIDO

    if valido:

        datos["valido"] = True
        estado.configure(text="● Archivo válido", text_color=COLOR_OK)
        mensaje.configure(
            text="Estructura validada correctamente.", text_color=COLOR_OK
        )
        agregar_log(f"{tipo_archivo}: archivo validado correctamente.")

    # ARCHIVO INVÁLIDO

    else:

        datos["valido"] = False
        estado.configure(text="● Archivo inválido", text_color=COLOR_ERROR)
        mensaje.configure(text=errores[0], text_color=COLOR_ERROR)
        agregar_log(f"{tipo_archivo}: archivo inválido.", "ERROR")
        for error in errores:
            agregar_error(f"{tipo_archivo} → {error}")
    comprobar_archivos_completos()


# CREAR BLOQUE DE ARCHIVO


def crear_bloque_archivo(parent, tipo_archivo):
    contenedor = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
    contenedor.pack(fill="x", padx=25, pady=8)
    # FILA PRINCIPAL

    fila = ctk.CTkFrame(contenedor, fg_color="transparent")
    fila.pack(fill="x", padx=15, pady=(12, 5))

    # NOMBRE DEL TIPO DE ARCHIVO

    nombre = ctk.CTkLabel(
        fila, text=tipo_archivo, width=190, anchor="w", font=("Arial", 14, "bold")
    )

    nombre.pack(side="left")

    # RUTA

    entry = ctk.CTkEntry(
        fila,
        height=38,
        placeholder_text="Seleccione un archivo .xlsx...",
        fg_color=COLOR_PANEL_2,
        border_color=COLOR_PANEL_2,
    )

    entry.pack(side="left", fill="x", expand=True, padx=10)

    # ESTADO

    estado = ctk.CTkLabel(
        fila, text="● Pendiente", width=130, text_color=COLOR_WTW
    )

    estado.pack(side="left")

    # BOTÓN BUSCAR

    boton = ctk.CTkButton(
        fila,
        text="Buscar",
        width=100,
        height=35,
        fg_color=COLOR_WTW,
        hover_color=COLOR_WTW_HOVER,
        command=lambda: seleccionar_archivo(tipo_archivo),
    )

    boton.pack(side="left", padx=(10, 5))

    # MENSAJE

    mensaje = ctk.CTkLabel(contenedor, text="", anchor="w", font=("Arial", 12))

    mensaje.pack(fill="x", padx=205, pady=(0, 10))

    # GUARDAR REFERENCIAS

    archivos[tipo_archivo] = {
        "entry": entry,
        "estado": estado,
        "mensaje": mensaje,
        "valido": False,
    }

# INICIAR BOT

def iniciar_bot():

    global bot_ejecutando
    global bot_pausado

    bot_ejecutando = True
    bot_pausado = False

    estado_bot.configure(text="● Ejecutando", text_color=COLOR_OK)

    agregar_log("Todos los archivos fueron validados.")

    agregar_log("Iniciando asistente...")

    # ejecutar_robot()

# PAUSAR BOT

def pausar_bot():

    global bot_pausado

    if not bot_ejecutando:

        agregar_log("No hay un bot ejecutándose.", "WARNING")

        return

    bot_pausado = True

    estado_bot.configure(text="● Pausado", text_color=COLOR_WARNING)

    agregar_log("Asistente pausado.", "WARNING")

# REANUDAR BOT

def reanudar_bot():
    global bot_pausado
    if not bot_ejecutando:
        return
    bot_pausado = False
    estado_bot.configure(text="● Ejecutando", text_color=COLOR_OK)
    agregar_log("Asistente reanudado.")


# DETENER BOT


def detener_bot():

    global bot_ejecutando
    global bot_pausado
    bot_ejecutando = False
    bot_pausado = False
    estado_bot.configure(text="● Detenido", text_color=COLOR_ERROR)

    agregar_log("Bot detenido.", "WARNING")


# ENCABEZADO


header = ctk.CTkFrame(app, height=80, fg_color=COLOR_PANEL, corner_radius=0)
header.pack(fill="x")
header.pack_propagate(False)

# CARGAR LOGO
ruta_logo = os.path.join(BASE_DIR, "..", "IMG", "imagen (1).png")
logo_img = Image.open(ruta_logo)  # <-- pon aquí la ruta de tu imagen
 
logo_ctk = CTkImage(
    light_image=logo_img,
    dark_image=logo_img,
    size=(120, 50)  # <-- ajusta ancho x alto según tu logo
)
 
titulo = ctk.CTkLabel(
    header,
    image=logo_ctk,
    text="",  # importante: vacío, si no aparece texto encima
)
 
titulo.pack(side="left", padx=30)


subtitulo = ctk.CTkLabel(
    header, text="Control de Automatización", font=("Arial", 18), text_color=COLOR_FONDO
)

subtitulo.pack(side="left")


estado_bot = ctk.CTkLabel(
    header, text="● Detenido", font=("Arial", 15, "bold"), text_color=COLOR_ERROR
)

estado_bot.pack(side="right", padx=30)

# PESTAÑAS


tabs = ctk.CTkTabview(
    app,
    fg_color=COLOR_FONDO,
    segmented_button_fg_color=COLOR_PANEL,
    segmented_button_selected_color=COLOR_WTW,
    segmented_button_selected_hover_color=COLOR_WTW_HOVER,
    segmented_button_unselected_color=COLOR_PANEL,
    segmented_button_unselected_hover_color=COLOR_PANEL_2,
)

tabs.pack(fill="both", expand=True, padx=20, pady=20)


tab_archivos = tabs.add("Archivos")

tab_logs = tabs.add("Ejecución")

tab_errores = tabs.add("Errores")

tab_control = tabs.add("Control")

# PESTAÑA ARCHIVOS

titulo_archivos = ctk.CTkLabel(
    tab_archivos, text="Archivos de entrada", font=("Arial", 24, "bold"),
    text_color=COLOR_WTW_HOVER,
)

titulo_archivos.pack(anchor="w", padx=25, pady=(25, 5))


descripcion = ctk.CTkLabel(
    tab_archivos,
    text=(
        "Seleccione los archivos requeridos. "
        "La estructura será validada automáticamente."
    ),
    font=("Arial", 14),
    text_color=COLOR_TEXTO_SECUNDARIO,
)

descripcion.pack(anchor="w", padx=25, pady=(0, 15))

scroll_archivos = ctk.CTkScrollableFrame(
    tab_archivos,
    fg_color="transparent"
)

scroll_archivos.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# CREAR LOS BLOQUES DENTRO DEL FRAME CON SCROLL
# (antes se creaban en tab_archivos, por eso no se podía bajar)

crear_bloque_archivo(scroll_archivos, "Directorio Nacional")

crear_bloque_archivo(scroll_archivos, "Formato novedades subgerente oficina para seguros")

crear_bloque_archivo(scroll_archivos, "Base Temporal Completa SS")

crear_bloque_archivo(scroll_archivos, "Base Banco Completa SS")

crear_bloque_archivo(scroll_archivos, "Base Seguros – Actualizada")


# ESTADO GENERAL
# (queda fuera del scroll, fijo debajo del listado)

estado_general = ctk.CTkLabel(
    tab_archivos,
    text="● Esperando archivos válidos",
    font=("Arial", 14, "bold"),
    text_color=COLOR_WARNING,
)

estado_general.pack(pady=(15, 10))

# BOTÓN INICIAR BOT
# (también fijo fuera del scroll)

btn_iniciar = ctk.CTkButton(
    tab_archivos,
    text="▶  INICIAR BOT",
    width=240,
    height=45,
    font=("Arial", 14, "bold"),
    fg_color=COLOR_DESHABILITADO,
    hover_color=COLOR_DESHABILITADO,
    state="disabled",
    command=iniciar_bot,
    text_color=COLOR_TEXTO_SECUNDARIO
)

btn_iniciar.pack(pady=10)

# PESTAÑA EJECUCIÓN


titulo_logs = ctk.CTkLabel(
    tab_logs, text="Log de ejecución", font=("Arial", 24, "bold"),
    text_color=COLOR_TEXTO_SECUNDARIO
,
)

titulo_logs.pack(anchor="w", padx=25, pady=(25, 10))


log_text = ctk.CTkTextbox(
    tab_logs,
    fg_color="#101014",
    text_color=COLOR_TEXTO,
    font=("Consolas", 13),
    corner_radius=10,
)

log_text.pack(fill="both", expand=True, padx=25, pady=(0, 25))


log_text.tag_config("info", foreground=COLOR_TEXTO)

log_text.tag_config("warning", foreground=COLOR_WARNING)

log_text.tag_config("error", foreground=COLOR_ERROR)


log_text.configure(state="disabled")

# PESTAÑA ERRORES


titulo_errores = ctk.CTkLabel(
    tab_errores, text="Registro de errores", font=("Arial", 24, "bold"),
    text_color=COLOR_TEXTO_SECUNDARIO,
)

titulo_errores.pack(anchor="w", padx=25, pady=(25, 10))


errores_text = ctk.CTkTextbox(
    tab_errores,
    fg_color="#101014",
    text_color=COLOR_ERROR,
    font=("Consolas", 13),
    corner_radius=10,
)

errores_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))


errores_text.configure(state="disabled")
# PESTAÑA CONTROL


titulo_control = ctk.CTkLabel(
    tab_control, text="Control del asistente", font=("Arial", 24, "bold"), text_color=COLOR_TEXTO_SECUNDARIO,
)

titulo_control.pack(pady=(30, 20))


btn_pausar = ctk.CTkButton(
    tab_control,
    text="Ⅱ  PAUSAR ASISTENTE",
    width=280,
    height=45,
    font=("Arial", 14, "bold"),
    fg_color=COLOR_WARNING,
    hover_color="#D97706",
    command=pausar_bot,
)

btn_pausar.pack(pady=8)


btn_reanudar = ctk.CTkButton(
    tab_control,
    text="▶  REANUDAR ASISTENTE",
    width=280,
    height=45,
    font=("Arial", 14, "bold"),
    fg_color=COLOR_WTW,
    hover_color=COLOR_WTW_HOVER,
    command=reanudar_bot,
)

btn_reanudar.pack(pady=8)


btn_detener = ctk.CTkButton(
    tab_control,
    text="■  DETENER BOT",
    width=280,
    height=45,
    font=("Arial", 14, "bold"),
    fg_color=COLOR_ERROR,
    hover_color="#DC2626",
    command=detener_bot,
)

btn_detener.pack(pady=8)

# INFORMACIÓN


info_frame = ctk.CTkFrame(tab_control, fg_color=COLOR_PANEL, corner_radius=10)

info_frame.pack(fill="x", padx=80, pady=30)


info_label = ctk.CTkLabel(
    info_frame,
    text=("Registros procesados: 0    |    " "Errores: 0    |    " "Tiempo: 00:00:00"),
    font=("Consolas", 14),
    text_color=COLOR_FONDO,
)

info_label.pack(pady=20)

# LOG INICIAL


agregar_log("Sistema iniciado.")

agregar_log("Interfaz lista.")

agregar_log("Esperando archivos...")

# EJECUTAR APLICACIÓN

app.mainloop()