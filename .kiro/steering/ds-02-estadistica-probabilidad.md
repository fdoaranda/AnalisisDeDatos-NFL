---
inclusion: auto
name: ds-02-estadistica-probabilidad
description: Estadística descriptiva e inferencial y probabilidad aplicada (distribuciones, intervalos, bootstrap, permutación, p-valores, tamaños de efecto, comparaciones múltiples, Bayes, tasas con n pequeño).
---

# Estadística y probabilidad aplicada

## 1. Describir antes de inferir
- Para cada variable: n, nulos, mínimo, cuantiles (p5, p25, p50, p75, p95), máximo, media, desviación. **Mira la distribución** (histograma/ECDF) antes de elegir resumen.
- Datos sesgados o con colas pesadas: usa **mediana y cuantiles**; la media puede engañar. Dato multimodal: la media puede no describir a nadie.
- Correlación (Pearson) mide asociación **lineal**; usa Spearman (`serie.corr(method="spearman")`, funciona sin scipy) si es monótona/no lineal o hay outliers. Correlación ≈ 0 no implica independencia. Siempre grafica el diagrama de dispersión: en el cuarteto de Anscombe los 4 conjuntos tienen r≈0.816 y la misma recta, pero uno es curvo, otro tiene un atípico y otro depende de un solo punto. `diagnose_relationship(x, y)` detecta esos tres casos (verificado con los 4 conjuntos); sus umbrales son heurísticos, para revisar la gráfica, no para decidir.

## 2. Incertidumbre: lo que convierte un número en evidencia
- **Intervalo de confianza (IC) 95%**: si repitiéramos el muestreo muchas veces, ~95% de los intervalos construidos así cubrirían el valor verdadero. NO es "95% de probabilidad de que el valor esté aquí" (eso sería un intervalo creíble bayesiano).
- **Bootstrap** (`bootstrap_ci`): remuestrear con reemplazo para aproximar la variabilidad de casi cualquier estadístico (mediana, razón, percentil). Supone observaciones independientes. Por defecto usa bootstrap-t para la media y percentil para el resto. Medido en simulaciones (datos lognormales muy sesgados, n=30): percentil ≈ 88% de cobertura, bootstrap-t ≈ 92%, ambos por debajo del 95% nominal. Con datos muy sesgados y n pequeño di que el IC es aproximado y puede quedar corto.
- **Datos agrupados/dependientes** (varias filas por partido, jugador, sesión): el n efectivo es el número de grupos, no de filas. Usa `cluster_bootstrap_ci` (remuestrea **grupos completos**). Medido: con 20 grupos de 20 filas, el bootstrap por filas cubría ~40-47% en vez de 95%; el de grupos ~92%. Con <20 grupos aun el IC por grupos queda algo corto (la función avisa).
- **Proporciones**: usa el intervalo de **Wilson** (`wilson_interval`), no el normal. Con n pequeño o p cerca de 0/1 la aproximación normal falla. Ejemplo: 3 de 3 NO es "100% seguro": el IC de Wilson va de ~44% a 100%.

## 3. Comparar grupos
- **Prueba de permutación** (`permutation_test`): mezcla etiquetas y mira qué tan extraña es la diferencia observada. Casi sin supuestos, fácil de explicar.
- **Siempre** reporta el **tamaño del efecto** (diferencia de medias con IC, `cohens_d`, razón de riesgos…). Con n enorme, diferencias triviales son "significativas"; con n pequeño, diferencias grandes no lo son.
- Distingue **significancia estadística** de **importancia práctica**: ¿la diferencia importa para la decisión?

## 4. p-valores: los seis principios de la ASA (Wasserstein y Lazar, 2016)
1. Un p-valor indica qué tan incompatibles son los datos con un modelo estadístico especificado.
2. NO mide la probabilidad de que la hipótesis estudiada sea cierta, ni de que los datos se deban solo al azar.
3. Las conclusiones y decisiones no deben basarse solo en si el p-valor pasa un umbral.
4. La inferencia correcta exige reporte completo y transparencia (cuántas pruebas hiciste).
5. Un p-valor o la significancia no mide el tamaño del efecto ni la importancia del resultado.
6. Por sí solo, un p-valor no es una buena medida de evidencia sobre un modelo o hipótesis.
Consecuencia práctica: reporta estimación + IC + n + p-valor (si procede), nunca "p<0.05, por lo tanto cierto".

## 5. Comparaciones múltiples y "p-hacking"
Si pruebas muchas hipótesis o buscas patrones hasta que "algo sale", algunas saldrán significativas por pura casualidad. Reglas:
- Declara de antemano (en `PLAN.md`) qué comparaciones vas a hacer; reporta TODAS las que hiciste.
- Con muchas pruebas, controla la tasa de falsos descubrimientos con Benjamini-Hochberg (`benjamini_hochberg`) o usa Bonferroni si pocas.
- Hallazgos exploratorios = hipótesis, no conclusiones. Confírmalos en datos que no usaste para encontrarlos (otra temporada, otra mitad separada por grupos).

## 6. Probabilidad que se usa a diario
- **Tasa base**: antes de interpretar una evidencia, ¿qué tan común es el evento? Un detector con 95% de acierto sobre un evento raro genera mayoría de falsos positivos. Teorema de Bayes: P(A|B) = P(B|A)·P(A) / P(B).
- **Independencia**: P(A y B) = P(A)·P(B) solo si son independientes. Verifícalo; no lo asumas.
- **Valor esperado** para decisiones: compara opciones por resultado esperado Y por riesgo (varianza, peor caso), no solo por el promedio.
- **Regresión a la media**: valores extremos tienden a ser menos extremos en la siguiente medición. Un "mejor desempeño" excepcional suele venir en parte de suerte.
- **Ley de los pequeños números**: promedios/tasas con n pequeño son muy ruidosos. Los rankings por tasa cruda premian a quienes tienen pocas observaciones.

## 7. Tasas con tamaños de muestra desiguales (rankings)
Un 3/3 no supera a un 90/100 en evidencia. Usa **encogimiento empírico (Beta-Binomial)** con `shrink_rates` (≥10 grupos; si no, fija una fuerza de prior explícita y justifícala) o muestra el IC de Wilson junto a cada tasa y ordena por el límite inferior. Siempre muestra n.

## 8. Regresión lineal: qué vigilar
- Interpreta coeficientes como asociaciones condicionales ("manteniendo lo demás constante"), no como efectos causales salvo diseño causal (`#ds-04`).
- Revisa residuos (patrones, heterocedasticidad), observaciones influyentes, multicolinealidad.
- R² alto no implica buen modelo ni causalidad; evalúa fuera de muestra.
- Los EE clásicos suponen observaciones independientes; con datos agrupados serán demasiado optimistas (medido: IC95 con cobertura real ~74%). Usa `ols(X, y, cluster=ids)` para errores robustos por grupo (cobertura ~92% con 25 grupos). Los IC usan la t de Student exacta (`t_crit`); con z=1.96 y n=12 la cobertura real era ~91%.

## 9. Series de tiempo y dependencia
Observaciones ordenadas en el tiempo no son independientes (autocorrelación). Divide por tiempo, no al azar; cuidado con tendencias y estacionalidad al comparar periodos.
