# Entendimiento: llenado de la pestaña "Ventas"

Archivo de salida: **base incentivos MES_AÑO soy prevenido.xlsx**
Pestañas del archivo: `Ventas` (principal), `Base Subgerente` (soporte), `Base red agencias` (soporte).

> **Nota sobre MES_AÑO:** es un marcador variable que cambia según el periodo procesado, con formato tipo mes abreviado + año (ej. "Jun 2026", "JUN 2026", "Ago 2026"). El nombre real del archivo de entrada y de salida cambia cada mes según este patrón.

Este documento describe cómo se arma la tabla de la pestaña **Ventas**, columna por columna, según la especificación de negocio.

---

## 1. Columnas A a K — datos de la transacción y del cajero

Estas columnas se llenan copiando datos del archivo fuente **"soy prevenido MES_AÑO"**, o mediante una fórmula que cruza con la pestaña **Base red agencias**.

| Columna Ventas | Origen | Tipo | Detalle |
|---|---|---|---|
| A | Col. A | Copia directa | — |
| B | Col. B | Copia directa | — |
| C | Col. G | Copia directa | — |
| D | Col. E | Copia directa | — |
| E | Col. H | Copia directa | — |
| F | Col. V | Copia directa | — |
| G | Col. S | Copia directa | — |
| H | Col. Q | Copia directa | — |
| I | Col. AB | Copia + limpieza | Se filtra y quita todo lo que va junto al "@" en el código de usuario |
| J | Fórmula | BUSCARX | `=BUSCARX(@I:I;'Base red agencias'!A:A;'Base red agencias'!C:C;1;0)` — busca el valor de I en la columna A de "Base red agencias" y trae el dato de su columna C |
| K | Col. AC | Copia directa | — |

**Orden de dependencia importante:** la columna I debe limpiarse (quitar "@" y lo que sigue) **antes** de que la fórmula de la columna J pueda hacer el cruce correctamente, ya que J depende del valor ya limpio de I.

**Nota:** las columnas A y B se reutilizan más adelante (ver columnas N y O), no deben descartarse tras copiarse.

---

## 2. Columnas L a M — cálculo de incentivo por valor de prima

Fórmulas tipo `SI` anidado, basadas en el valor de la columna `VALOR PRIMA`:

| Columna | Fórmula |
|---|---|
| L | `=+SI([@[VALOR PRIMA]]=2414;137;SI([@[VALOR PRIMA]]=5072;290;SI([@[VALOR PRIMA]]=6644;378;SI([@[VALOR PRIMA]]=11597;658;0))))` |
| M | `=+SI([@[VALOR PRIMA]]=2414;34;SI([@[VALOR PRIMA]]=5072;72;SI([@[VALOR PRIMA]]=6644;95;SI([@[VALOR PRIMA]]=11597;164;0))))` |

---

## 3. Columnas N a S — bloque del subgerente

| Columna | Origen | Detalle |
|---|---|---|
| N | Col. A (reutilizada) | Copia directa |
| O | Col. B (reutilizada) | Copia directa |
| P | Fórmula BUSCARX | `=BUSCARX(@N:N;'Base subgerentes'!H:H;'Base subgerentes'!A:A;1;0)` — trae la **cédula** del subgerente usando el código de agencia |
| Q | Fórmula BUSCARX | `=BUSCARX(@N:N;'Base subgerentes'!H:H;'Base subgerentes'!B:B;1;0)` — trae el **nombre** del subgerente usando el código de agencia |
| R | = P | Columna de "novedad": se replica (copia y pega) el valor de P |
| S | = Q | Columna de "novedad": se replica (copia y pega) el valor de Q |

**Regla especial de cruce por nombre:** para encontrar la cédula del subgerente **operativo** a partir de su nombre, se busca en el archivo **"Base banco completa SS"**, en la columna **U**; si hay coincidencia exacta, se toma la cédula de la columna **T** de ese mismo archivo.

---

## 4. Puntos abiertos / a confirmar

- El documento original menciona **5 insumos de entrada**, pero solo se detallan con precisión: "soy prevenido MES_AÑO", "Base Subgerente" y "Base red agencias". Falta identificar los otros insumos y qué alimenta el **segundo archivo Excel de salida**.
- Hay dos nombres de fuente que podrían ser el mismo archivo o dos distintos: **"Base subgerentes"** (usada en las fórmulas BUSCARX de P y Q) y **"Base banco completa SS"** (usada para la búsqueda por nombre en columna U / cédula en columna T). Se recomienda confirmar si son la misma base.
- La limpieza de la columna I (quitar "@" y lo que sigue) debe quedar definida como un paso de transformación explícito antes del BUSCARX de la columna J.
