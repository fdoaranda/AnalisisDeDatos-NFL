---
inclusion: manual
---

# Plan del evento (horarios reales del portal: 10:00 a 13:00)

El reto ("Side Quest"): herramienta/visualización O métrica nueva para entrenador, scout o comentarista NFL. Entrega: .zip + repo PÚBLICO + captura/demo + README de 3-5 oraciones. Rúbrica: Visión de juego, Ejecución técnica, Comunicación, Originalidad. Dos personas: A = números (`backend/`), B = jurado (`dashboard/`, README).

| Hora | Fase | Salida |
|---|---|---|
| 10:00-10:15 | Licencia Kiro, descargar dataset, `--check` | Entorno OK en ambas máquinas |
| 10:15-10:40 | A: auditar y entender el dataset · B: abrir/validar proyecto, frontend con mocks | `docs/calidad-datos.md`, esqueleto con mocks |
| **10:40** | **Enfoque definido** (límite duro 10:45) | `PLAN.md` y `docs/api.md` acordados |
| 11:00-11:45 | Construcción: A API + análisis · B dashboard con mock | App funcionando por separado |
| **11:15** | Decisión del plus de IA: solo si el MVP ya corre (máx. 40 min, corte duro 12:15) | Sí/No anotado en PLAN.md |
| 11:45-11:50 | Integración (`VITE_USE_MOCKS=false`) | App end-to-end |
| 11:50 | Primera entrega de respaldo | `--check` + `--entregar` + push a GitHub (repo PÚBLICO) + captura del resultado |
| 12:00-12:30 | A: revisión escéptica de la conclusión · B: README (3-5 oraciones arriba) con cifras reales | Conclusión verificada |
| 12:30 | Congelar features | Solo arreglar y documentar |
| 12:40-12:50 | `revisor-entrega`, guion de demo, entrega final | Publicado |
| 13:00 | Cierre del evento | Margen de 10 min |

Regla: congelar features a las 12:30. Después solo arreglar y documentar.
