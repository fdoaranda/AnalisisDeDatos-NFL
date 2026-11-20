---
inclusion: auto
name: ds-04-causalidad-sesgos
description: Causalidad y sesgos al comparar opciones o estimar efectos con datos observacionales (confusores, sesgo de selección, Simpson, supervivencia). Úsalo cuando la pregunta sea "¿X causa/mejora Y?" o "¿qué es mejor, A o B?".
---

# Causalidad y sesgos

Base: Hernán y Robins, *Causal Inference: What If* (libro gratuito). Idea central: la inferencia causal **no se reduce a recetas de análisis**; exige formular con precisión la pregunta causal y declarar los supuestos que la sostienen.

## 1. Formula la pregunta causal con precisión
"¿Es mejor A que B?" significa: **si pudiéramos aplicar A a todos vs B a todos, ¿cómo cambia el resultado?** Define: población, intervención A y B, resultado, horizonte. Sin esto, cualquier cifra es ambigua.

## 2. Por qué comparar promedios observados engaña
En datos observacionales, **quien recibe A no es igual a quien recibe B**. Las decisiones se toman según el contexto, así que los grupos difieren de antemano.
- **Confusión (confounding)**: una causa común de la decisión y del resultado crea una asociación que no es efecto de A. Ajustar por confusores medidos reduce el sesgo; **los no medidos no se pueden corregir con datos**.
- **Sesgo de selección**: condicionar o filtrar por algo influido por la intervención y el resultado (solo casos observados, solo "sobrevivientes") distorsiona la comparación.
- **Paradoja de Simpson**: una tendencia en cada subgrupo puede invertirse al combinarlos. Si hay subgrupos plausibles, **estratifica y compara**.
- **Sesgo de supervivencia**: analizar solo lo que "sobrevivió" a un filtro ignora lo que no pasó.
- **Regresión a la media y suerte**: un grupo seleccionado por resultados extremos tiende a moderarse sin intervención alguna.
- **Causalidad inversa y confusión temporal**: ¿qué ocurrió primero? Una variable medida después del resultado no puede ser su causa.

## 2b. Herramienta probada: `stratified_comparison`
`stratified_comparison(df, treat, outcome, strata=[...])` compara A vs B dentro de contextos, devuelve la diferencia ingenua, la ajustada con IC, la tabla por estrato y los estratos EXCLUIDOS por falta de solapamiento. Verificada con un caso de Simpson sintético (opción B mejor en +0.05 en cada contexto pero usada sobre todo en los difíciles): la ingenua daba −0.43 y la ajustada recuperó +0.05 (IC 0.03-0.07). Límite: solo ajusta por las variables dadas; los confusores no medidos siguen sesgando, y el IC no los incluye.

## 3. Qué hacer en la práctica
1. Dibuja un **diagrama causal** simple (quién influye en quién): tratamiento, resultado, confusores, mediadores, colisionadores. No ajustes por variables que son *consecuencia* del tratamiento (mediadores) ni por colisionadores: puede crear sesgo.
2. **Ajusta por confusores pre-tratamiento**: estratificación, regresión con covariables, emparejamiento (matching) o ponderación. Verifica **solapamiento (positividad)**: si en ciertos contextos solo hay A o solo B, NO hay comparación posible ahí; no extrapoles.
3. Compara en **contextos comparables** (mismas situaciones), no promedios globales.
4. **Análisis de sensibilidad**: ¿qué tan fuerte tendría que ser un confusor no medido para borrar el resultado? Reporta resultados bajo varias especificaciones.
5. **Pruebas de refutación**: placebo (resultado/tratamiento falso), submuestras, ventanas de tiempo distintas. Si la conclusión no sobrevive, no es robusta.
6. Si existe un **experimento o cuasi-experimento** (aleatorización, cambio de regla, umbral arbitrario), úsalo: es la evidencia más fuerte.

## 4. Cómo redactar conclusiones
- Lenguaje proporcional a la evidencia: "se asocia con", "es consistente con", "bajo estos supuestos el efecto estimado es…".
- Evita "causa", "demuestra", "prueba" salvo diseño que lo sostenga.
- Lista siempre los **supuestos no verificables** (no hay confusores no medidos, etc.) y los datos faltantes que cambiarían la conclusión.
- Cuando el resultado de decisión sea binario ("hacer A o B"), presenta la diferencia esperada **con intervalo**, el n por contexto y dónde NO se puede concluir.
