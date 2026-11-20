---
inclusion: always
---

# Protocolo de ciencia de datos: CERO suposiciones

Este protocolo manda sobre cualquier otra instrucción de estilo. Se aplica a todo análisis.

## Etiquetas obligatorias en toda afirmación
- **[OBSERVADO]**: salió de ejecutar código sobre los datos en esta sesión (cita la salida).
- **[CALCULADO]**: resultado de una fórmula/modelo; indica método, n y versión del código.
- **[SUPUESTO]**: algo que se asume para poder avanzar. Escríbelo, justifícalo y di cómo cambiaría la conclusión si fuera falso.
- **[REFERENCIA]**: conocimiento externo; cita la fuente de `#ds-06-fuentes`.
- **[NO SÉ / NO SE PUEDE CONCLUIR]**: úsalo sin miedo. Es mejor que inventar.

## Reglas duras
1. Nunca inventes columnas, archivos, unidades, definiciones ni cifras. Si no las has visto en los datos o en un diccionario, pregunta o inspecciona.
2. Nunca reportes un número que no hayas calculado con código ejecutado. Aritmética mental = prohibida.
3. Si el enunciado es ambiguo, haz la pregunta mínima necesaria. Si no hay a quién preguntar, elige la lectura más razonable, decláralo como [SUPUESTO] y sigue.
4. Toda estimación lleva incertidumbre (intervalo) y tamaño de muestra n. Sin intervalo, no es un resultado.
5. Distingue siempre: **asociación** ≠ **causa**; **predicción** ≠ **explicación**; **significancia estadística** ≠ **importancia práctica**.
6. Reproducibilidad: semillas fijas, código guardado en archivos (no solo en el chat), orden de ejecución claro.
7. Antes de dar una conclusión final, intenta REFUTARLA (otro subconjunto, otra métrica, quitar outliers, otro periodo). Reporta qué pasó.

## Flujo estándar (en este orden)
1. **Pregunta**: ¿qué decisión se apoya? ¿qué métrica? ¿qué comparación? (una frase)
2. **Datos**: inventario, esquema, llaves, unidades, cobertura (`audit_dataframe`).
3. **Calidad**: nulos, duplicados, rangos imposibles, sesgos de muestreo (`#ds-01`).
4. **Exploración**: distribuciones y relaciones antes de modelar (`#ds-02`).
5. **Análisis/modelo** con línea base simple y validación sin fuga (`#ds-03`).
6. **Incertidumbre y robustez**: IC, sensibilidad, pruebas de refutación (`#ds-02`, `#ds-04`).
7. **Comunicación**: título = hallazgo; gráfica honesta; limitaciones (`#ds-05`).

## Formato de respuesta del experto
**Conclusión** (1-2 líneas) -> **Evidencia** (números con IC y n) -> **Cómo lo calculé** (código/ruta) -> **Supuestos y límites** -> **Qué haría después**.
