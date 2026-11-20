# PLAN — Lo que muestran vs. lo que juegan: Índice de disfraz defensivo

> Se llena JUNTOS en los primeros 20 min. Después solo se actualiza el "Registro" al final.
> Regla: si no cabe en una línea, no está claro todavía.

## 1. El reto en 5 líneas
- Qué piden: una herramienta, visualización o métrica nueva con datos de tracking para un entrenador, scout o comentarista de la NFL.
- Entregable esperado: herramienta/visualización O métrica nueva + .zip + repo PÚBLICO + captura/demo + README de 3-5 oraciones
- Formato elegido (marcar uno): ( ) visualización/herramienta de comparación  (X) métrica/puntuación inventada (Índice de disfraz, presentado en un tablero por equipo)
- Cómo evalúan: 3 rondas; puntaje 1-5 en Visión de juego, Ejecución técnica, Comunicación, Originalidad (+ otros que anuncien):
- Restricciones: 3 h, equipo de 2, stack fijo (FastAPI + React/Vite/Tailwind 3/Recharts), datos de solo lectura en `data/` (825 MB).
- Fecha/hora límite de entrega: respaldo **12:00** · final **12:50**

**Tipo de reto:** ( ) ejercicios concretos  ( ) análisis + visualización  (X) app/herramienta (confirmado por el portal)  ( ) modelo predictivo
_Si es "ejercicios": no se construye frontend; ver sección 9._

## 1b. Usuario y valor (obligatorio, es la "Visión de juego")
- Usuario concreto: **coordinador ofensivo** que prepara el partido contra un rival.
- Frase que le damos: "Esta defensa muestra blitz y no lo manda en X% de sus jugadas de pase (liga: Y%), y esconde el blitz en Z% (liga: W%)."
- Qué lo hace original: compara lo que la defensa **muestra al snap** (posiciones del tracking) con lo que **juega** (rol y cobertura de PFF), jugador por jugador.
- Plus de IA (decidir a las 11:15): ( ) sí (X) no por ahora. Solo se agregaría después de la entrega de respaldo.

## 2. Pregunta central (UNA, medible)
> ¿Qué defensas de la NFL muestran al snap algo distinto de lo que juegan, y en qué porcentaje de sus jugadas de pase, comparado con el promedio de la liga?

- Decisión que apoya: el coordinador ofensivo elige protección y lectura del QB según el tipo de disfraz habitual del rival.
- Métrica de resultado: % de jugadas de pase con disfraz por equipo defensivo (0-100 %, con IC 95 %), en dos componentes:
  1. **Frente**, con dos métricas principales que son las dos caras del disfraz:
     - **"Muestra blitz y no lo manda"** = 5 o más defensores en la línea al snap y 4 o menos atacan al QB (`pff_role = Pass Rush`). Liga: 1,653 jugadas [CALCULADO].
     - **"Blitz escondido"** = 4 o menos en la línea al snap y 5 o más atacan. Liga: 751 jugadas [CALCULADO].
  2. **Cáscara: "muestra 2 safeties profundos y rota"** = entre jugadas con 2 safeties profundos al snap, % que juegan Cover-3 o Cover-1.
- Comparación: cada equipo defensivo (32) contra el resto de la liga, dentro de estratos down × yardas por ganar × formación ofensiva.
- Población: jugadas de pase de la temporada 2021, semanas 1-8, con snap, sin conversiones de 2 puntos. La cáscara excluye sacks y scrambles porque no tienen frame de pase. **NO aplica a:** carreras, otras temporadas ni a si el disfraz funciona.

## 3. Datos (se llena tras `audit_dataframe`, no antes)
Detalle completo en `docs/datos.md`.

| Archivo | Filas | Llave única | Unidad de análisis | ¿Filas dependientes? (agrupadas por...) |
|---|---|---|---|---|
| `games.csv` | 122 | `gameId` | partido | por semana |
| `plays.csv` | 8,557 | (`gameId`, `playId`) | jugada de pase | por partido y equipo |
| `pffScoutingData.csv` | 188,254 | (`gameId`, `playId`, `nflId`) | jugador en jugada (22 por jugada) | por jugada, partido y equipo |
| `players.csv` | 1,679 | `nflId` | jugador | — |
| `tracking/*.csv` (122) | 8,314,178 | (`gameId`, `playId`, `nflId`, `frameId`) | jugador en frame (22 + balón) | por jugador, jugada y partido |

- Diccionario de datos encontrado: **no** (pendiente en el portal del evento).
- Columnas clave [OBSERVADO]: `x`, `y` en yardas [SUPUESTO]; `x` NO está orientada (la ofensiva ataca hacia +x si `playDirection == "right"`, verificado); `frameId` a 10 fps [SUPUESTO]; `event` (`ball_snap`, `pass_forward` y sus `autoevent_*`); `pff_role`, `pff_positionLinedUp`, `pff_passCoverage`, `pff_passCoverageType`.
- Problemas de calidad: temporada 2021, no 2023; ventana de solo 5 frames antes del snap; 953 jugadas sin evento de pase (casi todas sacks y scrambles); eventos de snap y pase duplicados. Ver `docs/datos.md`.
- Filtros aplicados y filas que quitan:
  - conversiones de 2 puntos: −35 jugadas (8,557 → 8,522);
  - sin snap o sin defensores medidos: frente con 8,498 jugadas;
  - cáscara: con snap, pase y safeties en ambos frames: 7,167 jugadas.

## 4. Análisis declarados DE ANTEMANO (anti p-hacking)
Lista de comparaciones/modelos que se van a hacer. Todo lo que se pruebe después se anota en el Registro como exploratorio.
1. **Frente por equipo:** % "muestra blitz y no lo manda" y % "blitz escondido" para cada uno de los 32 equipos contra la liga (Vista 1, con selector entre las dos métricas).
2. **Cáscara por equipo:** % de rotación (2 profundos al snap → Cover-3 o Cover-1) para cada equipo contra la liga (Vista 2).
3. **Frente por situación** para el equipo elegido: misma métrica por down × yardas por ganar contra la liga en la misma situación (Vista 3).
4. **Sensibilidad** de los umbrales [SUPUESTO]: "en la línea" con U = 2 o 3 yd de profundidad y L = 6, 8 o 10 yd a lo ancho; safety profundo a 8, 10 o 12 yd. Se reporta si cambia el ranking.
5. **Refutación:** estabilidad del ranking entre semanas 1-4 y semanas 5-8.

- Método de incertidumbre: Wilson por equipo; `cluster_bootstrap_ci` por partido para tasas de equipo; `stratified_comparison` (equipo = 1 vs resto = 0) con estratos down × yardas por ganar × formación para la diferencia ajustada; `shrink_rates` para ordenar el ranking.
- Validación: n/a (análisis descriptivo, no predictivo). Robustez con los puntos 4 y 5.
- Corrección por pruebas múltiples necesaria: **sí**, `benjamini_hochberg` sobre las 32 comparaciones de cada métrica (3 métricas: muestra y no manda, blitz escondido, rotación de cáscara).
- Línea base: el promedio de la liga en la misma situación.

## 5. Alcance MVP (máx. 3 vistas) y fuera de alcance
**Entra:**
1. Vista 1. Título-hallazgo: "<Equipo> muestra blitz y no lo manda en X% de sus pases (liga Y%)": ranking de los 32 equipos con IC y la línea de la liga. Selector: "muestra y no manda" / "blitz escondido".
2. Vista 2: perfil del equipo elegido con sus 3 métricas (muestra y no manda, blitz escondido, rotación de cáscara) contra la liga, con IC y n.
3. Vista 3: las dos métricas del frente para el equipo elegido por situación (down × yardas por ganar) contra la liga.

**NO entra (aunque tentador):**
- Componente de corners (press contra Man/Zone): Man/Zone es una etiqueta de la jugada, no de cada corner. Solo si sobra tiempo, y como exploratorio.
- Blitz de safety: 9 casos en total.
- Movimiento antes del snap: solo hay 5 frames previos.
- Decir si el disfraz "funciona" o engaña al QB, porque eso es causal.
- Chat con IA antes de la entrega de respaldo.

## 6. Reparto (ver `docs/api.md` para el contrato)
| Persona | Dueño de | Agentes | Entrega a la otra persona |
|---|---|---|---|
| A: **Hugo** (números) | `backend/`, `docs/`, `tools/` | experto-datos, auditor-calidad, estadistico-rigor, escepticista-revisor | endpoints reales según `docs/api.md` + CSV de agregados precalculados |
| B: **Fernando** (jurado) | `dashboard/`, `README.md` | frontend-dashboard, narrador-visual, revisor-entrega | dashboard + README |

- Quién corre `--entregar`: **Hugo** (una sola persona)
- Quién sube el repo PÚBLICO y verifica que no hay secretos: **Hugo**
- Canal de comunicación: en persona

## 7. Hitos (ajusta las horas al evento)
Horarios del evento: construcción 11:00-12:00, cierre 12:00-13:00. Respaldo a las **12:00**.

| Hora | Hito | Responsable | Hecho |
|---|---|---|---|
| 10:00-11:00 | Dataset, auditoría (`docs/datos.md`), enfoque elegido | Hugo | [x] |
| 11:15 | PLAN.md y docs/api.md acordados | ambos | [ ] |
| 11:15-11:40 | Hugo: script de agregados + API real · Fernando: dashboard con mocks | Hugo · Fernando | [ ] |
| 11:40 | Integración API real + dashboard | ambos | [ ] |
| **12:00** | **ENTREGA DE RESPALDO** (`--check` + `--entregar`) + push a GitHub | Hugo | [ ] |
| 12:00-12:25 | Hugo: sensibilidad + `escepticista-revisor` · Fernando: README con cifras reales + captura | Hugo · Fernando | [ ] |
| 12:25 | Congelar features; solo arreglar y documentar | ambos | [ ] |
| 12:35 | `revisor-entrega` + guion de demo | ambos | [ ] |
| **12:50** | **ENTREGA FINAL** (`--check` + `--entregar` + push) | Hugo | [ ] |

## 8. Riesgos y plan de recorte
| Si pasa esto... | ...recortamos esto |
|---|---|
| El script de agregados tarda o falla | Entregar solo el frente (Vista 1 + Vista 2 sin cáscara) |
| Integración se atrasa | Entregar con 1 vista funcional + README honesto |
| El ranking cambia mucho con los umbrales | Mostrarlo como resultado: "depende de la definición", con las dos versiones |
| Resultado no concluyente (IC se traslapan con la liga) | Reportarlo con IC y límites: "no se puede concluir" también es resultado |
| `--check` falla cerca del final | Prioridad #1: arreglar versiones/estructura antes que features |

## 9. Si el reto es de ejercicios
No aplica.

## 10. Definición de "terminado"
- [ ] `--check` pasa sin errores
- [ ] La app arranca desde cero siguiendo el README
- [ ] Cada número del README sale de código ejecutado (ruta del script)
- [ ] Conclusión revisada por `escepticista-revisor` (veredicto: ____)
- [ ] Limitaciones y supuestos escritos
- [ ] `--entregar` corrido y publicación verificada

## Registro (se va llenando durante el evento)
**Supuestos** (cada uno: qué, por qué, qué cambia si es falso)
- [SUPUESTO] "En la línea" = 2 yd o menos de profundidad y 8 yd o menos a lo ancho del balón al snap. Por qué: separa a la línea defensiva (mediana 0.95 yd) de los LB en cobertura (mediana 4.29 yd). Si es falso: cambian los conteos (con U = 3 yd, los LB en la línea que caen pasan de 2,878 a 4,151). Se reporta la sensibilidad.
- [SUPUESTO] Safety profundo = 10 yd o más del balón. Si es falso, cambia la clasificación de la cáscara. Se prueban 8 y 12 yd.
- [SUPUESTO] Las etiquetas PFF (`pff_role`, `pff_passCoverage`) son la verdad de referencia de "lo que se juega". Si fueran ruidosas, el disfraz medido incluye error de anotación.
- [SUPUESTO] Cover-3 y Cover-1 son coberturas de un solo safety profundo. Confirmar con el diccionario.
- [SUPUESTO] 10 frames por segundo (media de `time` entre frames: 0.0999 s).

**Decisiones**
| Hora | Decisión | Quién |
|---|---|---|
| ~11:10 | Pregunta: Índice de disfraz defensivo (frente + cáscara); corners fuera del MVP | Hugo · Fernando |
| ~11:10 | Formato: métrica nueva; usuario: coordinador ofensivo | Hugo · Fernando |
| ~11:10 | Hugo corre `--entregar` y sube el repo | Hugo · Fernando |
| ~11:15 | Frente con 2 métricas principales: "muestra y no manda" y "blitz escondido"; sin IA por ahora; final 12:50 | Hugo · Fernando |

**Análisis exploratorios hechos fuera de la lista declarada (sección 4)**
- Viabilidad de presión, separación y rotación (`tools/opciones_viables.py`): solo conteos, sin comparar grupos.
- Viabilidad del frente y los corners (`tools/disfraz_viabilidad.py`): solo conteos, sin comparar grupos.
