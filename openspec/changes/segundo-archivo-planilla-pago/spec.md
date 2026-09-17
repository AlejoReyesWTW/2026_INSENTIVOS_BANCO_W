---
name: segundo-archivo-planilla-pago
status: implemented
---

# Segundo archivo de salida: Planilla de pago (tablas de cajeros y subgerentes)

## Contexto y problema

El proceso genera hoy un archivo (archivo 1) con la pestaña Ventas ya cruzada y
con incentivos calculados (col L = CAJERO, col M = SUBGERENTE) y novedades
aplicadas (col R/S con el reemplazo cuando corresponde).

La operación necesita además un **segundo archivo** resumen (planilla de pago)
que muestre, por funcionario, el total de incentivos que generó.

## Requerimiento

Una **sola hoja** con **2 tablas simples** separadas por **2 columnas en blanco**:

```
[Tabla CAJEROS]              [2 cols vacías]   [Tabla SUBGERENTES]
Nombre Cajero | Cédula | Suma                 Nombre Subg. | Cédula | Suma
...           | ...    | ...                  ...          | ...    | ...
```

### Origen de datos (desde el archivo 1, pestaña Ventas)

| Tabla | Nombre | Cédula | Suma |
| --- | --- | --- | --- |
| Cajeros | K (NOMBRE_CAJERO) | J (CC_CAJERO) | SUM(L) por cédula |
| Subgerentes | Q/P (sin novedad) o S/R (con novedad) | idem | SUM(M) por cédula |

- Se **suman las columnas L y M** (no el valor prima).
- En **subgerentes con novedad**, debe aparecer el **reemplazo** (cédula/nombre
  de R/S) — cada uno con lo suyo (el reemplazo con la suma de los días que
  cubrió, el titular con el resto).
- Se lee del **archivo 1 ya generado** (valores, no fórmulas: sin riesgo de
  corrupción de Excel).

## Nombres de archivos y validación de mes

- Los archivos de salida (archivo 1 y planilla de pago) se nombran con el
  **mes actual del sistema** (ej: "base incentivos septiembre 2026 soy
  prevenido.xlsx" y "planilla de pago septiembre 2026.xlsx").
- El **mes esperado = mes actual del sistema** (decisión del usuario).
- **Validación de coherencia**: si un insumo que lleva mes en el nombre
  (SOY PREVENIDO, etc.) NO coincide con el mes esperado → **bloquear el
  proceso** con error (ej: estamos en septiembre y cargan insumos de enero).
- Los archivos de insumo pueden venir con nombre de mes distinto: la validación
  es justamente para detectar ese cruce mal.

## Ubicación y UI

- El archivo 2 se guarda en la **misma carpeta** que el archivo 1
  (`Insumos/Salida/`).
- Debe aparecer en la **card "Planilla de pago (mes/año)"** de la sección
  Archivos de salida (el widget ya existe como placeholder).

## Requerimientos

### R1: Agrupar y sumar cajeros

- Por cada cédula de cajero (col J), sumar los valores de col L.
- Nombre del cajero: col K.

### R2: Agrupar y sumar subgerentes

- Por cada cédula de subgerente (col R si hay novedad, sino P), sumar col M.
- Nombre: col S si hay novedad, sino Q.

### R3: Escribir el archivo con 2 tablas

- Una hoja, con encabezados y filas de cada tabla, separadas por 2 columnas
  en blanco.

### R4: Validación de mes

- Comparar el mes del nombre de cada insumo con mes en el nombre contra el mes
  actual del sistema; si difiere, devolver error y no procesar.

## Criterios de aceptación

- [x] El archivo 2 se genera con las 2 tablas y las sumas correctas.
- [x] Subgerentes con novedad muestran al reemplazo (R/S).
- [x] Ambos archivos de salida usan el mes del ciclo detectado en el nombre.
- [ ] Un insumo con mes distinto al esperado bloquea el proceso con error.
- [x] El archivo 2 aparece en la card "Planilla de pago".
- [x] Sin fórmulas (valores), funciones cortas y validadas (TDD).
