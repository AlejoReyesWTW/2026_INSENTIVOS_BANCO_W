---
name: ui-progreso-comisiones-dinamicas
status: implemented
---

# UI scroll + comisiones dinámicas + barra de progreso

## Contexto y problema

1. **UI — cards de salida escondidas**: El tab "Archivos" tiene dos secciones
   colapsables (entrada y salida). Cuando el processo termina, la sección de
   salida se habilita abajo, pero si la sección de entrada está abierta, las
   cards de salida quedan ocultas detrás y solo se ven colapsando la entrada.
   Además, con ambas secciones colapsadas queda demasiado espacio vacío entre
   ellas. Se necesita scroll vertical para bajar y ver todo, y un espaciado
   compacto entre secciones.

2. **Comisiones quemadas**: Los valores de incentivo cajero/subgerente están
   hardcodeados en el código y en `Configuracion.json` (tabla_primas:
   2414→137/34, 5072→290/72, 6644→378/95, 11597→658/164). El banco tiene un
   archivo `Bases/Base_Comisiones_Insentivos.xlsx` con esa tabla. Si cambian
   valores a futuro, el sistema debe leerlos de ese archivo automáticamente.

3. **Barra de progreso descriptiva**: El ProgressDialog ya muestra porcentaje,
   paso y tiempo. Se pide mensajes de etapa descriptivos (10% armando
   documento principal, 35% haciendo cruces con los archivos excel, 50%
   armando excel principal, 60% cruce con novedades, etc.).

## Requerimientos

### R1: Scroll en tab Archivos y espaciado compacto

- La sección de entrada debe tener un scroll interno que permita bajar y ver
  todos los bloques sin colapsar la sección de salida.
- Las cards de salida deben ser visibles al bajar (scroll) sin necesidad de
  colapsar la sección de entrada.
- Con ambas secciones colapsadas, deben quedar una debajo de la otra con
  espacio pequeño/moderado (sin hueco grande).
- Con las secciones abiertas, el comportamiento actual se mantiene: todos los
  botones visibles y scroll para bajar cuando aparece la sección de salida.

### R2: Comisiones dinámicas desde Base_Comisiones_Insentivos.xlsx

- Nueva fuente de tabla de primas: `Bases/Base_Comisiones_Insentivos.xlsx`
  (hoja "Hoja1", filas 3-6: col A=prima cajero, col B=comisión cajero,
  col D=prima subgerente, col E=comisión subgerente).
- ConfigLoader debe cargar la tabla de primas desde ese archivo en lugar de
  `tabla_primas` hardcodeada en Configuracion.json.
- Si el archivo no existe, fallback a la tabla actual (no romper el flujo).

### R3: Barra de progreso con etapas descriptivas

- Mensajes de etapa con porcentaje: 10% armando documento principal, 35%
  haciendo cruces con archivos excel, 50% armando excel principal, 60% cruce
  con novedades, etc., hasta 100%.

## Criterios de aceptación

- [ ] Con entrada abierta y salida visible, se puede bajar con scroll y ver las cards.
- [ ] Con ambas secciones colapsadas, el espacio entre headers es compacto.
- [ ] Los cálculos L/M usan valores leídos de Base_Comisiones_Insentivos.xlsx.
- [ ] Si el banco cambia un valor en el xlsx, el archivo de salida refleja el cambio.
- [ ] La barra de progreso muestra porcentajes con mensajes de etapa.

## Verificación (2026-09-11)

- [x] Confirmado que las columnas L/M usan `Bases/Base_Comisiones_Insentivos.xlsx`
      como fuente (vía `tabla_comisiones.path`), no valores hardcodeados.
- [x] Prueba empírica: copia del xlsx con cajero(2414)=999 → el sistema calculó
      L=999 aunque el JSON seguía en 137. El Excel manda.
- [x] `tabla_primas` del JSON queda solo como fallback si falta el archivo.
- [x] Los números del docstring de `comisiones_reader.py` son documentación del
      formato, no lógica ejecutable.
