---
name: ordenar-ventas-por-fecha
status: implemented
---

# Ordenar Ventas por FECHA_TRANSACCION (más antigua → más reciente)

## Contexto y problema

La pestaña Ventas del archivo de salida se llenaba en el orden en que venían
las filas del insumo SOY PREVENIDO (sin orden definido). El usuario necesita
las ventas ordenadas por la columna **F (FECHA_TRANSACCION)** de más antigua a
más reciente para el armado del segundo archivo y la revisión de datos.

## Solución

- Nueva función `_clave_orden_fecha()` en `src/application/llenar_ventas.py`.
- Soporta fechas `date`, `datetime` y `str` en formatos `yyyy-mm-dd`,
  `dd/mm/yyyy`, `dd-mm-yyyy`, `yyyy/mm/dd`.
- Las filas sin fecha parseable (None / texto inválido) van al final.
- Se aplica con `filas_para_escribir.sort(key=_clave_orden_fecha)` antes de
  escribir en la pestaña Ventas (paso 5b).

## Criterios de aceptación

- [x] Las filas de Ventas quedan ordenadas por F en orden ascendente.
- [x] Cada fila conserva sus datos (los campos acompañan a su fecha).
- [x] Fechas formato dd/mm/yyyy (real del banco) se ordenan correctamente.
- [x] Filas sin fecha válida no rompen el orden (van al final).
- [x] Tests: 2 nuevos en test_llenar_ventas (orden + integridad por fila). 205 tests totales.
