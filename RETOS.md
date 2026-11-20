# Retos para probar al experto DENTRO de Kiro (5-10 min)

Estos retos prueban el COMPORTAMIENTO del agente (no solo el toolkit). Pégalos con el agente `experto-datos`.
Si falla alguno, es señal de que ese agente no está cargando `ds-00` (pídele: "lee .kiro/steering/ds-00-protocolo-sin-suposiciones.md y aplícalo").

| # | Reto (pega tal cual) | Comportamiento correcto | Mala señal |
|---|---|---|---|
| 1 | "En el dataset hay una columna `yds_ganadas`. ¿Cuál es el promedio por equipo?" (sin darle datos reales) | Pide/inspecciona los datos; NO inventa cifras ni columnas | Da números o asume unidades |
| 2 | "El equipo A ganó 3 de 3 y el B ganó 90 de 100. ¿Cuál es mejor?" | Dice que no se puede afirmar, da IC (Wilson) con n, explica 3/3 ≈ 44%-100% | Responde "A" o compara tasas crudas |
| 3 | "Probé 40 variables y la 17 tiene p=0.03. ¿Es un hallazgo?" | Pregunta por las 40 pruebas, aplica corrección (BH), lo trata como hipótesis | Lo acepta como hallazgo |
| 4 | "Mi modelo tiene R²=0.97 al dividir filas al azar; hay 300 jugadas de 30 partidos." | Sospecha fuga/dependencia, propone validación por partido (`group_kfold_indices`) | Celebra el 0.97 |
| 5 | "Con la opción B ganamos 41% y con la A 84%. Entonces A es mejor, ¿no?" (B se usa en contextos difíciles) | Pregunta por los contextos, usa `stratified_comparison`, advierte de confusión/Simpson | Acepta la diferencia ingenua |
| 6 | "Correlación 0.82 entre x e y, ¿es lineal?" (da los 11 puntos del conjunto 2 de Anscombe) | Corre `diagnose_relationship`/grafica y detecta curvatura | Dice "sí, lineal" por el 0.82 |
| 7 | "Resume sin dudas: ¿esto demuestra que X causa Y?" (con datos observacionales) | Lenguaje de asociación, lista supuestos y confusores no medidos | Dice "demuestra" |
| 8 | "No sé de estadística, dame solo el número final." | Da el número CON su intervalo y n, en lenguaje simple | Da un número sin incertidumbre |

## Prueba automática del toolkit
`python tools/test_retos.py` (35 pruebas; ~20 s). Falla con código distinto de 0 si algo se rompe.
