---
name: rellenar-pq-desde-directorio
status: implemented
---

# Rellenar P/Q vacías usando Directorio Nacional (2ª pasada de cruce)

## Contexto y problema

En la salida "base incentivos {mes} {año} soy prevenido.xlsx", la pestaña Ventas
tiene columnas **P (CC_SUBGERENTE)** y **Q (NOMBRE_SUBGERENTE)** que se llenan
cruzando el código de agencia (col N) contra la pestaña **Base subgerentes**
(col H → devuelve col A=cédula / col B=nombre).

Hoy solo 44 de 134 agencias tienen subgerente en Base subgerentes → **90 agencias
quedan con P/Q vacías** porque su subgerente no está en esa pestaña.

El subgerente faltante SÍ está en el insumo **Directorio Nacional** (hoja
'DIRECTORIO ACT'): columna B = COD, columna F = SUBGERENTE (nombre).

## Flujo (2ª pasada)

1. Tras el primer armado de P/Q, **filtrar por columna P** y quedarse con las filas vacías.
2. De esas filas, extraer los **códigos únicos** de la columna N (COD) — sin duplicados.
3. Filtrar **Directorio Nacional** por su columna B (COD) usando esa lista.
4. Copiar del directorio: **col B (COD)** y **col F (SUBGERENTE = nombre)**.
5. Pegar en **Base subgerentes** debajo de la última fila con datos:
   - COD (dir B) → columna **H** (COD AGENCIA)
   - SUBGERENTE (dir F) → columna **B** (EMPLEADO/nombre)
6. **Corregir nombres**: leer `Bases/Correccion_nombres_base_subgerentes.xlsx`
   (F1 título, F2 encabezados "NOMBRE ERRONEO" | "NOMBRE CORRECTO A CAMBIAR",
   datos desde F3) y reemplazar en Base subgerentes todo nombre erróneo por
   su correcto. Se recorre el archivo desde la fila 3; si más adelante se
   agregan más nombres, se procesan automáticamente.
7. **Completar cédulas**: para cada fila nueva pegada, buscar su nombre
   (col B) en las filas ANTERIORES de Base subgerentes; si hay coincidencia
   exacta, copiar la cédula (col A) de esa fila al frente del nombre.
   (El subgerente ya existe como empleado con cédula en la base, solo
   estaba asociado a otra agencia.)
8. **Refrescar el cruce P/Q**: re-ejecutar el armado de P/Q contra la Base
   subgerentes ya actualizada → P muestra la CÉDULA real (no el nombre) y
   Q el nombre.

## Requerimientos

### R1: Detectar P/Q vacías

- Dado el workbook con Ventas lleno, enumerar filas donde P (col 16) está vacía.
- Extraer códigos únicos de col N (col 14) de solo esas filas.

### R2: Consultar Directorio Nacional

- Filtrar la hoja 'DIRECTORIO ACT' por columna B (COD) con la lista de códigos.
- Devolver pares (cod, nombre_subgerente) únicos.

### R3: Pegar en Base subgerentes

- Agregar al final de la pestaña (tras la última fila con datos) una fila por
  (cod, nombre): col B = nombre, col H = cod.

### R4: Refrescar P/Q

- Re-ejecutar el cálculo de P/Q para las filas que estaban vacías (y sus réplicas R/S).

## Criterios de aceptación

- [ ] Tras el flujo completo, no quedan P/Q vacías en filas cuyo código exista en Directorio Nacional.
- [ ] La lista de códigos únicos no tiene duplicados.
- [ ] Las filas nuevas en Base subgerentes quedan debajo de la última con datos.
- [ ] El proceso completo entra en el pipeline de ProcesarCiclo (se ejecuta una 2ª pasada antes de guardar).
