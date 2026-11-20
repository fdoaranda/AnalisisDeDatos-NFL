---
inclusion: auto
name: ds-03-modelado-validacion
description: Modelado predictivo y validación (línea base, train/test, validación cruzada, fuga de información, métricas, calibración, sobreajuste). Úsalo al construir o evaluar cualquier modelo.
---

# Modelado y validación

## Principios
1. **Empieza por la línea base más simple** (media, mayoría, regla heurística, regresión lineal/logística). Un modelo complejo solo vale si le gana a la línea base **de forma clara y con incertidumbre reportada**.
2. **La evaluación debe imitar el uso real.** Si el modelo predecirá el futuro, valida con tiempo; si predecirá para grupos nuevos (otros partidos, jugadores, sesiones), valida con grupos separados.
3. **Sobreajuste**: error de entrenamiento bajo + error de prueba alto. Más flexibilidad = más riesgo (compromiso sesgo-varianza). La validación cruzada y el conjunto de prueba existen para detectarlo.

## Partición de datos
- *Entrenamiento / validación / prueba*: usa validación para elegir modelo e hiperparámetros; toca el conjunto de **prueba UNA vez** al final.
- *k-fold*: estima el desempeño promediando k particiones. Con datos dependientes usa **GroupKFold** (`group_kfold_indices`) para que un mismo grupo nunca quede en entrenamiento y prueba a la vez.
- *Series de tiempo*: entrena en el pasado, prueba en el futuro (`time_split`). Nada de mezclar al azar.
- Incluye en la validación TODOS los pasos que aprenden de los datos (escalado, imputación, selección de variables): ajústalos solo con el entrenamiento de cada partición.

## Fuga de información (data leakage) - lista de sospechas
- Variables que contienen el resultado o se conocen solo después del evento.
- Filas casi idénticas o del mismo grupo en entrenamiento y prueba.
- Normalizar/imputar/seleccionar variables usando todo el conjunto antes de dividir.
- Usar el futuro para predecir el pasado (ventanas, agregaciones por temporada completa).
- Resultado "demasiado bueno" => asume fuga hasta demostrar lo contrario.

## Métricas (elige según la decisión)
- **Regresión**: MAE (interpretable, robusto), RMSE (castiga errores grandes), R² fuera de muestra. Compara siempre contra la línea base.
- **Clasificación**: exactitud engaña con clases desbalanceadas. Usa precisión/recall/F1 según costo de errores, AUC-ROC (ranking) o PR-AUC (clase rara), y matriz de confusión.
- **Probabilidades**: no basta con acertar la clase; evalúa **calibración** (`calibration_table`) y **Brier score** (`brier_score`). Un modelo que dice 70% debe acertar ~70% de esas veces. Reporta n por intervalo.
- Reporta la **incertidumbre de la métrica** (IC por bootstrap de grupos o variación entre folds), no solo un número.

## Modelos útiles con solo pandas + numpy
Con el stack fijo no hay scikit-learn garantizado. Opciones válidas y explicables: regresión lineal (`ols`), regresión logística por descenso de gradiente/Newton escrita con numpy, k vecinos, árboles de decisión simples, modelos por reglas y tablas de tasas con encogimiento (`shrink_rates`). **Antes de agregar una librería nueva, confirma que `--check` y la entrega siguen funcionando** y que la versión sea compatible; si no, no la uses.

## Interpretabilidad y honestidad
- Un modelo "explica" solo lo que sus variables permiten; la importancia de variables NO es causalidad.
- Revisa errores por subgrupos (¿falla más en ciertos casos?) y casos extremos.
- Documenta: datos usados, partición, métricas, línea base, limitaciones, semilla y versión.
