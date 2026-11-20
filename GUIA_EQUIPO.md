# Guía para 2 personas · Hackathon NFL Big Data Bowl UNAM · 20 nov 2026

Evento: 10:00–13:00 (hora CDMX). Es una **app**. Entrega con `.hackathon\setup.cmd --entregar`.

## Roles

| | **A · "Números"** | **B · "Jurado"** |
|---|---|---|
| Carpeta | `backend/`, `data/`, `docs/` | `dashboard/`, `README.md` |
| Agentes Kiro | `experto-datos`, `auditor-calidad`, `estadistico-rigor`, `escepticista-revisor`, `backend-fastapi` | `lider-reto`, `frontend-dashboard`, `narrador-visual`, `revisor-entrega` |
| Responsable de | que cada número sea correcto, con IC y n | que se vea claro, que corra y que el README venda el proyecto |
| Entrega | — | **B corre `--entregar`** (una sola persona) |

Regla de oro: **cada quien edita solo su carpeta**. El único archivo compartido es `docs/api.md` (el contrato). Si hay que cambiarlo, avisar en voz alta.

## Antes de las 10:00 (los dos)

- [ ] Copiar el kit (`.kiro/`, `tools/`, `docs/`, `PLAN.md`) a la carpeta del proyecto.
- [ ] Abrir la carpeta en Kiro y **confiar en ella** (quitar "Restricted Mode"). Si no, los agentes no aparecen.
- [ ] Probar que se ven los agentes en el selector.
- [ ] Correr `.venv\Scripts\python tools/test_retos.py`. Debe pasar todo (33 o 35).
- [ ] Siempre usar `.venv\Scripts\python`, nunca el `python` suelto (no trae pandas).
- [ ] Activar licencia de Kiro (portal, paso 4) y bajar el dataset (paso 5).

## Reloj del evento

| Hora | A (Números) | B (Jurado) |
|---|---|---|
| **10:00–10:20** | Cargar datos, correr `auditor-calidad`: columnas, nulos, duplicados, rangos. Anotar hallazgos en `PLAN.md`. | Leer el reto. Con `lider-reto` proponer 2–3 preguntas candidatas. Preparar `dashboard/` con datos de mentira (mocks). |
| **10:20–10:40** | Con `experto-datos`: ¿qué análisis responde la pregunta, con qué muestra y qué riesgos tiene? | Dibujar el esqueleto de las 3 vistas máximas. |
| **10:40** (los dos juntos, 10 min) | **Fijar la pregunta central** y llenar `PLAN.md` + `docs/api.md` (qué endpoints, qué JSON). Límite 10:45. | Igual. Si no hay acuerdo, decide quien lleva los números. |
| **10:45–11:50** | Implementar endpoints del contrato en `backend/` (FastAPI). Cada cifra con `{estimado, ic_inf, ic_sup, n, metodo, nota}`. Probar con `/health` y `/api/resumen`. | Construir el dashboard contra los **mocks** (`VITE_USE_MOCKS=true`). No esperar al backend. |
| **11:50** | **Primera entrega:** `--check`, subir a GitHub. | Integrar: apagar mocks, conectar al backend real. Correr `--check`. |
| **11:50–12:30** | `escepticista-revisor` intenta refutar la conclusión. Corregir. | Pulir gráficas y textos. Escribir README con `readme-template`. |
| **12:30** | **Congelar código.** Solo arreglos de errores. | Igual. |
| **12:30–12:50** | Revisar que los números del README coincidan con la app. | `revisor-entrega` → corregir → `--entregar`. |
| **12:50–13:00** | Verificar que se publicó. No tocar nada más. | Afinar README si el portal lo permite. |

## Cómo no esperarse el uno al otro

1. **El contrato manda.** B construye contra `docs/api.md` con mocks; A implementa lo mismo. Cuando A termina un endpoint, lo avisa y B solo apaga el mock de ese endpoint.
2. **Si A se atrasa**, B sigue con mocks y se ve igual. **Si B se atrasa**, A deja los endpoints probados con `curl` y ayuda con textos del README.
3. **Si algo no se logra a las 11:30**, se recorta (una vista menos), no se alarga.
4. Un mensaje corto cada ~30 min: "listo X / me trabé en Y".

## Git

- Un repo, ramas cortas o commits pequeños; A solo toca `backend/`, `data/`, `docs/`; B solo `dashboard/` y `README.md`. Así casi no hay conflictos.
- Hacer `git pull` antes de cada `git push`.
- Commits a nombre de cada quien, **sin líneas `Co-Authored-By`**.
- Nunca subir `.env`, claves ni credenciales.

## Qué hacer con los agentes

- Pedir una cosa a la vez y con la pregunta clara.
- Para cualquier cifra, exigir: **n, intervalo de confianza y cómo se calculó**. Si el agente no corrió código, no es un resultado.
- Si el agente afirma una causa ("X provoca Y"), pedirle que intente refutarla (`escepticista-revisor`).
- Si un agente no aparece o falla, usar `#rol-experto-datos` (o el rol que toque) en el chat.
- Prompts por fase: `PROMPTS.md`. Pruebas de comportamiento: `RETOS.md`.

## Comandos útiles

```
.hackathon\setup.cmd --check       # valida versiones (hacerlo seguido)
.hackathon\setup.cmd --entregar    # valida + crea el zip + publica (solo B, al final)
.venv\Scripts\python tools/test_retos.py
```

## Antes de entregar (checklist)

- [ ] `--check` sin errores.
- [ ] La app corre de cero (backend + dashboard).
- [ ] El README está en la raíz y explica: pregunta, datos, método, resultado, límites, cómo correrlo.
- [ ] Cada número del README sale del código y coincide con la app.
- [ ] Se dicen los límites: qué **no** se puede concluir.
- [ ] Sin secretos en el repo.
