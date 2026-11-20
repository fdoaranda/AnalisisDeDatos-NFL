# Índice de disfraz defensivo: lo que la defensa muestra vs. lo que juega

Construimos un tablero que mide cuánto disfraza cada defensa de la NFL sus intenciones antes del snap: compara lo que la defensa **muestra** con la posición de sus jugadores (tracking) contra lo que **juega** (etiquetas de PFF). Lo más sólido que revela es la rotación de cáscara: con 2 safeties profundos al snap, Miami juega cobertura de un solo safety en ~65 % de las jugadas, contra ~36 % de la liga. Lo usaría un coordinador ofensivo para elegir protección y lectura del QB contra un rival, y un comentarista para explicar qué está escondiendo una defensa. Cada cifra trae su intervalo de confianza y su n, y el tablero dice también lo que **no** se puede concluir.

![Captura del tablero](docs/captura.png)

## Hallazgos

Temporada 2021, semanas 1 a 8, solo jugadas de pase. Un equipo se marca como "distinto de la liga" solo si pasa un criterio estricto (ver Método).

| Métrica | Liga (IC 95 %) | Equipos distintos de la liga |
|---|---|---|
| Rotación de cáscara: con 2 safeties profundos al snap, % que juega cobertura de un safety (Cover-3 o Cover-1) | 35.6 % [32.8, 38.5] | 4: MIA (65 %, por encima de la liga), TB, HOU y MIN |
| Muestra blitz y no lo manda: 5 o más en la línea al snap y 4 o menos atacan al QB | 19.5 % [18.2, 20.7] | 4, todos por debajo de la liga: LV, NYJ, CLE y SF. Ninguno por encima |
| Blitz escondido: 4 o menos en la línea al snap y 5 o más atacan | 8.8 % [8.1, 9.6] | 1, por debajo de la liga (BUF). Ninguno por encima |

- **Resultado honesto:** en "muestra blitz y no lo manda" y "blitz escondido" ningún equipo está claramente por encima de la liga. Con 7 u 8 partidos por equipo, la mayoría de las defensas no se distinguen del promedio. Eso también es un hallazgo.
- Cifras de cada equipo (con IC y n) en el tablero y en la API (`/api/resumen`, `/api/comparacion`).

## Qué tan robusto es

Probamos otros umbrales y otras mitades de temporada (análisis en [`tools/sensibilidad_estabilidad.py`](tools/sensibilidad_estabilidad.py)):

- **Rotación de cáscara:** el ranking casi no cambia al mover el umbral del safety (Spearman ≥ 0.96). Es la métrica más estable.
- **Muestra blitz y no lo manda:** el ranking es estable si "en la línea" es 8 o 10 yd, pero cambia con 6 yd. MIA queda entre los primeros y SF último en todas las definiciones probadas.
- **Blitz escondido:** el ranking entre equipos no se distingue del ruido de muestreo. No lo interpretamos como ranking.
- **Entre semanas 1-4 y 5-8** los rankings se parecen poco, pero no más de lo que se esperaría por azar con tan pocos partidos. No afirmamos que un equipo disfrace de forma constante.

## Datos

- Fuente: NFL Big Data Bowl (tracking de jugadores + etiquetas PFF), **temporada 2021, semanas 1 a 8**. 122 partidos y 8,557 jugadas de pase (8,498 con snap y defensores medidos para el frente).
- Ventana de tracking corta: unos 5 frames antes del snap, así que no estudiamos movimiento previo.
- "Lo que se juega" viene de etiquetas de PFF (anotación humana).
- Auditoría de calidad en [`docs/datos.md`](docs/datos.md). Los datos originales van en el `.zip` de entrega, pero **no están en este repositorio** (pesan 825 MB). La app usa un archivo precalculado: `backend/datos/jugadas_disfraz.csv`.

## Método

- **Definiciones:** "en la línea" = 2 yd o menos de profundidad y 8 yd o menos a lo ancho del balón al snap. Safety profundo = 10 yd o más. Son supuestos; por eso probamos su sensibilidad.
- **Tasas por equipo:** bootstrap por partido (se remuestrean partidos completos, porque las jugadas de un mismo partido no son independientes).
- **Diferencia contra la liga:** comparación estratificada por down × yardas por ganar × formación ofensiva.
- **"Distinto de la liga":** el intervalo por partido de la diferencia ajustada, al 99.84 % (Bonferroni, 32 equipos), no incluye 0. Las barras del tablero muestran el IC al 95 %. Es un criterio conservador a propósito: con 32 equipos, alguno saldría "distinto" por azar.
- Funciones estadísticas (solo numpy y pandas) en [`backend/stats_toolkit.py`](backend/stats_toolkit.py).

## Qué NO se puede concluir

- No mide si el disfraz **funciona** ni si engaña al QB: eso sería causal y con estos datos no se puede.
- No aplica a carreras, otras temporadas ni a semanas 9 en adelante.
- SF, CLE y NYJ salen bajos en "muestra blitz y no lo manda" y altos en "blitz escondido". Puede reflejar cuántos jugadores alinean habitualmente en la línea, y no un disfraz.
- Los umbrales de "en la línea" y "safety profundo" son supuestos.
- Con 7 u 8 partidos por equipo, los intervalos son anchos.

## Cómo correrlo

Requisitos del evento: Python 3.12.12 con `uv` y Node 22.23.1 (el entorno queda en `.venv`).

```powershell
# 1. Verificar el entorno
.\.hackathon\setup.cmd --check

# 2. API (terminal 1), puerto 8000
.venv\Scripts\uvicorn backend.main:app --port 8000

# 3. Dashboard (terminal 2)
cd dashboard
npm install
npm run dev
```

Abre `http://127.0.0.1:5173`. El dashboard usa la API real a través de un proxy de `/api` hacia `http://127.0.0.1:8000`. La API tarda unos 15 a 30 segundos en arrancar porque calcula los intervalos al iniciar. Documentación interactiva de la API en `http://127.0.0.1:8000/docs`.

## Estructura

```
backend/    API FastAPI (main.py, analisis.py, modelos.py, stats_toolkit.py)
  datos/    jugadas_disfraz.csv (una fila por jugada, precalculado)
dashboard/  React 18 + Vite + TypeScript + Tailwind 3 + Recharts (3 vistas)
docs/       api.md (contrato de la API), datos.md (auditoría), captura.png
tools/      scripts de auditoría, precálculo y sensibilidad
PLAN.md     pregunta, análisis declarados de antemano, supuestos y decisiones
```

## Equipo

Hugo (números: `backend/`, `docs/`, `tools/`) y Fernando (dashboard y README). Hackathon NFL Big Data Bowl, UNAM, 2026.


