# Auditoría de datos (`data/`)

Código: `tools/auditoria_datos.py` (auditoría completa con `audit_dataframe`) y `tools/auditoria_extra.py` (verificaciones de seguimiento). Salidas crudas: `docs/auditoria_salida.txt` y `docs/auditoria_extra_salida.txt`. No se modificó ningún archivo de `data/`.

Etiquetas: **[OBSERVADO]** salió de código ejecutado, **[CALCULADO]** resultado de una cuenta sobre los datos, **[SUPUESTO]** hipótesis declarada, **[NO SÉ]** no se puede afirmar con lo que hay.

**Diccionario de datos:** [OBSERVADO] no existe en el repo (`data/` solo tiene CSV; no hay ningún `.md` con definiciones). Todo significado de columna marcado [NO SÉ] se confirma en el portal del evento: https://databowlmexico.aluva.people.aws.dev/

## 1. Hallazgos ordenados por impacto

| # | Impacto | Hallazgo | Evidencia | Qué hacer (pendiente de aprobación) |
|---|---|---|---|---|
| 1 | CRÍTICO | Los datos son de la temporada **2021, semanas 1 a 8**, no 2023 | [OBSERVADO] `season` tiene 1 valor (2021) en las 122 filas de `games.csv`; `gameDate` va de 2021-09-09 a 2021-11-01 | Confirmar con organizadores. En README y app decir "2021, semanas 1-8". Las conclusiones no aplican a otras temporadas. |
| 2 | CRÍTICO | La ventana de tracking es corta: ~5 frames antes del snap y 5 después del pase | [CALCULADO] sobre jugadas con snap: frames antes del snap, mediana 5, p5 5, p95 5 (máx. 117). Frames después del pase: mediana 5, máx. 5 (n=7,604). | No se puede estudiar movimiento previo al snap (shifts, rotaciones de safeties). Solo se estudia snap -> pase. |
| 3 | CRÍTICO | Solo hay jugadas de pase (dropbacks). No hay jugadas de carrera | [OBSERVADO] `passResult` sin nulos en 8,557 jugadas; valores C 4,620, I 2,755, S 543, R 449, IN 190 | Toda conclusión se limita a jugadas de pase. Significado exacto de `R` [NO SÉ] (diccionario). |
| 4 | CRÍTICO | Faltan eventos de pase en 953 jugadas, casi todas sacks y scrambles | [CALCULADO] jugadas sin `pass_forward` ni `autoevent_passforward`: 953 de 8,557. Por `passResult`: S 513 (de 543), R 437 (de 449), C 2, I 1. | Si la métrica usa "frame del pase", sacks y scrambles quedan fuera y se sesga hacia jugadas donde el QB sí lanzó. Declararlo o usar otro frame final (p. ej. último frame). |
| 5 | IMPORTANTE | `time` no sirve para ordenar frames. Resolución de 1 segundo | [OBSERVADO] 0 valores con fracción de segundo; en 0 de 8,557 jugadas el nº de segundos distintos iguala al de frames; 7,306,289 de 8,117,367 diferencias consecutivas = 0 s. Mediana frames/segundos distintos = 8.2. | Usar `frameId`. Si se necesita tiempo real: [SUPUESTO] 10 frames/s, apoyado en que la diferencia media de `time` entre frames es 0.0999 s [CALCULADO]. Confirmar en diccionario. |
| 6 | IMPORTANTE | Coordenadas sin normalizar por sentido de juego (VERIFICADO) | [OBSERVADO] `playDirection`: left 4,287,706 filas, right 4,026,472. [CALCULADO] con signo = +1 si `right`, -1 si `left`: profundidad defensiva al snap > 0 en todas salvo 4 de 93,478 filas defensor-jugada; entre snap y pase los rushers avanzan (mediana DL -5.30 yd) y la cobertura retrocede (mediana CB +4.84 yd). Ver `tools/disfraz_viabilidad.py`. | `x` NO está orientada: la ofensiva ataca hacia +x cuando `playDirection == "right"`. Multiplicar por ese signo para profundidad o avance. Para distancias entre jugadores no hace falta. |
| 7 | IMPORTANTE | Etiquetas de evento duplicadas y no mutuamente excluyentes | [OBSERVADO] 27 valores de `event`. [CALCULADO] 3,756 jugadas tienen a la vez `ball_snap` y `autoevent_ballsnap`; 24 jugadas no tienen ningún snap; 57 jugadas solo tienen `autoevent_passforward`. | Definir una regla única: snap = `ball_snap` si existe, si no `autoevent_ballsnap`. Misma regla para pase. Documentar cuántas jugadas cambian de frame. Qué significa `autoevent_*` [NO SÉ]. |
| 8 | IMPORTANTE | 35 intentos de conversión de 2 puntos mezclados con jugadas normales | [OBSERVADO] `down == 0` y `yardsToGo == 0` en 35 filas; `playDescription` de las 4 primeras: "TWO-POINT CONVERSION ATTEMPT" | Excluir o marcar (35 de 8,557 = 0.4%). |
| 9 | IMPORTANTE | `dropBackType` nulo (528, 6.2%) y relacionado con el resultado | [CALCULADO] con `dropBackType` nulo: C 29.5%, I 57.6%; con valor: C 55.6%, I 30.5% | No imputar con la moda ni borrar sin avisar. Si se usa `dropBackType`, reportar con "sin dato" como categoría. Motivo del nulo [NO SÉ]. |
| 10 | IMPORTANTE | Faltas incompletas: `playResult` difiere de `prePenaltyPlayResult` sin dato de falta | [CALCULADO] 31 jugadas con `penaltyYards` nulo, `foulName1` nulo y `playResult != prePenaltyPlayResult` (C 16, S 11, R 4). 20 jugadas con `penaltyYards` y sin `foulName1`. | Para métricas de yardas usar la columna elegida de forma consistente y decir cuál. Significado de ambas columnas [NO SÉ]. |
| 11 | IMPORTANTE | 969 filas de jugadores fuera del rectángulo [0,120] x [0,53.3] | [CALCULADO] 112 por `x`, el resto por `y`; 85 jugadas distintas. El balón tiene 204 filas fuera en `y`. | [SUPUESTO] son jugadores que salen de la cancha o ruido de medición, no errores de captura. No borrar. Revisar en caso de usar distancia a la banda. |
| 12 | IMPORTANTE | Balón con valores extremos distintos a los jugadores | [CALCULADO] `s` máx. balón 29.34 vs jugadores 11.18; `s>14`: 29,654 filas, todas balón; `a` máx. 50.69 (balón); `dis>1.5`: 31,184 balón y 27 jugadores | Analizar balón y jugadores por separado. No usar `s`, `a` del balón sin filtrar. |
| 13 | IMPORTANTE | Nulos estructurales en el balón | [OBSERVADO] `nflId`, `jerseyNumber`, `o`, `dir` nulos en 361,486 filas, todas con `team == "football"` (4.35% del total). Ningún jugador tiene nulos en ninguna columna. | No imputar. Filtrar `team != "football"` antes de agrupar por `nflId`. |
| 14 | IMPORTANTE | `playId` no identifica jugada por sí solo | [OBSERVADO] `playId` tiene 3,762 valores distintos en 8,557 jugadas | Siempre unir y agrupar por (`gameId`, `playId`). |
| 15 | IMPORTANTE | Cobertura parcial de semanas 6 a 8 | [OBSERVADO] partidos por semana: 16, 16, 16, 16, 16, 14, 13, 15 | [NO SÉ] si faltan por descansos (bye) o por recorte del dataset. No se comparan semanas sin decirlo. |
| 16 | MENOR | Nulos de PFF son estructurales, no errores | [CALCULADO] `pff_hit/hurry/sack` tienen valor en 94,127 filas = Coverage 57,765 + Pass Rush 36,362; las columnas `*Allowed` en 48,087 = Pass Block 46,057 + Pass Route 2,030 | No tratar como faltantes. No poner 0. |
| 17 | MENOR | `players.csv`: nulos y formatos mezclados | [OBSERVADO] `birthDate` nulo 232 (13.8%); `collegeName` nulo 224 (13.3%); 14 `birthDate` con formato `mm/dd/yyyy` (ej. `05/15/1986`) y el resto `yyyy-mm-dd` | No se usa edad ni universidad en el MVP. Si se usara, normalizar formato. |
| 18 | MENOR | `displayName` repetido para jugadores distintos | [OBSERVADO] 8 nombres repetidos (16 `nflId`), ej. "Josh Allen" QB y OLB | Unir siempre por `nflId`, nunca por nombre. Mostrar nombre + posición. |
| 19 | MENOR | Pocos valores nulos aislados en `plays.csv` | [OBSERVADO] `offenseFormation` 7, `defendersInBox` 7, `personnelO` 1, `personnelD` 1, `absoluteYardlineNumber` 1. `yardlineSide` nulo en 125, todas con `yardlineNumber == 50` | Descartar esas pocas filas solo en análisis que usen la columna; reportar n. |
| 20 | MENOR | Columnas casi vacías | [OBSERVADO] `foulName3` y `foulNFLId3` constantes (1 valor no nulo); `foulName2` 99.65% nulo | No usar. |
| 21 | MENOR | Aceleración atípica en 10 filas de jugadores | [CALCULADO] `a` máx. de jugadores 21.92; 10 filas con `abs(a) > 15`. `dis > 1.2` en 68 filas | Valor legítimo o glitch [NO SÉ]. No afecta promedios con n = 8.3 millones; sí un máximo. Usar cuantiles, no máximos. |

## 2. Inventario de archivos

| Archivo | Filas | Columnas | Llave única | Duplicados en llave | Duplicados exactos |
|---|---|---|---|---|---|
| `games.csv` | 122 | 7 | `gameId` | 0 | 0 |
| `players.csv` | 1,679 | 7 | `nflId` | 0 | 0 |
| `plays.csv` | 8,557 | 32 | (`gameId`, `playId`) | 0 | 0 |
| `pffScoutingData.csv` | 188,254 | 15 | (`gameId`, `playId`, `nflId`) | 0 | 0 |
| `tracking/tracking_<gameId>.csv` (122 archivos, 825 MB en total `data/`) | 8,314,178 | 16 | (`gameId`, `playId`, `nflId`, `frameId`) | 0 | 0 |

[OBSERVADO] Los 122 archivos de tracking tienen el mismo encabezado y el `gameId` interno coincide con el del nombre del archivo.
[OBSERVADO] En tracking, la llave incluye `nflId` nulo (balón). Con `nflId` nulo hay una fila por frame, y la llave sigue sin duplicados.

## 3. Columnas, tipos y nulos

Tipos tal como los lee pandas con los dtypes indicados en el script (tracking) o por defecto (resto). "Rol" es lo que [OBSERVADO] hace la columna en los datos. El significado de negocio no está confirmado salvo donde lo dice la tabla.

### `games.csv` (122 filas)
| Columna | dtype | Nulos | Únicos | Rol | Notas |
|---|---|---|---|---|---|
| `gameId` | int64 | 0 | 122 | **ID de partido** | llave |
| `season` | int64 | 0 | 1 | constante | 2021 |
| `week` | int64 | 0 | 8 | periodo | 1 a 8 |
| `gameDate` | object | 0 | 24 | fecha texto `mm/dd/yyyy` | parseable en 122 de 122 |
| `gameTimeEastern` | object | 0 | 6 | hora texto | |
| `homeTeamAbbr`, `visitorTeamAbbr` | object | 0 | 32, 32 | **equipo** | 32 equipos en total |

### `players.csv` (1,679 filas)
| Columna | dtype | Nulos | Únicos | Rol | Notas |
|---|---|---|---|---|---|
| `nflId` | int64 | 0 | 1,679 | **ID de jugador** | llave |
| `height` | object | 0 | 16 | texto `pies-pulgadas` | 66 a 81 pulgadas [CALCULADO]; ninguna con pulgadas > 11 |
| `weight` | int64 | 0 | 176 | numérica | 158 a 380; unidad [NO SÉ] (libras [SUPUESTO] por la escala) |
| `birthDate` | object | 232 (13.8%) | 1,174 | fecha texto | 2 formatos (ver hallazgo 17) |
| `collegeName` | object | 224 (13.3%) | 236 | categoría | |
| `officialPosition` | object | 0 | 19 | **posición** | QB, WR, CB, etc. `LB` (2) y `DB` (2) son genéricos |
| `displayName` | object | 0 | 1,671 | nombre | no único (hallazgo 18) |

### `plays.csv` (8,557 filas, 122 partidos)
| Columna | dtype | Nulos | Únicos | Rol | Notas |
|---|---|---|---|---|---|
| `gameId`, `playId` | int64 | 0 | 122; 3,762 | **ID de partido / jugada** | `playId` solo único dentro del partido |
| `playDescription` | object | 0 | 8,555 | texto libre | |
| `quarter` | int64 | 0 | 5 | periodo | 1 a 5 (5 = tiempo extra [SUPUESTO], 98 jugadas) |
| `down` | int64 | 0 | 5 | numérica | 0 a 4; 0 = conversión de 2 puntos (35) |
| `yardsToGo` | int64 | 0 | 32 | numérica | 0 a 39 |
| `possessionTeam`, `defensiveTeam` | object | 0 | 32, 32 | **equipo** | nunca iguales entre sí |
| `yardlineSide` | object | 125 | 32 | equipo/lado del campo | nulo si `yardlineNumber == 50` |
| `yardlineNumber` | int64 | 0 | 50 | numérica | 1 a 50 |
| `gameClock` | object | 0 | 898 | texto | |
| `preSnapHomeScore`, `preSnapVisitorScore` | int64 | 0 | 42, 38 | numérica | |
| `passResult` | object | 0 | 5 | categoría | C, I, S, R, IN |
| `penaltyYards` | float64 | 7,801 (91.2%) | 60 | numérica | -18 a 50 |
| `prePenaltyPlayResult`, `playResult` | int64 | 0 | 98; 102 | numérica | -34 a 91 en `playResult` |
| `foulName1/2/3`, `foulNFLId1/2/3` | object / float64 | 91.4% / 99.65% / 99.99% | 29 / 15 / 1 | falta y jugador | |
| `absoluteYardlineNumber` | float64 | 1 | 99 | numérica | 11 a 109 |
| `offenseFormation` | object | 7 | 7 | categoría | SHOTGUN 5,481; EMPTY 1,396; SINGLEBACK 1,189 ... |
| `personnelO`, `personnelD` | object | 1, 1 | 30; 29 | categoría | texto "4 DL, 2 LB, 5 DB" |
| `defendersInBox` | float64 | 7 | 11 | numérica | 1 a 11 |
| `dropBackType` | object | 528 (6.2%) | 8 | categoría | TRADITIONAL 6,542; SCRAMBLE 899 ... |
| `pff_playAction` | int64 | 0 | 2 | binaria 0/1 | 1 en 2,038 |
| `pff_passCoverage` | object | 0 | 12 | categoría | Cover-3 2,665; Cover-1 2,011; Cover-2 1,085 ... |
| `pff_passCoverageType` | object | 0 | 3 | categoría | Zone 5,588; Man 2,481; Other 488 |

### `pffScoutingData.csv` (188,254 filas; 22 filas por jugada en las 8,557 jugadas)
| Columna | dtype | Nulos | Rol | Notas |
|---|---|---|---|---|
| `gameId`, `playId`, `nflId` | int64 | 0 | **IDs** | 1,679 `nflId` |
| `pff_role` | object | 0 | categoría (5) | Coverage 57,765; Pass Block 46,057; Pass Route 39,513; Pass Rush 36,362; Pass 8,557 |
| `pff_positionLinedUp` | object | 0 | categoría (56) | QB 8,557 (igual que `Pass`); [SUPUESTO] `Pass` es el QB |
| `pff_hit`, `pff_hurry`, `pff_sack` | float64 | 94,127 (50%) | binaria 0/1 | solo con valor en Coverage y Pass Rush. Tasas [CALCULADO]: hit 0.9%, hurry 3.1%, sack 0.6% (sobre filas no nulas; ojo, el denominador mezcla coverage y rush) |
| `pff_beatenByDefender`, `pff_hitAllowed`, `pff_hurryAllowed`, `pff_sackAllowed` | float64 | 140,167 (74.5%) | binaria 0/1 | solo en Pass Block y Pass Route |
| `pff_nflIdBlockedPlayer` | float64 | 141,728 (75.3%) | **ID de jugador** | 665 únicos |
| `pff_blockType` | object | 140,350 (74.6%) | categoría (12) | PP 24,697; PA 6,331; PT 5,906 ... |
| `pff_backFieldBlock` | float64 | 140,351 (74.6%) | binaria 0/1 | |

### `tracking_*.csv` (8,314,178 filas, 8,557 jugadas, 23 filas por frame: 22 jugadores + balón)
| Columna | dtype (script) | Nulos | Únicos | Rango observado | Rol |
|---|---|---|---|---|---|
| `gameId`, `playId` | int32 | 0 | 122; 3,762 | | **IDs** |
| `nflId` | Int32 | 361,486 (4.35%) | 1,679 | | **ID de jugador**; nulo = balón |
| `frameId` | int16 | 0 | 203 | 1 a 203; empieza en 1 en las 8,557 jugadas; sin huecos | orden temporal |
| `time` | datetime (UTC) | 0 | 40,621 | resolución de 1 s | marca de tiempo |
| `jerseyNumber` | Int16 | 361,486 | 99 | 1 a 99 | número de camiseta |
| `team` | category | 0 | 33 | 32 equipos + `football` | **equipo** (y balón) |
| `playDirection` | category | 0 | 2 | left / right | sentido de la jugada |
| `x` | float32 | 0 | | -3.55 a 121.15 | posición [SUPUESTO] yardas, eje largo |
| `y` | float32 | 0 | | -4.53 a 57.72 | posición [SUPUESTO] yardas, eje corto |
| `s` | float32 | 0 | | 0 a 29.34 (jugadores 0 a 11.18) | [SUPUESTO] velocidad, yardas/s |
| `a` | float32 | 0 | | 0 a 50.69 (jugadores 0 a 21.92) | [SUPUESTO] aceleración, yardas/s² |
| `dis` | float32 | 0 | | 0 a 10.45 | [SUPUESTO] distancia desde el frame anterior, yardas. Respaldo: mediana de `dis / (0.1 * s)` = 1.001 en jugadores con `s > 1` [CALCULADO] |
| `o`, `dir` | float32 | 361,486 | 36,001 | 0 a 360 | [SUPUESTO] orientación y dirección en grados. Respaldo: ninguna fila fuera de [0, 360] |
| `event` | category | 0 | 27 | `None` en 7,673,352 filas | evento marcado en el frame |

[NO SÉ] unidades de `x`, `y`, `s`, `a`, `dis`, `o`, `dir`, sentido del ángulo y significado de `event`. Confirmar en el diccionario del portal.

## 4. Rangos físicos y lógicos

| Revisión | Resultado | Etiqueta |
|---|---|---|
| `x` fuera de [0, 120] | 112 filas, todas de jugadores | [CALCULADO] |
| `y` fuera de [0, 53.3] | 1,061 filas (857 jugadores, 204 balón) | [CALCULADO] |
| `s < 0`, `dis < 0`, `o`/`dir` fuera de [0, 360] | 0 filas | [CALCULADO] |
| `s > 14` | 29,654 filas, todas del balón | [CALCULADO] |
| `a` fuera de [-15, 15] | 1,845 filas (1,835 balón, 10 jugadores) | [CALCULADO] |
| `dis > 1.5` | 31,211 filas (31,184 balón, 27 jugadores) | [CALCULADO] |
| Velocidad máxima por equipo (jugadores) | de 9.65 (SEA, TEN) a 11.18 (HOU) | [OBSERVADO] |
| `a` (aceleración) con mínimo 0 | no hay aceleraciones negativas: `a` mínimo 0 en los 8.3 M de filas | [OBSERVADO] |
| `down` = 0 | 35 filas, todas conversiones de 2 puntos | [OBSERVADO] |
| `yardsToGo` = 0 | 35 filas, las mismas | [CALCULADO] |
| `playResult` vs `prePenaltyPlayResult` | 31 diferencias sin falta registrada | [CALCULADO] |
| `weight` | 158 a 380; por posición coherente (ej. C 270 a 330; CB 158 a 218) | [CALCULADO] |
| `defendersInBox` | 1 a 11 | [OBSERVADO] |

[OBSERVADO] `a` no tiene valores negativos. Eso sugiere que `a` es magnitud y no aceleración con signo. Confirmar en diccionario (no se debe interpretar como "frenado" sin eso).

## 5. Nulos: dónde y por qué

| Tabla | Columna(s) | Patrón | Etiqueta |
|---|---|---|---|
| tracking | `nflId`, `jerseyNumber`, `o`, `dir` | 361,486 filas = todas las filas `team == "football"`; 0 nulos en jugadores | [OBSERVADO] |
| pffScoutingData | `pff_hit`, `pff_hurry`, `pff_sack` | nulos exactamente cuando `pff_role` es Pass Block, Pass Route o Pass | [CALCULADO] 94,127 con valor = 57,765 + 36,362 |
| pffScoutingData | `*Allowed`, `pff_beatenByDefender` | nulos salvo Pass Block y Pass Route | [CALCULADO] 48,087 = 46,057 + 2,030 |
| plays | `penaltyYards`, `foulName*`, `foulNFLId*` | nulos cuando no hubo falta; 20 `penaltyYards` sin `foulName1` | [OBSERVADO] |
| plays | `yardlineSide` | nulo solo con `yardlineNumber == 50` (125 de 125) | [OBSERVADO] |
| plays | `dropBackType` | 528 nulos, resultado de la jugada distinto al resto (hallazgo 9). Motivo [NO SÉ] | [CALCULADO] |
| plays | `offenseFormation`, `defendersInBox` | 7 nulos. Por `passResult`: C 2, I 2, IN 2, R 1 | [OBSERVADO] |
| players | `birthDate`, `collegeName` | 13.8% y 13.3%; se reparten en todas las posiciones (QB 7, WR 24, CB 34...). Motivo [NO SÉ] | [OBSERVADO] |

## 6. Llaves, grupos y cruces

**Columnas que identifican grupos** [OBSERVADO]:
- Partido: `gameId` (122).
- Jugada: (`gameId`, `playId`) (8,557).
- Jugador: `nflId` (1,679). Balón = `nflId` nulo, `team == "football"`.
- Equipo: `team` en tracking (32 + football); `possessionTeam`, `defensiveTeam`, `homeTeamAbbr`, `visitorTeamAbbr` en las otras tablas.
- Rol y posición: `pff_role`, `pff_positionLinedUp` (PFF), `officialPosition` (`players.csv`).
- [CALCULADO] En las 8,557 jugadas, los 2 equipos del tracking (sin balón) coinciden exactamente con {`possessionTeam`, `defensiveTeam`}. Por tanto, ofensiva y defensa se asignan uniendo `team` con `plays.possessionTeam`.
- [OBSERVADO] Los 22 jugadores de cada jugada aparecen en tracking y en PFF (22 filas por jugada).

**Cruces verificados** [CALCULADO], con `validate=` y `indicator=True`:

| Cruce | Cardinalidad | Filas antes -> después | Sin pareja |
|---|---|---|---|
| plays -> games | many_to_one | 8,557 -> 8,557 | 0 |
| pff -> plays | many_to_one | 188,254 -> 188,254 | 0 |
| pff -> players | many_to_one | 188,254 -> 188,254 | 0 |
| tracking (jugadas) <-> plays | one_to_one (ambos sentidos) | 8,557 -> 8,557 | 0 y 0 |
| games -> tracking (partidos) | one_to_one | 122 -> 122 | 0 |
| tracking (`nflId`) -> players | many_to_one | 1,679 -> 1,679 | 0 |
| tracking (game, play, nflId) <-> pff | one_to_one (ambos sentidos) | 188,254 -> 188,254 | 0 y 0 |

Sin hallazgos en cruces. El riesgo a vigilar es unir tracking con `plays`/`pff` por `playId` sin `gameId`.

## 7. Sesgo de muestreo: qué cubre y qué no

| Cubre | No cubre |
|---|---|
| 122 partidos, semanas 1 a 8 de 2021, 32 equipos [OBSERVADO] | Semanas 9 en adelante, playoffs, otras temporadas |
| Jugadas de pase con dropback (C, I, S, R, IN) [OBSERVADO] | Jugadas de carrera, patadas, pases fuera de dropback si existen [NO SÉ] |
| De 5 frames antes del snap a 5 frames después del pase (en la mayoría de jugadas) [CALCULADO] | Movimiento previo al snap (shifts, motion largos) |
| 47 a 97 jugadas por partido (mediana 70) [CALCULADO]; 203 a 339 jugadas por equipo ofensivo [CALCULADO] | Muestras por equipo pequeñas si se cruzan con cobertura y formación |

Semanas 6, 7 y 8 tienen menos partidos (14, 13, 15) que las semanas 1 a 5 (16 cada una) [OBSERVADO]. El motivo [NO SÉ].

## 8. Lista de verificación de `ds-01`

- [x] n filas/columnas y llave única comprobadas: ver sección 2. 0 duplicados en llave en las 5 tablas.
- [~] tipos y unidades confirmados: tipos sí (sección 3). **Unidades no**: [NO SÉ] hasta ver el diccionario.
- [x] nulos analizados (cuántos, dónde, por qué): sección 5. El motivo de `dropBackType` y de `birthDate`/`collegeName` sigue [NO SÉ].
- [x] duplicados revisados: 0 filas exactas duplicadas en las 5 tablas; `displayName` repetido (hallazgo 18); eventos duplicados (hallazgo 7).
- [x] rangos físicos/lógicos validados: sección 4.
- [x] cardinalidad de joins verificada: sección 6.
- [x] datos originales preservados: ningún script escribe en `data/`. Pasos de limpieza propuestos con conteos en la tabla de hallazgos; ninguno aplicado.

## 9. Impacto en la idea recomendada ("Tiempo hasta la presión")

- Viable: snap -> pase en ~7,600 jugadas con ambos eventos (hallazgo 4) y posiciones de los 22 jugadores.
- Hay que decidir qué hacer con sacks y scrambles, que casi no tienen evento de pase (hallazgo 4).
- No viable: cualquier idea que necesite movimiento previo al snap (hallazgo 2). La idea 3 de la respuesta anterior ("Mapa de reacción defensiva") queda descartada con esta evidencia.
- Para distinguir rushers y bloqueadores existe `pff_role` (Pass Rush, Pass Block) en las 8,557 jugadas, con 22 filas por jugada [OBSERVADO].

## 10. Pasos de limpieza propuestos (esperan aprobación)

| Paso | Filas afectadas | Motivo |
|---|---|---|
| Excluir conversiones de 2 puntos (`down == 0`) | 35 de 8,557 jugadas | no son jugadas comparables |
| Separar balón de jugadores (`team == "football"`) | 361,486 de 8,314,178 filas | nulos estructurales y extremos propios |
| Regla única de snap y pase (`ball_snap` > `autoevent_ballsnap`; `pass_forward` > `autoevent_passforward`) | 24 jugadas sin snap; 953 sin pase | hallazgos 4 y 7 |
| Marcar (no borrar) filas fuera de cancha | 969 filas de jugadores en 85 jugadas | hallazgo 11 |
| Unir siempre por (`gameId`, `playId`) y `nflId` | 0 filas | hallazgos 14 y 18 |
