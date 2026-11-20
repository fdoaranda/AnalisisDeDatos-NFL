---
inclusion: always
---

# Contexto: Hackathon NFL Big Data Bowl UNAM ("Side Quest")

- Evento de 3 horas (10:00 a 13:00), equipo de 2. Gana lo que se ENTREGA funcionando, no lo más ambicioso.
- **El reto (diapositiva oficial):** crear una herramienta o visualización para un **entrenador, scout o comentarista de la NFL**. El punto es encontrar **insights** que sirvan para coachear, hacer scouting o televisar.
- **Dos formatos posibles (elegir UNO):** (1) Visualización / herramienta de comparación: gráfica, tablero, animación o herramienta interactiva. (2) Métrica / puntuación: inventar una estadística que cuantifique algo aún no medido.
- **Datos:** seguimiento de jugadores cuadro por cuadro (posición, velocidad, aceleración, orientación) en frames previos y posteriores al pase, temporada 2023 de la NFL. Portal: https://databowlmexico.aluva.people.aws.dev/ . Los nombres exactos de columnas y archivos NO se asumen: se leen del dataset y su diccionario.
- **Qué se entrega:** (a) código fuente en .zip y **repositorio PÚBLICO en GitHub**, (b) el resultado: visualización, captura de la herramienta o demo de la métrica, (c) **README de 3 a 5 oraciones**: qué construiste, qué revela y quién lo usaría. Hora límite: confirmar con los organizadores.
- **Evaluación:** 3 rondas (filtrado -> rúbrica -> deliberación). Puntaje 1 a 5 en: **Visión de juego, Ejecución técnica, Comunicación, Originalidad** (puede haber más criterios; confirmar).
- Se publica con `setup --entregar` (hay que pasar `--check`). El README.md en la raíz se evalúa primero.

## Qué significa cada criterio para nuestras decisiones
- **Visión de juego:** el insight debe ser algo que un entrenador/scout/comentarista reconozca como útil y entendible de fútbol americano. Piensa en una decisión o una frase para la transmisión.
- **Ejecución técnica:** números correctos, con incertidumbre (IC y n), código que corre de cero. Aquí el protocolo de datos (`ds-*`) es ventaja.
- **Comunicación:** un hallazgo por vista, título que diga la conclusión, README breve y claro.
- **Originalidad:** una métrica o ángulo que no sea el obvio. Debe quedar defendible, no solo novedoso.

## Reglas de trabajo
1. MVP primero: algo que corra de punta a punta en la primera hora y media, luego se mejora.
2. Un solo insight bien respondido, para un usuario concreto > diez gráficas sin historia.
3. Todo texto de la app y README en español, claro y para jurados no técnicos.
4. Si algo se atora más de 10 minutos, simplifica en vez de depurar sin fin.
5. Nunca pongas llaves, contraseñas ni tokens en el código, README ni repo (el repo es público).
6. La IA es un PLUS (ver `agente-ia-strands`): solo después de que el MVP funcione, y la app debe seguir sirviendo sin ella.
