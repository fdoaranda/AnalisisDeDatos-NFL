# Índice de disfraz defensivo: lo que la defensa muestra vs. lo que juega

Construimos un tablero que mide cuánto disfraza cada defensa de la NFL sus intenciones antes del snap. Compara lo que la defensa muestra con la posición de sus jugadores (tracking) contra lo que realmente juega (etiquetas de PFF). Las métricas son "muestra blitz y no lo manda", "blitz escondido" y "muestra 2 safeties profundos y rota". Cada cifra se reporta con su intervalo de confianza al 95% y su n. Lo usaría un coordinador ofensivo para elegir protección y lectura del QB contra un rival, y un comentarista para explicar qué hace una defensa.

> **Estado actual (avance parcial):** el dashboard está terminado con **datos de ejemplo (mocks)**. Las cifras que muestra son inventadas y **no son resultados del análisis**. Todavía faltan el cálculo real y la API real (ver [Pendiente](#pendiente)). Este README no incluye ningún hallazgo numérico porque aún no se ha calculado ninguno.

## Pregunta

¿Qué defensas muestran al snap algo distinto de lo que juegan, y en qué porcentaje de sus jugadas de pase, comparado con el promedio de la liga? Detalle y análisis declarados de antemano: [`PLAN.md`](PLAN.md).

## Métricas

| Métrica | Definición | Base (denominador) |
|---|---|---|
| Muestra blitz y no lo manda | 5 o más defensores en la línea al snap y 4 o menos atacan al QB | jugadas de pase con snap |
| Blitz escondido | 4 o menos en la línea al snap y 5 o más atacan | jugadas de pase con snap |
| Muestra 2 safeties profundos y rota | de las jugadas con 2 safeties a 10 yd o más al snap, % que juega Cover-3 o Cover-1 | jugadas con 2 safeties profundos al snap y con pase |

## Datos

- Fuente: NFL Big Data Bowl (tracking + PFF), **temporada 2021, semanas 1 a 8** (no 2023). 122 partidos, 8,557 jugadas de pase (8,522 tras quitar 35 conversiones de 2 puntos).
- Solo jugadas de pase. Ventana de tracking corta: unos 5 frames antes del snap, por lo que no se estudia movimiento previo.
- "Lo que se juega" viene de etiquetas PFF (anotación humana).
- Auditoría completa de calidad: [`docs/datos.md`](docs/datos.md). Los archivos de `data/` no se modifican y no se suben al repo.

## Vistas del dashboard

1. **Ranking de la liga:** los 32 equipos para una métrica, con barras de error (IC 95%), la línea de la liga y una tabla con cifra, IC y n.
2. **Perfil del equipo:** las 3 métricas del equipo elegido contra la liga, con IC, n y lugar entre los 32.
3. **Por situación:** las 2 métricas del frente por down × yardas por ganar, equipo contra liga.

Reglas de la interfaz: texto en español, aviso visible cuando n < 30, estados de carga y error, y el contrato de datos fijo en [`docs/api.md`](docs/api.md).

## Método

- Tasas por equipo: bootstrap por clusters de partido (2,000 réplicas, semilla 0).
- Diferencia equipo contra resto de la liga: comparación estratificada por down × yardas por ganar × formación.
- Pruebas múltiples: corrección Benjamini-Hochberg sobre los 32 equipos de cada métrica; "distinto de la liga" significa q < 0.05.
- Orden del ranking: tasa encogida por tamaño de muestra.
- Funciones en [`tools/stats_toolkit.py`](tools/stats_toolkit.py).

## Qué NO se puede concluir

- No mide si el disfraz funciona ni si engaña al QB (eso sería causal).
- No aplica a carreras, otras temporadas ni a semanas 9 en adelante.
- Los umbrales ("en la línea" a 2 yd de profundidad y 8 yd de ancho, safety profundo a 10 yd) son supuestos; está planeado probar su sensibilidad.
- La rotación de safeties excluye sacks y scrambles porque no tienen frame de pase.

## Cómo correr

Requisitos del evento: Python 3.12.12 con `uv`, Node 22.23.1. Entorno en `.venv`.

```powershell
# Verificar entorno (Windows)
.\.hackathon\setup.cmd --check

# Backend (hoy solo expone /health)
.venv\Scripts\uvicorn backend.main:app --reload --port 8000

# Dashboard (en otra terminal)
cd dashboard
npm install
npm run dev
```

El dashboard usa mocks por defecto. Para usar la API real: `VITE_USE_MOCKS=false`. Con mocks, `?error=1` en la URL fuerza el estado de error.

Producción: `npm run build` en `dashboard/` genera `dashboard/dist`, que el servidor sirve junto con la API.

## Estructura

```
backend/    API FastAPI (main.py con /health)
dashboard/  React 18 + Vite + TypeScript + Tailwind 3 + Recharts
  src/views/  Hallazgo.tsx (Vista 1), Perfil.tsx (Vista 2), Situacion.tsx (Vista 3)
  src/mocks/  JSON de ejemplo con la forma de docs/api.md
data/       datos originales (solo lectura, no versionados)
docs/       api.md (contrato), datos.md (auditoría), salidas de auditoría
tools/      scripts de auditoría y estadística
PLAN.md     pregunta, análisis declarados, reparto e hitos
```

## Pendiente

- [ ] Script de agregados precalculados en `tools/` con los IC y q reales.
- [ ] API real (`/api/meta`, `/api/resumen`, `/api/comparacion`, `/api/serie`) y apagar los mocks.
- [ ] Sensibilidad de umbrales y estabilidad entre semanas 1-4 y 5-8.
- [ ] Ajustes de visualización acordados en la revisión (notas de IC, n en las etiquetas, tooltips con IC).
- [ ] Verificar `npm run build`: aún no se ha compilado el dashboard en esta máquina.
- [ ] Cifras reales, captura o GIF, `--check`, `--entregar` y repositorio público sin secretos.

## Equipo

Hugo (números: `backend/`, `docs/`, `tools/`) y Fernando (dashboard y README). Hackathon NFL Big Data Bowl, UNAM.
