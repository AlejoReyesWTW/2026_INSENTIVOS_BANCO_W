---
name: novedades-subgerente
status: implemented
---

# Fase Novedades: cruce de reemplazos de subgerente en Ventas

## Contexto y problema

El archivo de salida (Base incentivos mes/año) tiene en la pestaña Ventas las
columnas **R = CC_NOVEDAD_SUBGERENTE** y **S = NOMBRE_NOVEDAD_SUBGERENTE**, que
hoy son réplicas de P/Q. Cuando un subgerente titular tiene permiso (novedad),
otra persona lo reemplaza por un período. Las ventas de ese titular durante el
rango de días deben quedar marcadas con la cédula/nombre del reemplazo en R/S.

El insumo es **Formato novedades subgerente oficina para seguros** (hoja
"Hoja1"): encabezados desde **fila 3**, registros desde **fila 4**.

## Campos del insumo (1-based)

```
A = CEDULA (titular)        B = NOMBRE (titular)
G = INICIO (dd/mm/aaaa)     H = FIN (dd/mm/aaaa)
J = CEDULA (reemplazo)      K = NOMBRE (reemplazo)
```

## Flujo (por cada registro de novedades)

1. Leer cédula reemplazo `J`, nombre reemplazo `K`, fechas `G` (inicio) y
   `H` (fin).
2. En Ventas, buscar las filas donde **R == J** (misma cédula).
3. De esas filas, quedarse solo con las que cumplen:
   `G <= FECHA_TRANSACCION <= H` (columna F).
4. Marcar esas filas: **R = J** y **S = K**.
5. Registrar log por persona (ver Requerimientos).

## Reglas de borde

- Si la cédula J NO aparece en R → no se cambia nada (log SIN DATOS).
- Solo se cambian registros cuyas fechas caen DENTRO del intervalo [G, H].
- Si el rango cubre 15 días pero solo hay ventas en 6 días → se cambian solo
  esos 6 (los días faltantes se pierden; no se inventan registros).
- Si hay 50 registros en 3 días y el rango es del 1 al 15 → se cambian los 50
  de esos 3 días (los que caen en el rango).
- Fila de novedades incompleta (sin J/K o sin G/H) → log + salto de fila.
- Solapamiento de fechas entre novedades → adjudica la primera encontrada +
  warning en log.

## Requerimientos

### R1: Leer novedades

- Leer hoja "Hoja1" con encabezados en fila 3 y registros desde fila 4.
- Devolver lista de registros {cedula_titular, nombre_titular, inicio, fin,
  cedula_reemplazo, nombre_reemplazo}.
- Filas incompletas se reportan y se omiten.

### R2: Aplicar reemplazo en Ventas

- Por registro, encontrar filas de Ventas con R == cedula_reemplazo.
- Filtrar por FECHA_TRANSACCION dentro de [inicio, fin].
- Escribir R y S en las filas que cumplen el rango.

### R3: Log de auditoría por persona

- Persona (nombre, cédula), ventas encontradas, intervalo encontrado
  (mín/máx de fechas), cantidad cambiada, estado:
  - COMPLETO: se cambió todo lo esperado en el rango.
  - PARCIAL: faltaron días (ventas encontradas en menos días que el rango).
  - SIN DATOS: no se encontró la cédula en R.

## Criterios de aceptación

- [ ] Lectura de novedades respeta fila 3 (encabezados) y fila 4+ (datos).
- [ ] Solo se marcan filas de Ventas con R == J y fecha dentro de [G, H].
- [ ] Reglas de borde (sin datos / parcia / fila incompleta) cumplen.
- [ ] El log registra encontrados, intervalo, cambiados y estado por persona.
- [ ] Funciones cortas y validadas (TDD), sin código espagueti.
