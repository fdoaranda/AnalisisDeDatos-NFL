# GUÍA FINAL (Kit v4) · Hackathon NFL Big Data Bowl UNAM · 20 nov 2026

Equipo de 2. Evento 10:00–13:00.
**El reto (Side Quest):** crear una herramienta o visualización para un **entrenador, scout o comentarista NFL** (o inventar una **métrica** nueva), con tracking cuadro por cuadro antes/después del pase, temporada 2023. Insights para coachear, hacer scouting o televisar.
**Se entrega:** .zip + **repo PÚBLICO de GitHub** + resultado (captura/demo) + **README de 3–5 oraciones** (qué construiste, qué revela, quién lo usaría).
**Se evalúa (1–5):** Visión de juego · Ejecución técnica · Comunicación · Originalidad. Hora límite: **preguntarla a los organizadores**.
**A = Números** (`backend/`, `data/`, `docs/`) · **B = Jurado** (`dashboard/`, `README.md`, y corre `--entregar`).

Cómo usar esta guía: sigue los pasos en orden. Donde diga **PROMPT**, elige el agente indicado en el selector de Kiro, pega el texto y reemplaza lo que va entre `<...>`.

Regla para TODO prompt de números: pídele siempre **n, intervalo de confianza y cómo lo calculó**. Si el agente no corrió código, no es resultado.

---

## PASO 0 · Antes de las 10:00 (los dos, 10 min)

1. Copiar el **Kit v4** (`.kiro/`, `tools/`, `docs/`, `PLAN.md`, `PROMPTS.md`) a la carpeta del proyecto, reemplazando lo anterior. Reabrir la carpeta en Kiro.
2. Abrir la carpeta en Kiro y **confiar en ella** (quitar Restricted Mode).
3. Verificar que aparecen los agentes en el selector.
4. Terminal (`Ctrl+ñ`): `.venv\Scripts\python tools/test_retos.py` → debe pasar todo.
5. Activar licencia Kiro (portal, paso 4). Bajar dataset (paso 5).
6. Acordar quién es A y quién es B.
7. `.hackathon\setup.cmd --check` (en la raíz del proyecto) para confirmar versiones.

_Si ya empezó el evento, haz el paso 0 en paralelo con el paso 1: no esperes a terminarlo._

---

## PASO 1 · 10:00–10:20 · Entender el reto y los datos

### B · agente `lider-reto`
**PROMPT:**
```
Reto: crear una herramienta o visualización (o una métrica nueva) para un entrenador, scout o comentarista de la NFL. Datos: tracking cuadro por cuadro (posición, velocidad, aceleración, orientación) antes y después del pase, temporada 2023. Se entrega .zip + repo público + captura/demo + README de 3 a 5 oraciones. Rúbrica 1-5: Visión de juego, Ejecución técnica, Comunicación, Originalidad. Somos 2, con 3 horas.
Dame 3 ideas. Cada una con: usuario concreto (entrenador, scout o comentarista), la pregunta o frase que le resuelve, formato (visualización o métrica), qué la hace original, columnas necesarias (solo si existen; si no las he visto, márcalas [NO SÉ]) y riesgo estadístico. Ordénalas por viabilidad en 3 horas y recomienda UNA.
```
Piensen en esto: ¿qué diría un comentarista en la transmisión, o qué decisión tomaría un entrenador, con su hallazgo? Si no hay una frase clara, la idea no está lista.

### A · agente `auditor-calidad`
Antes, mueve el dataset a `data/` (no lo edites; trabaja sobre copias).
**PROMPT:**
```
Audita los datos de data/<ARCHIVO>. Usa tools/stats_toolkit.py (audit_dataframe) corriendo código real con .venv\Scripts\python.
Dime: filas y columnas, tipo de cada columna, nulos por columna, duplicados, rangos raros o imposibles, cómo se identifica una fila (llave), y qué columnas parecen identificar grupos (equipo, jugador, partido…).
Etiqueta cada afirmación como [OBSERVADO] o [CALCULADO]. No supongas el significado de ninguna columna: si no lo sabes, ponlo como [NO SÉ] y dime dónde confirmarlo (diccionario de datos).
Escribe los hallazgos en docs/datos.md.
```

---

## PASO 2 · 10:20–10:40 · Elegir el análisis

### A · agente `experto-datos`
**PROMPT:**
```
Pregunta candidata: "<UNA DE LAS PREGUNTAS DE lider-reto>".
Lee docs/datos.md. Reformula la pregunta de forma medible y dime:
1) qué variable es el resultado y cuál es la comparación (A vs B),
2) cuántas observaciones hay por grupo (calcúlalo, no estimes),
3) qué factores podrían confundir la comparación y cómo los controlaríamos (stratified_comparison),
4) qué análisis haríamos y qué intervalo de confianza usaríamos,
5) qué NO podríamos concluir con estos datos.
Si la muestra de algún grupo es muy chica, dilo con el número exacto. No des conclusiones todavía.
```

### B · agente `frontend-dashboard`
**PROMPT:**
```
Revisa la carpeta dashboard/ de la plantilla (React 18, Vite, TypeScript, Tailwind 3, Recharts). Prepara un esqueleto con máximo 3 vistas para responder: "<PREGUNTA>".
Usa datos de mentira (mocks) con la bandera VITE_USE_MOCKS. No instales librerías fuera del stack fijado. Textos en español. Dime qué archivos creaste.
```

---

## PASO 3 · 10:40–10:45 · Contrato (LOS DOS JUNTOS, límite 10:45)

Sentados juntos, decidan la pregunta central y llenen `PLAN.md` y `docs/api.md`.

### A · agente `backend-fastapi`
**PROMPT:**
```
Con base en PLAN.md, completa docs/api.md: lista de endpoints (/health, /api/meta, /api/resumen, /api/serie, /api/comparacion, /api/detalle según haga falta), parámetros, y el JSON exacto de respuesta con tipos TypeScript.
Toda cifra estadística debe usar la forma {estimado, ic_inf, ic_sup, n, metodo, nota}. Define el formato de error.
Hazlo mínimo: solo lo que el dashboard necesita para responder la pregunta.
```
B revisa el resultado y confirma que su dashboard puede pintar todo con ese JSON. **Si no hay acuerdo, decide A.** Desde aquí, el contrato no cambia sin avisar en voz alta.

---

## PASO 4 · 10:45–11:50 · Construir en paralelo

### A · backend
**PROMPT 1 (agente `backend-fastapi`):**
```
Implementa en backend/ los endpoints de docs/api.md con FastAPI y pydantic v2 (versiones del stack, no cambies requirements). Carga los datos de data/ una vez al arrancar. Empieza por /health y /api/resumen y dime cómo probarlos con curl o el navegador.
```
**PROMPT 2 (agente `experto-datos`), para cada cifra:**
```
Calcula <MÉTRICA> para <GRUPO A> vs <GRUPO B> usando <COLUMNAS>. Usa stratified_comparison y bootstrap_ci (o cluster_bootstrap_ci si las filas se agrupan por <JUGADOR/PARTIDO>).
Dame: estimado, IC 95%, n por grupo, método, y una frase de qué NO se puede concluir. Corre el código y muéstrame el resultado; no me des números de memoria.
Luego deja la función lista para que backend/ la use.
```
**PROMPT 3 (si hay una relación x–y), `experto-datos`:**
```
Antes de interpretar la relación entre <X> y <Y>, corre diagnose_relationship y dime las alertas (curvatura, atípicos, apalancamiento). Grafícala y dime si una línea recta es honesta.
```

### B · dashboard
**PROMPT 1 (`frontend-dashboard`):**
```
Construye la vista <NOMBRE> del dashboard usando EXACTAMENTE el JSON de docs/api.md (con mocks por ahora). Recharts para gráficas. Muestra siempre el intervalo de confianza y el n junto a cada cifra (barras de error o texto), no solo el estimado.
Diseño simple y legible, textos en español.
```
**PROMPT 2 (`narrador-visual`):**
```
Revisa las gráficas de dashboard/ pensando en un comentarista o entrenador que las ve en 10 segundos (Comunicación) y con criterio de visualización honesta: ejes que empiecen donde corresponde, sin 3D, títulos que digan la conclusión, incertidumbre visible, etiquetas legibles, sin colores que engañen. Dame cambios concretos, archivo por archivo.
```

**Mientras tanto:** comunicación corta cada 30 min ("listo X / trabado en Y"). Si a las 11:30 algo no va, **se recorta una vista**, no se alarga.

---

## PASO 4b · 11:15 · PLUS DE IA (solo si el MVP ya corre)

Decisión rápida a las 11:15: si el dashboard y el backend ya funcionan juntos (o casi), A hace el plus de IA con máximo 40 min. Si no, se omite sin culpa. Corte duro: 12:15.

### A · agente `agente-ia-strands`
**PROMPT:**
```
El MVP ya corre. Agrega el plus de IA más simple: un "comentarista asistente" que responda preguntas de <USUARIO: entrenador/scout/comentarista> sobre nuestro hallazgo, con strands-agents 1.64.0 y boto3. El agente debe llamar tools que usan las MISMAS funciones del backend; nunca debe inventar ni recordar cifras. Prompt de sistema en español, respuestas de 2-3 frases citando las cifras de las tools (con IC y n). Endpoint POST /api/chat. Si no hay credenciales o Bedrock falla, la app debe seguir funcionando sin el chat. Credenciales solo del entorno, nunca en el código (el repo es público).
Luego pruébalo con 3 preguntas con respuesta que calculemos aparte y 1 imposible de responder con los datos.
```

### B
Agrega un panel de chat simple en `dashboard/` (agente `frontend-dashboard`): un cuadro de texto, la respuesta y un mensaje claro si el chat no está disponible.

**Valor para la rúbrica:** suma a Originalidad y Comunicación, pero solo si está bien hecho. Un chat que inventa números resta en Ejecución técnica.

---

## PASO 5 · 11:50 · PRIMERA ENTREGA (obligatoria, aunque esté incompleta)

1. A: avisa a B qué endpoints ya están listos.
2. B: apaga los mocks de esos endpoints (`VITE_USE_MOCKS=false`) y prueba que se vea todo.
3. Los dos: `.hackathon\setup.cmd --check` → corregir errores de versiones.
4. Subir a GitHub en un repo **PÚBLICO**: `git pull`, `git add`, `git commit`, `git push`. Como es público, revisa que no haya `.env`, llaves ni datos que no se puedan compartir.
5. Tomar la **captura o GIF del resultado** (lo piden como entregable) y guardarla en `docs/captura.png`. Commits a nombre de cada quien, **sin Co-Authored-By**. Nunca subir `.env`.

---

## PASO 6 · 11:50–12:30 · Refutar y pulir

### A · agente `escepticista-revisor`
**PROMPT:**
```
Esta es nuestra conclusión: "<CONCLUSIÓN>". Tus datos: docs/ y backend/.
Intenta refutarla: ¿hay confusores?, ¿Simpson?, ¿muestra pequeña?, ¿sesgo de selección?, ¿múltiples comparaciones sin corregir (Benjamini-Hochberg)?, ¿estamos diciendo causa donde solo hay asociación?
Corre los chequeos con código. Dime qué tan fuerte sigue la conclusión y cómo debemos redactarla de forma honesta.
```

### A · agente `estadistico-rigor` (si hay dudas de método)
**PROMPT:**
```
Revisa el método de <CÁLCULO> en backend/<ARCHIVO>. ¿Es correcto el intervalo? ¿Hay fuga de información o doble conteo? Verifica con una simulación o un caso con respuesta conocida.
```

### B · README (agente `frontend-dashboard` o `revisor-entrega`)
Usa `#readme-template` en el chat.
**PROMPT:**
```
Escribe README.md en la raíz siguiendo #readme-template. ARRIBA, un resumen de 3 a 5 oraciones sin tecnicismos: qué construimos, qué revela (con UN número y su incertidumbre) y quién lo usaría (entrenador, scout o comentarista) para qué. Debajo, el detalle: pregunta, datos, método, hallazgos con IC y n, límites, cómo correr, stack y equipo. Usa solo cifras que yo te pegue de la app; no inventes ninguna.
```

---

## PASO 7 · 12:30 · CONGELAR CÓDIGO
Desde aquí solo se arreglan errores. Nada de funciones nuevas.

## PASO 8 · 12:30–12:50 · Revisión final

### A
Verifica que **cada número del README coincida con la app**. Pega las cifras a B.

### B · agente `revisor-entrega`
**PROMPT:**
```
Haz la revisión final de entrega: ¿el README está en la raíz y cubre pregunta, datos, método, resultado, límites y cómo correr?, ¿corre la app de cero?, ¿hay secretos o archivos pesados que no deban subirse?, ¿cumple el stack fijado?, ¿los números del README coinciden con los de la app? Lista pendientes por prioridad.
```
Corregir pendientes. Luego, **solo B**:
```
.hackathon\setup.cmd --entregar
```
Esto valida, crea `entrega-<proyecto>-<fecha>.zip` y publica. **Hazlo a las 12:45 como tarde.**
Después, registra la entrega en el portal (databowlmexico.aluva.people.aws.dev): el .zip, el link del repo público, la captura y el README. Pregunta si se sube ahí o se publica solo con `--entregar`.

## PASO 9 · 12:50–13:00
Confirmar que se publicó. Afinar solo el README si el portal lo permite. No tocar código.

---

## Si algo falla

| Problema | Solución |
|---|---|
| No aparecen los agentes | Confiar en la carpeta (quitar Restricted Mode). Alternativa: `#rol-experto-datos` en el chat. |
| `No module named pandas` | Usar `.venv\Scripts\python`, no `python`. |
| `--check` marca versiones | No instales otra versión; vuelve a la del stack fijado. |
| El agente da un número sin correr código | Dile: "Corre el código y muéstrame la salida. No me des números de memoria." |
| Se acaba el tiempo | Recorta una vista. Una pregunta bien respondida gana a tres a medias. |
| Kiro pide aprobar cada comando | Es modo Supervised (más seguro). Puedes pasar a Autopilot solo en este proyecto. |

## Checklist final
- [ ] `--check` sin errores
- [ ] App corre de cero
- [ ] README en la raíz: 3–5 oraciones arriba (qué, qué revela, quién lo usa), límites, sin cifras inventadas
- [ ] Repo de GitHub PÚBLICO y sin secretos
- [ ] Captura/GIF del resultado incluida
- [ ] Cada cifra con IC y n
- [ ] Sin secretos en el repo
- [ ] `--entregar` hecho antes de las 12:50
