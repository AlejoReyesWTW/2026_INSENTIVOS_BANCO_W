"""Caso de uso principal: orquestar el procesamiento completo de un ciclo.

Une todos los pasos:
1. Validar los 6 archivos de insumo contra Configuracion.json.
2. Detectar el ciclo (mes/año) del nombre del SOY PREVENIDO.
3. Copiar la plantilla al directorio de salida con nombre dinámico.
4. Llenar las 3 pestañas (Ventas, Base subgerentes, Base red agencias).
5. Insertar fórmulas en Ventas.
6. Guardar y registrar logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from src.application.copiar_plantilla import copiar_plantilla_a_salida
from src.application.detectar_ciclo import detectar_ciclo
from src.application.generar_planilla_pago import generar_planilla_pago
from src.application.insertar_formulas import insertar_formulas_ventas
from src.application.llenar_base_red_agencias import llenar_base_red_agencias
from src.application.llenar_base_subgerentes import llenar_base_subgerentes
from src.application.llenar_ventas import llenar_ventas
from src.application.novedades import aplicar_novedades
from src.application.rellenar_pq_desde_directorio import (
    codigos_pq_vacios,
    completar_cedulas_en_base,
    corregir_nombres_en_base,
    leer_directorio_por_codigos,
    pegar_subgerentes_en_base,
    refrescar_pq,
)
from src.application.validar_insumos import ValidadorInsumos
from src.domain.insumo import TipoInsumo
from src.domain.mes_valido import validar_mes_insumos
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.excel_writer import ExcelWriter
from src.infrastructure.file_utils import generar_nombre_unico_si_existe
from src.infrastructure.logger import LoggerDiario


@dataclass
class ResultadoProceso:
    """Resultado del procesamiento completo de un ciclo de incentivos."""

    exito: bool
    ruta_salida: Path | None = None
    filas_ventas: int = 0
    filas_base_subgerentes: int = 0
    filas_base_red_agencias: int = 0
    ruta_planilla_pago: Path | None = None
    errores: list[str] = field(default_factory=list)


class ProcesarCiclo:
    """Orquesta el procesamiento end-to-end de un ciclo mensual."""

    def __init__(
        self,
        insumos: dict[TipoInsumo, Path],
        config_loader: ConfigLoader,
        logger: LoggerDiario,
        ruta_plantilla: Path,
        directorio_salida: Path,
    ) -> None:
        self.insumos = insumos
        self.config = config_loader
        self.logger = logger
        self.ruta_plantilla = ruta_plantilla
        self.directorio_salida = directorio_salida

    def ejecutar(
        self,
        progress_callback: callable = None,  # type: ignore[type-arg]
    ) -> ResultadoProceso:
        """Ejecuta el flujo completo y retorna el resultado.

        Args:
            progress_callback: opcional, recibe (percent: int, mensaje: str)
                para reportar avance a una UI (ej: ProgressDialog).
        """

        def _avance(percent: int, mensaje: str) -> None:
            """Helper: reporta avance al callback (si existe) + al logger."""
            self.logger.info(f"[{percent}%] {mensaje}")
            if progress_callback is not None:
                progress_callback(percent, mensaje)

        _avance(0, "Iniciando procesamiento del ciclo...")

        # 1. Validar estructura de los insumos.
        _avance(10, "📄 Armando documento principal: validando archivos de insumo...")
        validador = ValidadorInsumos(self.config)
        resultado_validacion = validador.validar(self.insumos)
        if not resultado_validacion.valido:
            errores = []
            for tipo, msgs in resultado_validacion.errores.items():
                errores.append(f"{tipo.value}:")
                errores.extend(f"  - {m}" for m in msgs)
            self.logger.error(
                f"Validación falló con {resultado_validacion.total_errores} errores."
            )
            for e in errores:
                self.logger.error(e)
            return ResultadoProceso(exito=False, errores=errores)

        _avance(15, "✅ Validación OK: estructura de insumos correcta.")

        # 1b. Validar coherencia de mes de los insumos contra el mes actual.
        _avance(
            16,
            "🗓️ Validando coherencia de mes en los archivos de insumo...",
        )
        validacion_mes = validar_mes_insumos(list(self.insumos.values()))
        if not validacion_mes.valido:
            for e in validacion_mes.errores:
                self.logger.error(e)
            return ResultadoProceso(exito=False, errores=validacion_mes.errores)

        # 2. Detectar ciclo del nombre del SOY PREVENIDO.
        ruta_soy_prevenido = self.insumos[TipoInsumo.SOY_PREVENIDO]
        try:
            periodo = detectar_ciclo(ruta_soy_prevenido)
        except Exception as e:
            self.logger.error(f"No se pudo detectar el ciclo: {e}")
            return ResultadoProceso(
                exito=False,
                errores=[f"No se pudo detectar el ciclo: {e}"],
            )
        _avance(20, f"🗓️ Ciclo detectado: {periodo}")

        # 2b. Carpeta de salida por fecha: salidas/<año>/<mes>/<día>
        #     (la operación la ve sin abrir la app).
        directorio_fecha = (
            self.directorio_salida / str(periodo.anio) / periodo.mes / _dia_actual()
        )
        self.directorio_salida = directorio_fecha

        # 3. Construir nombre del archivo de salida.
        nombre_archivo = (
            f"base incentivos {periodo.mes} {periodo.anio} soy prevenido.xlsx"
        )
        _avance(25, f"📁 Archivo de salida: {nombre_archivo}")

        # 4. Copiar plantilla al directorio de salida.
        try:
            self.directorio_salida.mkdir(parents=True, exist_ok=True)
            ruta_destino = self.directorio_salida / nombre_archivo
            ruta_destino = generar_nombre_unico_si_existe(ruta_destino)
            ruta_destino = copiar_plantilla_a_salida(
                plantilla=self.ruta_plantilla,
                directorio_salida=self.directorio_salida,
                nombre_archivo=ruta_destino.name,
            )
            _avance(35, f"📋 Plantilla base copiada: {ruta_destino.name}")
        except Exception as e:
            self.logger.error(f"No se pudo copiar la plantilla: {e}")
            return ResultadoProceso(
                exito=False,
                errores=[f"No se pudo copiar la plantilla: {e}"],
            )

        # 5. Llenar las 3 pestañas.
        filas_ventas = 0
        filas_subgerentes = 0
        filas_red = 0

        writer = ExcelWriter(ruta_destino)
        try:
            # 5a. Ventas desde SOY PREVENIDO.
            _avance(
                45, "🔗 Haciendo cruces con archivos excel: llenando pestaña Ventas..."
            )
            filas_ventas = llenar_ventas(
                ruta_insumo=ruta_soy_prevenido,
                writer=writer,
            )
            _avance(55, f"📊 Ventas: {filas_ventas} filas escritas.")

            # 5b. Base subgerentes desde Base Banco Completa.
            _avance(65, "🔗 Cruce con base de empleados: llenando Base subgerentes...")
            filas_subgerentes = llenar_base_subgerentes(
                ruta_insumo=self.insumos[TipoInsumo.BASE_BANCO],
                writer=writer,
            )
            _avance(72, f"👥 Base subgerentes: {filas_subgerentes} filas.")

            # 5c. Base red agencias desde Base Seguros Actualizada.
            _avance(78, "🔗 Cruce con base de agencias: llenando Base red agencias...")
            filas_red = llenar_base_red_agencias(
                ruta_insumo=self.insumos[TipoInsumo.BASE_SEGUROS],
                writer=writer,
                logger=self.logger,
            )
            _avance(83, f"🏦 Base red agencias: {filas_red} filas.")

            # 6. Insertar fórmulas en Ventas (1a pasada P/Q).
            _avance(85, "🧮 Calculando incentivos y cruzando datos de respaldo...")
            tabla_primas = self.config.cargar_tabla_primas()
            if filas_ventas > 0:
                insertar_formulas_ventas(
                    writer=writer,
                    tabla_primas=tabla_primas,
                    fila_inicio=2,
                    fila_fin=filas_ventas + 1,
                    logger=self.logger,
                )

                # 6b. 2a pasada: rellenar P/Q vacías desde Directorio Nacional.
                _avance(
                    88,
                    "🗂️ Buscando subgerentes faltantes en Directorio Nacional...",
                )
                rellenadas = self._rellenar_pq_desde_directorio(
                    writer=writer,
                    fila_fin=filas_ventas + 1,
                )
                _avance(
                    95,
                    f"🧮 Incentivos calculados; P/Q: {rellenadas} filas completadas.",
                )

                # 6c. Fase Novedades: reemplazos de subgerente (R/S).
                _avance(
                    96,
                    "🔄 Aplicando novedades de subgerente (reemplazos por fecha)...",
                )
                novedades_applicadas = self._aplicar_novedades(
                    writer=writer,
                )
                _avance(
                    97,
                    f"🔄 Novedades: {novedades_applicadas} reemplazos procesados.",
                )

            # 7. Guardar.
            writer.guardar()
            _avance(98, "💾 Guardando archivo Excel principal...")
        finally:
            writer.cerrar()

        ruta_planilla = self.directorio_salida / (
            f"planilla de pago {periodo.mes} {periodo.anio}.xlsx"
        )
        try:
            ruta_planilla = generar_planilla_pago(ruta_destino, ruta_planilla)
            self.logger.info(f"Planilla de pago generada: {ruta_planilla.name}")
            _avance(99, "📄 Planilla de pago generada correctamente.")
        except (OSError, KeyError, ValueError) as e:
            mensaje = f"No se pudo generar la planilla de pago: {e}"
            self.logger.error(mensaje)
            return ResultadoProceso(
                exito=False,
                ruta_salida=ruta_destino,
                ruta_planilla_pago=ruta_planilla,
                filas_ventas=filas_ventas,
                filas_base_subgerentes=filas_subgerentes,
                filas_base_red_agencias=filas_red,
                errores=[mensaje],
            )

        _avance(100, f"🎉 Procesamiento completado: {ruta_destino.name}")
        self.logger.info(f"Procesamiento exitoso: {ruta_destino}")

        return ResultadoProceso(
            exito=True,
            ruta_salida=ruta_destino,
            ruta_planilla_pago=ruta_planilla,
            filas_ventas=filas_ventas,
            filas_base_subgerentes=filas_subgerentes,
            filas_base_red_agencias=filas_red,
        )

    def _aplicar_novedades(
        self,
        writer: ExcelWriter,
    ) -> int:
        """Fase Novedades: aplica reemplazos de subgerente en Ventas R/S.

        Args:
            writer: ExcelWriter abierto sobre el archivo de salida.

        Returns:
            Cantidad de reemplazos de novedades procesados.
        """
        ruta_novedades = self.insumos.get(TipoInsumo.NOVEDADES_SUBGERENTE)
        if ruta_novedades is None:
            self.logger.info(
                "[novedades] No hay archivo de novedades: se omite la fase."
            )
            return 0
        try:
            resultados = aplicar_novedades(
                writer=writer,
                ruta_novedades=ruta_novedades,
                logger=self.logger,
            )
        except (OSError, ValueError, KeyError) as e:
            self.logger.error(f"[novedades] Error aplicando novedades: {e}")
            return 0
        return len(resultados)

    def _rellenar_pq_desde_directorio(
        self,
        writer: ExcelWriter,
        fila_fin: int,
    ) -> int:
        """2a pasada: rellena P/Q vacías de Ventas desde Directorio Nacional.

        Flujo:
          1. Códigos únicos (col N) de filas con P vacía.
          2. Filtrar Directorio Nacional por col B y copiar (COD, SUBGERENTE).
          3. Pegar en Base subgerentes: COD→col H, nombre→col B.
          4. Refrescar P/Q/R/S de Ventas contra la base actualizada.

        Args:
            writer: ExcelWriter abierto sobre el archivo de salida.
            fila_fin: última fila de Ventas (1-based, inclusiva).

        Returns:
            Cantidad de filas de Ventas que quedaron con P/Q llenas tras
            la 2a pasada (0 si no hay Directorio Nacional o no hay vacías).
        """
        ruta_directorio = self.insumos.get(TipoInsumo.DIRECTORIO_NACIONAL)
        if ruta_directorio is None:
            self.logger.info(
                "[2a pasada] No hay Directorio Nacional: se omite el relleno de P/Q."
            )
            return 0

        codigos = codigos_pq_vacios(writer, fila_inicio=2, fila_fin=fila_fin)
        if not codigos:
            self.logger.info(
                "[2a pasada] No hay P/Q vacías: cruce completo en 1a pasada."
            )
            return 0
        self.logger.info(
            f"[2a pasada] {len(codigos)} códigos de agencia con P/Q vacía."
        )

        pares = leer_directorio_por_codigos(ruta_directorio, codigos)
        if not pares:
            self.logger.warning(
                "[2a pasada] Directorio Nacional sin coincidencias para los códigos faltantes."
            )
            return 0
        self.logger.info(
            f"[2a pasada] Directorio Nacional: {len(pares)} subgerentes encontrados."
        )

        pegadas = pegar_subgerentes_en_base(writer, pares)
        self.logger.info(f"[2a pasada] {pegadas} filas agregadas a Base subgerentes.")

        # Paso intermedio 1: corregir nombres erróneos de las filas pegadas
        # usando Correccion_nombres_base_subgerentes.xlsx (si está
        # configurado). Así la búsqueda de cédulas por nombre funciona
        # aunque el Directorio Nacional traiga nombres mal escritos.
        ruta_correcciones = self._ruta_correcciones_nombres()
        if ruta_correcciones is not None:
            corregidos = corregir_nombres_en_base(writer, ruta_correcciones)
            self.logger.info(
                f"[2a pasada] {corregidos} nombres corregidos en Base subgerentes."
            )
        else:
            self.logger.info(
                "[2a pasada] Sin archivo de correcciones: se omite la corrección de nombres."
            )

        # Paso intermedio 2: completar la cédula (col A) de las filas nuevas
        # buscando su nombre en las filas anteriores de la base.
        fila_ini_pegadas = writer._workbook["Base subgerentes"].max_row - len(pares) + 1
        completadas = completar_cedulas_en_base(writer, fila_inicio=fila_ini_pegadas)
        self.logger.info(f"[2a pasada] {completadas} cédulas completadas por nombre.")

        llenas = refrescar_pq(writer, fila_inicio=2, fila_fin=fila_fin)
        self.logger.info(f"[2a pasada] P/Q refrescadas: {llenas} filas.")
        return llenas

    def _ruta_correcciones_nombres(self) -> Path | None:
        """Devuelve la ruta al archivo de correcciones de nombres si existe."""
        try:
            path_rel = self.config.cargar_correcciones_nombres_path()
        except (AttributeError, KeyError, TypeError, ValueError):
            return None
        if path_rel is None:
            return None
        ruta = Path(path_rel)
        if not ruta.exists():
            self.logger.warning(
                f"[2a pasada] Archivo de correcciones no existe: {ruta}"
            )
            return None
        return ruta


def _dia_actual() -> str:
    """Devuelve el día actual como string (sin cero a la izquierda)."""
    return str(date.today().day)
