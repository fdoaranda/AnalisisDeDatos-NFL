# Contrato de API — Índice de disfraz defensivo

> Fuente de verdad entre `backend/` (Hugo) y `dashboard/` (Fernando).
> Fernando construye con MOCKS que tengan EXACTAMENTE estas formas; Hugo hace que la API real las devuelva.
> **Si cambia algo aquí: avisar en persona en ese momento y anotarlo en el Registro de cambios.**

## Convenciones
- **Rutas relativas sin diagonal inicial** en el dashboard: `fetch('api/resumen?metrica=muestra_no_manda')`, nunca `fetch('/api/...')`, `localhost` ni URLs absolutas. La app se publica en una subruta.
- Desarrollo: Vite (5173) y Uvicorn (8000) por separado; `vite.config.ts` hace proxy de `/api` a `http://localhost:8000` y conserva `base: './'`. En producción, el mismo servidor sirve `dashboard/dist` y la API.
- Todo JSON, `snake_case`, números como números, nulos como `null` (nunca `NaN` ni `""`).
- **Proporciones en 0-1** dentro de `Estimacion` (el dashboard las muestra como %). Diferencias en puntos de proporción (0.05 = 5 puntos porcentuales).
- Respuestas ya agregadas: el dashboard no calcula nada, solo formatea.
- Equipos con la abreviatura de los datos (`KC`, `TB`...). 32 equipos.
- Los datos se precalculan una vez (script en `tools/`) y la API los carga al arrancar. Respuesta < 1 s.

### Forma de toda cifra estadística: `Estimacion`
```json
{ "estimado": 0.184, "ic_inf": 0.151, "ic_sup": 0.219, "n": 262, "metodo": "cluster_bootstrap_partido", "nota": null }
```
- Nunca hay `estimado` sin `ic_inf`, `ic_sup` y `n`. Si no hay datos: `estimado`, `ic_inf`, `ic_sup` en `null` y `n: 0`.
- `n` = jugadas en el denominador.
- `metodo` ∈ `"cluster_bootstrap_partido"` (tasas: remuestrea partidos, 2,000 réplicas, semilla 0) · `"estratificada"` (diferencia equipo − resto con `stratified_comparison`, estratos down × yardas por ganar × formación).
- `nota`: si `n < 30` → `"pocos datos: interpretar con cautela"`. El dashboard la muestra visible.

### Métricas (`metrica`)
| id | etiqueta visible | numerador / denominador |
|---|---|---|
| `muestra_no_manda` | Muestra blitz y no lo manda | 5+ en la línea al snap y ≤4 atacan / jugadas de pase con snap |
| `blitz_escondido` | Blitz escondido | ≤4 en la línea al snap y 5+ atacan / jugadas de pase con snap |
| `rotacion_cascara` | Muestra 2 safeties profundos y rota | juega Cover-3 o Cover-1 / jugadas con 2 safeties profundos al snap y con pase |

### Errores
Todas las respuestas no-200 tienen esta forma (también los errores de validación de FastAPI, que se convierten a 400):
```json
{ "error": { "codigo": "parametro_invalido", "mensaje": "El equipo 'XYZ' no existe. Usa uno de /api/meta." } }
```
| HTTP | `codigo` | Cuándo |
|---|---|---|
| 400 | `parametro_invalido` | `metrica` o `equipo` faltante o fuera de la lista de `/api/meta` |
| 404 | `sin_datos` | el filtro no tiene jugadas |
| 500 | `interno` | error del servidor (mensaje genérico, sin detalles internos) |

---

## Endpoints

| # | Método | Ruta | Vista | Estado |
|---|---|---|---|---|
| 1 | GET | `/health` | arranque (contrato del evento) | mock / real |
| 2 | GET | `/api/meta` | encabezado, selectores, pie de página | mock / real |
| 3 | GET | `/api/resumen?metrica=` | Vista 1: ranking de los 32 equipos | mock / real |
| 4 | GET | `/api/comparacion?equipo=` | Vista 2: perfil del equipo contra la liga | mock / real |
| 5 | GET | `/api/serie?equipo=&metrica=` | Vista 3: equipo vs liga por situación | mock / real |

`/api/detalle` y `/api/chat` no entran en el MVP.

### 1. `GET /health`
```json
{ "status": "ok" }
```

### 2. `GET /api/meta`
Sin parámetros.
```json
{
  "fuente": "NFL Big Data Bowl: tracking + PFF, temporada 2021, semanas 1-8",
  "temporada": 2021,
  "semanas": [1, 8],
  "partidos": 122,
  "jugadas": 8522,
  "equipos": ["ARI", "ATL", "BAL", "...", "WAS"],
  "metricas": [
    { "id": "muestra_no_manda", "etiqueta": "Muestra blitz y no lo manda", "descripcion": "5 o más defensores en la línea al snap y 4 o menos atacan al QB" },
    { "id": "blitz_escondido", "etiqueta": "Blitz escondido", "descripcion": "4 o menos defensores en la línea al snap y 5 o más atacan al QB" },
    { "id": "rotacion_cascara", "etiqueta": "Muestra 2 safeties profundos y rota", "descripcion": "De las jugadas con 2 safeties a 10 yd o más al snap, % que juega Cover-3 o Cover-1" }
  ],
  "umbrales": { "linea_profundidad_yd": 2.0, "linea_ancho_yd": 8.0, "safety_profundo_yd": 10.0 },
  "limitaciones": [
    "Solo jugadas de pase de 2021, semanas 1-8.",
    "Lo que se juega viene de etiquetas PFF (anotación humana).",
    "Mide cuánto disfraza cada defensa, no si el disfraz funciona.",
    "La rotación de safeties excluye sacks y scrambles (no tienen frame de pase)."
  ],
  "generado": "2026-11-20T11:30:00Z"
}
```

### 3. `GET /api/resumen`
Vista 1. Query: `metrica` (obligatorio, id de `/api/meta`).
`equipos` viene **ya ordenado** de mayor a menor tasa (orden por tasa encogida con `shrink_rates`; `posicion` 1 = el que más disfraza).
```json
{
  "metrica": "muestra_no_manda",
  "titulo": "KC muestra blitz y no lo manda en 31% de sus pases; la liga, en 19%",
  "liga": { "estimado": 0.195, "ic_inf": 0.186, "ic_sup": 0.204, "n": 8498, "metodo": "cluster_bootstrap_partido", "nota": null },
  "equipos": [
    {
      "equipo": "KC",
      "posicion": 1,
      "tasa": { "estimado": 0.31, "ic_inf": 0.26, "ic_sup": 0.36, "n": 287, "metodo": "cluster_bootstrap_partido", "nota": null },
      "diferencia_vs_liga": { "estimado": 0.11, "ic_inf": 0.06, "ic_sup": 0.16, "n": 8498, "metodo": "estratificada", "nota": null },
      "q_bh": 0.003,
      "distinto_de_liga": true
    }
  ]
}
```
- `diferencia_vs_liga`: equipo (1) contra el resto de la liga (0), ajustada por estratos.
- `q_bh`: p-valor corregido por Benjamini-Hochberg sobre los 32 equipos de esa métrica. `distinto_de_liga = q_bh < 0.05`.

### 4. `GET /api/comparacion`
Vista 2. Query: `equipo` (obligatorio).
```json
{
  "equipo": "KC",
  "titulo": "KC disfraza más que la liga en 2 de 3 métricas",
  "metricas": [
    {
      "metrica": "muestra_no_manda",
      "etiqueta": "Muestra blitz y no lo manda",
      "equipo": { "estimado": 0.31, "ic_inf": 0.26, "ic_sup": 0.36, "n": 287, "metodo": "cluster_bootstrap_partido", "nota": null },
      "liga": { "estimado": 0.195, "ic_inf": 0.186, "ic_sup": 0.204, "n": 8498, "metodo": "cluster_bootstrap_partido", "nota": null },
      "diferencia_vs_liga": { "estimado": 0.11, "ic_inf": 0.06, "ic_sup": 0.16, "n": 8498, "metodo": "estratificada", "nota": null },
      "posicion": 1,
      "distinto_de_liga": true
    }
  ]
}
```
Siempre trae las 3 métricas en el orden de `/api/meta`.

### 5. `GET /api/serie`
Vista 3. Query: `equipo` (obligatorio), `metrica` (obligatorio; `muestra_no_manda` o `blitz_escondido`. `rotacion_cascara` → 400).
`puntos` en este orden fijo de situaciones: `1er down` · `2do y corto (1-3)` · `2do y medio (4-7)` · `2do y largo (8+)` · `3ro/4to y corto (1-3)` · `3ro/4to y medio (4-7)` · `3ro/4to y largo (8+)`.
```json
{
  "equipo": "KC",
  "metrica": "muestra_no_manda",
  "titulo": "KC simula más el blitz en 3ro y largo: 45% contra 28% de la liga",
  "eje_x": "Situación (down y yardas por ganar)",
  "eje_y": "% de jugadas de pase",
  "puntos": [
    {
      "situacion": "3ro/4to y largo (8+)",
      "equipo": { "estimado": 0.45, "ic_inf": 0.33, "ic_sup": 0.57, "n": 52, "metodo": "cluster_bootstrap_partido", "nota": null },
      "liga": { "estimado": 0.28, "ic_inf": 0.26, "ic_sup": 0.30, "n": 1610, "metodo": "cluster_bootstrap_partido", "nota": null }
    },
    {
      "situacion": "2do y corto (1-3)",
      "equipo": { "estimado": 0.12, "ic_inf": 0.0, "ic_sup": 0.31, "n": 17, "metodo": "cluster_bootstrap_partido", "nota": "pocos datos: interpretar con cautela" },
      "liga": { "estimado": 0.15, "ic_inf": 0.12, "ic_sup": 0.18, "n": 520, "metodo": "cluster_bootstrap_partido", "nota": null }
    }
  ]
}
```
Una situación sin jugadas del equipo se devuelve con `equipo.estimado: null` y `n: 0` (no se omite).

---

## Tipos TypeScript (Fernando los copia a `dashboard/src/types/api.ts`)
```ts
export type MetricaId = 'muestra_no_manda' | 'blitz_escondido' | 'rotacion_cascara';
export type MetodoEstimacion = 'cluster_bootstrap_partido' | 'estratificada';

export interface Estimacion {
  estimado: number | null;
  ic_inf: number | null;
  ic_sup: number | null;
  n: number;
  metodo: MetodoEstimacion;
  nota: string | null;
}

export interface ApiError {
  error: { codigo: 'parametro_invalido' | 'sin_datos' | 'interno'; mensaje: string };
}

export interface Health { status: 'ok' }

export interface MetricaInfo { id: MetricaId; etiqueta: string; descripcion: string }

export interface Meta {
  fuente: string;
  temporada: number;
  semanas: [number, number];
  partidos: number;
  jugadas: number;
  equipos: string[];
  metricas: MetricaInfo[];
  umbrales: { linea_profundidad_yd: number; linea_ancho_yd: number; safety_profundo_yd: number };
  limitaciones: string[];
  generado: string;
}

export interface EquipoRanking {
  equipo: string;
  posicion: number;
  tasa: Estimacion;
  diferencia_vs_liga: Estimacion;
  q_bh: number | null;
  distinto_de_liga: boolean;
}

export interface Resumen {
  metrica: MetricaId;
  titulo: string;
  liga: Estimacion;
  equipos: EquipoRanking[];
}

export interface MetricaEquipo {
  metrica: MetricaId;
  etiqueta: string;
  equipo: Estimacion;
  liga: Estimacion;
  diferencia_vs_liga: Estimacion;
  posicion: number;
  distinto_de_liga: boolean;
}

export interface Comparacion {
  equipo: string;
  titulo: string;
  metricas: MetricaEquipo[];
}

export interface PuntoSituacion {
  situacion: string;
  equipo: Estimacion;
  liga: Estimacion;
}

export interface Serie {
  equipo: string;
  metrica: Exclude<MetricaId, 'rotacion_cascara'>;
  titulo: string;
  eje_x: string;
  eje_y: string;
  puntos: PuntoSituacion[];
}
```

## Mocks (Fernando)
- Un JSON por endpoint en `dashboard/src/mocks/` con la MISMA forma que arriba (cifras inventadas).
- Interruptor `VITE_USE_MOCKS=true|false`; al integrar, `false`, sin cambiar código.
- Incluir casos feos a propósito: una situación con `estimado: null` y `n: 0`, un equipo con `nota` de pocos datos, un IC que cruza la línea de la liga, y una respuesta `ApiError`.

## Reglas para Hugo (backend)
- `backend/main.py` expone `app`; todo bajo `/api/...` salvo `/health`.
- Cargar agregados precalculados UNA vez al arrancar (lifespan). No leer el tracking por request.
- Todo IC sale de `tools/stats_toolkit.py`; semilla fija.
- Handler de excepciones que devuelva siempre la forma `ApiError` (incluye `RequestValidationError` → 400).
- `summary` en cada endpoint (Swagger en `/docs`). Probar cada endpoint antes de marcarlo "real".

## Registro de cambios del contrato
| Hora | Endpoint | Cambio | Quién avisó | Confirmado por |
|---|---|---|---|---|
| ~11:20 | todos | Contrato inicial a partir de PLAN.md | Hugo | |
