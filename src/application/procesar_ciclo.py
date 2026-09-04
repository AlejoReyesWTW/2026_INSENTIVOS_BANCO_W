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
from pathlib import Path

from src.application.copiar_plantilla import copiar_plantilla_a_salida
from src.application.detectar_ciclo import detectar_ciclo
from src.application.insertar_formulas import insertar_formulas_ventas
from src.application.llenar_base_red_agencias import llenar_base_red_agencias
from src.application.llenar_base_subgerentes import llenar_base_subgerentes
from src.application.llenar_ventas import llenar_ventas
from src.application.validar_insumos import ValidadorInsumos
from src.domain.insumo import TipoInsumo
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

    def ejecutar(self) -> ResultadoProceso:
        """Ejecuta el flujo completo y retorna el resultado."""
        self.logger.info("Iniciando procesamiento del ciclo.")

        # 1. Validar estructura de los insumos.
        self.logger.info("Validando estructura de los insumos...")
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

        self.logger.info("Validación OK.")

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
        self.logger.info(f"Ciclo detectado: {periodo}")

        # 3. Construir nombre del archivo de salida.
        nombre_archivo = (
            f"base incentivos {periodo.mes} {periodo.anio} soy prevenido.xlsx"
        )
        self.logger.info(f"Archivo de salida: {nombre_archivo}")

        # 4. Copiar plantilla al directorio de salida.
        try:
            self.directorio_salida.mkdir(parents=True, exist_ok=True)
            # Determinar el path final ANTES de copiar para evitar
            # sobreescribir archivos de ciclos anteriores.
            ruta_destino = self.directorio_salida / nombre_archivo
            ruta_destino = generar_nombre_unico_si_existe(ruta_destino)
            # Ahora sí copiar al path definitivo.
            ruta_destino = copiar_plantilla_a_salida(
                plantilla=self.ruta_plantilla,
                directorio_salida=self.directorio_salida,
                nombre_archivo=ruta_destino.name,
            )
            self.logger.info(f"Plantilla copiada a: {ruta_destino}")
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
            self.logger.info("Llenando pestaña Ventas...")
            filas_ventas = llenar_ventas(
                ruta_insumo=ruta_soy_prevenido,
                writer=writer,
            )
            self.logger.info(f"Ventas: {filas_ventas} filas.")

            # 5b. Base subgerentes desde Base Banco Completa.
            self.logger.info("Llenando pestaña Base subgerentes...")
            filas_subgerentes = llenar_base_subgerentes(
                ruta_insumo=self.insumos[TipoInsumo.BASE_BANCO],
                writer=writer,
            )
            self.logger.info(f"Base subgerentes: {filas_subgerentes} filas.")

            # 5c. Base red agencias desde Base Seguros Actualizada.
            self.logger.info("Llenando pestaña Base red agencias...")
            filas_red = llenar_base_red_agencias(
                ruta_insumo=self.insumos[TipoInsumo.BASE_SEGUROS],
                writer=writer,
            )
            self.logger.info(f"Base red agencias: {filas_red} filas.")

            # 6. Insertar fórmulas en Ventas.
            self.logger.info("Insertando fórmulas en Ventas...")
            tabla_primas = self.config.cargar_tabla_primas()
            # Si no hay datos en Ventas, no insertamos fórmulas.
            if filas_ventas > 0:
                insertar_formulas_ventas(
                    writer=writer,
                    tabla_primas=tabla_primas,
                    fila_inicio=2,
                    fila_fin=filas_ventas + 1,
                )
                self.logger.info("Fórmulas insertadas en Ventas.")

            # 7. Guardar.
            writer.guardar()
        finally:
            writer.cerrar()

        self.logger.info(f"Procesamiento completado: {ruta_destino}")

        return ResultadoProceso(
            exito=True,
            ruta_salida=ruta_destino,
            filas_ventas=filas_ventas,
            filas_base_subgerentes=filas_subgerentes,
            filas_base_red_agencias=filas_red,
        )
