---
inclusion: auto
name: ds-01-limpieza-calidad
description: Limpieza, estructura y calidad de datos (tidy data, nulos, duplicados, outliers, unidades, fusiones). Úsalo al cargar, inspeccionar, limpiar o unir datos.
---

# Limpieza y calidad de datos

## Estructura "tidy" (Wickham, 2014)
Un conjunto de datos ordenado cumple tres reglas: (1) cada variable es una columna, (2) cada observación es una fila, (3) cada tipo de unidad observacional forma su propia tabla. Casi todo "dato sucio" es una violación de esto (valores en los encabezados, varias variables en una columna, varias unidades mezcladas). En pandas: `melt`, `pivot`, `split`, `merge`.

## Antes de tocar nada
- **Audita primero, limpia después.** `audit_dataframe(df, key=[...])` no modifica nada. Lee el reporte completo.
- Define la **llave** (qué identifica una fila) y verifica que sea única. Duplicados en la llave = error de datos o llave mal definida.
- Verifica **unidades y escalas** (yardas vs metros, segundos vs frames, 0-1 vs 0-100). Busca el diccionario de datos; si no existe, documenta lo que infieras como [SUPUESTO].
- Guarda los datos originales intactos; limpia en un pipeline (función) reproducible y registra cuántas filas afecta cada paso.

## Valores faltantes
Pregunta **por qué** faltan antes de decidir qué hacer:
- *Faltan al azar* -> eliminar o imputar tiene poco sesgo.
- *Faltan por una razón relacionada con la variable o el resultado* -> eliminar/imputar puede sesgar. Investiga si el patrón de nulos se relaciona con otras columnas (`df.isna().groupby(...)`).
- Un nulo puede significar "no aplica", "no medido" o "cero": no son lo mismo. Nunca rellenes con 0 sin saberlo.
- Si imputas, agrega una columna indicadora de imputación y reporta sensibilidad (resultado con y sin imputar).

## Valores atípicos (outliers)
- Distingue **error** (imposible: velocidad negativa, fuera de rango físico) de **valor extremo legítimo**. Los errores se corrigen/eliminan con justificación; los legítimos NO se borran solo porque "estorban".
- Usa mediana/MAD o cuantiles para detectar; reporta el resultado con y sin ellos.
- Winsorizar o transformar (log) cambia la pregunta; declara cuando lo hagas.

## Duplicados y fusiones (joins)
- Antes de `merge`, cuenta filas y verifica la cardinalidad esperada: `merge(..., validate="one_to_one"|"one_to_many"|"many_to_one")`.
- Después: compara filas antes/después, nulos nuevos, filas sin pareja (`indicator=True`).
- Un join con llave no única multiplica filas y **infla promedios y conteos** en silencio. Es el error más común.

## Tipos y formato
- Fechas a `datetime`, categorías a `category`, IDs como texto (no numérico) para no perder ceros ni hacer aritmética con ellos.
- Texto: normaliza espacios y mayúsculas, pero guarda el original si hay duda.
- Reduce memoria en tablas grandes: `float32`, `category`, leer solo columnas necesarias (`usecols`), procesar por partes (`chunksize`).

## Sesgo de muestreo (pregunta clave)
¿Estos datos representan la población sobre la que quiero concluir? ¿Quién/qué quedó fuera (periodos, equipos, tipos de eventos)? Si la muestra es un subconjunto seleccionado, las conclusiones solo aplican a ese subconjunto. Dilo.

## Lista de verificación mínima (marca cada una con evidencia)
- [ ] n filas/columnas y llave única comprobadas
- [ ] tipos y unidades confirmados
- [ ] nulos analizados (cuántos, dónde, por qué)
- [ ] duplicados revisados
- [ ] rangos físicos/lógicos validados
- [ ] cardinalidad de joins verificada
- [ ] datos originales preservados; pasos de limpieza documentados con conteos
