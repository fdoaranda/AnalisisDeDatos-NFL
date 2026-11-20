---
inclusion: auto
name: ds-05-visualizacion-comunicacion
description: Visualización honesta y comunicación de resultados (elección de gráfica, incertidumbre, color, narrativa, README y presentación). Úsalo al graficar, diseñar dashboards o redactar hallazgos.
---

# Visualización y comunicación

Base: Wilke, *Fundamentals of Data Visualization* (gratuito en línea); Cairo, *The Truthful Art*; Downey, *Think Stats* (flujo de exploración).

## Elegir la gráfica según la pregunta
| Pregunta | Gráfica recomendada |
|---|---|
| ¿Cómo se distribuye una variable? | Histograma, densidad, ECDF, caja/violín |
| ¿Cómo se comparan categorías? | Barras ordenadas (eje desde 0) o puntos con IC |
| ¿Cómo cambia en el tiempo? | Líneas (eje temporal ordenado) |
| ¿Hay relación entre dos variables? | Dispersión (con transparencia/binning si hay mucha densidad) |
| ¿Cómo se compone un total? | Barras apiladas con pocas categorías; evita pasteles con muchas |
| ¿Cómo se comparan muchos grupos con n distinto? | Puntos con IC y n visible, ordenados |

## Reglas de honestidad
- **Barras siempre desde cero**; en líneas/puntos el eje puede recortarse si se indica.
- **Muestra la incertidumbre** (barras de error, bandas) y el **n**. Una diferencia sin intervalo puede ser ruido.
- No uses doble eje ni 3D decorativo. No truncar para exagerar.
- Muestra los datos, no solo el resumen, cuando sea posible (puntos sobre cajas, jitter).
- Ordena categorías por valor (no alfabéticamente) salvo que exista orden natural.
- Escala de colores: secuencial para magnitud, divergente para desviación de un punto medio, categórica solo para pocas clases. Comprueba contraste y que no dependa solo del color (daltonismo).
- Etiqueta ejes con **unidades**. Quita decoración que no informa (tinta sin datos).

## Narrativa: una gráfica, un mensaje
- **El título es el hallazgo** ("Los equipos X rinden 8% mejor tras…"), no la descripción ("Gráfica de rendimiento").
- Estructura de la historia: pregunta -> hallazgo principal -> evidencia -> matices/limitaciones -> implicación para la decisión.
- Máximo 3 mensajes por vista. Lo demás va en detalle bajo demanda.
- Para audiencia no técnica: traduce a unidades de decisión (ej. "ganarías ~X puntos por partido"), no a coeficientes.

## Reporte de resultados (README / presentación)
Incluye siempre: la pregunta, los datos (fuente, filtros, n), el método en lenguaje simple, **resultados con intervalo**, limitaciones y supuestos, y cómo reproducirlo. Declara lo que NO se puede concluir: da más credibilidad, no menos.

## Dashboards
Un KPI principal con su incertidumbre, filtros que cambien el resultado de verdad, estados de carga/error, y un aviso visible cuando una selección tenga n pequeño ("pocos datos: interpretar con cautela").
