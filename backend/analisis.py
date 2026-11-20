"""Cálculo de las métricas de disfraz a partir de backend/datos/jugadas_disfraz.csv.

Toda cifra con incertidumbre sale de tools/stats_toolkit.py. Semilla fija.
Cifra principal = IC 95 % por bootstrap de PARTIDOS (las jugadas de un partido no son independientes).
El q-value (Benjamini-Hochberg sobre un EE que supone independencia) es solo orientativo.
El archivo de entrada lo genera tools/precalcular_jugadas.py a partir de data/.
"""
from __future__ import annotations

import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.stats_toolkit import (benjamini_hochberg, cluster_bootstrap_ci,  # noqa: E402
                                 cluster_bootstrap_stratified_diff, shrink_rates)

ARCHIVO = ROOT / "backend" / "datos" / "jugadas_disfraz.csv"
TEMPORADA = 2021    # [OBSERVADO] games.csv: season = 2021 en los 122 partidos (docs/datos.md, hallazgo 1)
N_BOOT = 2000
N_BOOT_DIF = 20000   # la decisión Bonferroni usa colas de ~0.08 %: ~16 réplicas por cola con 20,000
ALPHA = 0.05
SEED = 0
N_MIN = 30          # por debajo, aviso de pocos datos
MIN_POR_BRAZO = 5   # regla de stratified_comparison
Q_FDR = 0.05
NOTA_Q = "orientativo, supone independencia entre jugadas"
METODO_TASA = "cluster_bootstrap_partido"
METODO_DIF = "estratificada_cluster_partido_bonferroni"
ESTRATOS = ["down", "ytg_cat", "formacion"]
UMBRAL_LINEA_PROF, UMBRAL_LINEA_ANCHO, UMBRAL_SAFETY = 2.0, 8.0, 10.0   # [SUPUESTO] ver PLAN.md
COL_LINEA = "n_linea_u2_l8"
COL_PROF = "n_saf_prof10"
UN_SAFETY = ["Cover-3", "Cover-1"]
SITUACIONES = ["1er down", "2do y corto (1-3)", "2do y medio (4-7)", "2do y largo (8+)",
               "3ro/4to y corto (1-3)", "3ro/4to y medio (4-7)", "3ro/4to y largo (8+)"]
_YTG_TXT = {"1-3": "corto (1-3)", "4-7": "medio (4-7)", "8+": "largo (8+)"}

METRICAS: dict[str, dict[str, str]] = {
    "muestra_no_manda": {
        "etiqueta": "Muestra blitz y no lo manda",
        "descripcion": "5 o más defensores en la línea al snap y 4 o menos atacan al QB",
    },
    "blitz_escondido": {
        "etiqueta": "Blitz escondido",
        "descripcion": "4 o menos defensores en la línea al snap y 5 o más atacan al QB",
    },
    "rotacion_cascara": {
        "etiqueta": "Muestra 2 safeties profundos y rota",
        "descripcion": "De las jugadas con 2 safeties a 10 yd o más al snap, % que juega Cover-3 o Cover-1",
    },
}
METRICAS_SERIE = ["muestra_no_manda", "blitz_escondido"]
LIMITACIONES = [
    "Solo jugadas de pase de 2021, semanas 1-8.",
    "Lo que se juega viene de etiquetas PFF (anotación humana).",
    "Mide cuánto disfraza cada defensa, no si el disfraz funciona.",
    "Cada equipo jugó 7 u 8 partidos: los intervalos por equipo pueden quedar estrechos.",
]


def _nivel_bonferroni(m: int) -> float:
    return 1 - ALPHA / m


def _txt_nivel(nivel: float) -> str:
    """0.95 -> '95 %'; 0.9984375 -> '99.84 %'."""
    return f"{100 * nivel:.2f}".rstrip("0").rstrip(".") + " %"


def criterio_distinto(m: int) -> dict:
    """Definición de 'distinto de la liga' para que el dashboard no escriba niveles ni textos a mano."""
    nivel_dec = _nivel_bonferroni(m)
    return {
        "nivel_ic_mostrado": 1 - ALPHA,
        "nivel_ic_decision": nivel_dec,
        "n_comparaciones": m,
        "metodo": "Bonferroni",
        "texto": (f"Distinto de la liga = el IC de decisión de {_txt_nivel(nivel_dec)} por partido "
                  f"(Bonferroni, {m} equipos) de la diferencia ajustada no incluye el 0. "
                  f"Las barras muestran el IC de {_txt_nivel(1 - ALPHA)}."),
    }


def limitacion_bonferroni(m: int) -> str:
    return (f"'Distinto de la liga' se decide con un IC de {_txt_nivel(_nivel_bonferroni(m))} por partido "
            f"(Bonferroni por {m} equipos), más exigente que el IC de 95 % que se muestra; "
            f"un equipo puede tener el IC de 95 % sin el 0 y aun así no salir distinto.")


# ----------------------------------------------------------------------------- carga
def cargar_jugadas(path: Path = ARCHIVO) -> pd.DataFrame:
    """Lee el precálculo y arma una columna 0/1 por métrica (NaN = la jugada no entra en el denominador)."""
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path.relative_to(ROOT).as_posix()}. Genéralo con: python tools/precalcular_jugadas.py")
    df = pd.read_csv(path)
    df = df[(df["down"] != 0) & df["n_def_snap"].notna()].copy()   # sin conversiones de 2 pts; con snap
    linea, rush = df[COL_LINEA], df["n_rush"]
    df["muestra_no_manda"] = ((linea >= 5) & (rush <= 4)).astype(float)
    df["blitz_escondido"] = ((linea <= 4) & (rush >= 5)).astype(float)
    dos_altos = df[COL_PROF] == 2
    df["rotacion_cascara"] = np.where(dos_altos, df["pff_passCoverage"].isin(UN_SAFETY).astype(float), np.nan)
    df["ytg_cat"] = pd.cut(df["yardsToGo"], [-1, 3, 7, 100], labels=["1-3", "4-7", "8+"]).astype(str)
    df["formacion"] = df["offenseFormation"].where(
        df["offenseFormation"].isin(["SHOTGUN", "EMPTY", "SINGLEBACK"]), "OTRA")
    df["situacion"] = np.select(
        [df["down"] == 1, df["down"] == 2],
        ["1er down", "2do y " + df["ytg_cat"].map(_YTG_TXT)],
        default="3ro/4to y " + df["ytg_cat"].map(_YTG_TXT))
    return df


# ----------------------------------------------------------------------------- utilidades
def _num(x) -> float | None:
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) or math.isinf(x) else x


def _vacia(metodo: str, n: int = 0, nota: str | None = None) -> dict:
    return {"estimado": None, "ic_inf": None, "ic_sup": None, "n": int(n), "metodo": metodo, "nota": nota}


def _pct(x: float | None) -> str:
    return "sin dato" if x is None else f"{round(100 * x)} %"


def estimacion_tasa(sub: pd.DataFrame, col: str) -> dict:
    """Proporción con IC 95 % por bootstrap de partidos completos."""
    s = sub[[col, "gameId"]].dropna()
    n = len(s)
    if n == 0:
        return _vacia(METODO_TASA)
    if s["gameId"].nunique() < 2:
        return _vacia(METODO_TASA, n, "menos de 2 partidos: no se puede calcular el intervalo")
    r = cluster_bootstrap_ci(s[col], s["gameId"], n_boot=N_BOOT, seed=SEED)
    notas = []
    if n < N_MIN:
        notas.append("pocos datos: interpretar con cautela")
    if "advertencia" in r:
        notas.append(f"solo {r['n_grupos']} partidos: el intervalo puede quedar estrecho")
    return {"estimado": _num(r["estimado"]), "ic_inf": _num(r["ic_inf"]), "ic_sup": _num(r["ic_sup"]),
            "n": n, "metodo": METODO_TASA, "nota": "; ".join(notas) or None}


def diferencia_vs_liga(df: pd.DataFrame, col: str, equipo: str,
                       m: int) -> tuple[dict, float | None, tuple[float | None, float | None]]:
    """Equipo (1) vs resto (0) dentro de down x yardas por ganar x formación.

    Devuelve (estimación con IC 95 % por partido para mostrar, p-valor clásico solo para el q-value
    orientativo, IC de decisión Bonferroni 1 - 0.05/m por partido).
    """
    d = df[[col, "defensiveTeam", "gameId"] + ESTRATOS].dropna(subset=[col]).copy()
    d["es_equipo"] = (d["defensiveTeam"] == equipo).astype(int)
    alpha_dec = ALPHA / m
    try:
        r = cluster_bootstrap_stratified_diff(d, "es_equipo", col, ESTRATOS, "gameId",
                                              min_per_arm=MIN_POR_BRAZO, n_boot=N_BOOT_DIF, alpha=ALPHA,
                                              seed=SEED, alpha_decision=alpha_dec)
    except ValueError:
        return _vacia(METODO_DIF, 0, "sin contextos comparables con la liga"), None, (None, None)
    ee, dif = r["ee_clasico"], r["estimado"]
    p = math.erfc(abs(dif / ee) / math.sqrt(2)) if ee and ee > 0 else None
    dlo, dhi = _num(r["ic_inf_decision"]), _num(r["ic_sup_decision"])
    notas = ["ajustada por down, yardas por ganar y formación",
             f"IC de decisión {_txt_nivel(r['nivel_decision'])} (Bonferroni, {m} equipos): "
             f"[{dlo:+.3f}, {dhi:+.3f}]" if dlo is not None and dhi is not None else "sin IC de decisión"]
    if r["pct_filas_excluidas"] > 0:
        notas.append(f"{r['pct_filas_excluidas']:.1f} % de jugadas sin contexto comparable quedaron fuera")
    est = {"estimado": _num(r["estimado"]), "ic_inf": _num(r["ic_inf"]), "ic_sup": _num(r["ic_sup"]),
           "n": int(r["n_filas"]), "metodo": METODO_DIF, "nota": "; ".join(notas)}
    return est, p, (dlo, dhi)


def _distinto(decision: tuple[float | None, float | None]) -> bool:
    """Distinto de la liga = el IC Bonferroni por partido de la diferencia ajustada no incluye 0."""
    lo, hi = decision
    return lo is not None and hi is not None and (lo > 0 or hi < 0)


# ----------------------------------------------------------------------------- /api/resumen
SIN_DESTACADO = {
    "muestra_no_manda": "muestra blitz sin mandarlo",
    "blitz_escondido": "esconde el blitz",
    "rotacion_cascara": "rota de 2 safeties profundos a uno",
}


def _titulo_resumen(metrica: str, equipo: str | None, tasa: float | None, liga: float | None) -> str:
    """Nombra a un equipo solo si su IC por partido lo pone por encima de la liga."""
    if equipo is None:
        return f"Ningún equipo {SIN_DESTACADO[metrica]} claramente más que la liga ({_pct(liga)})"
    if metrica == "muestra_no_manda":
        return f"{equipo} muestra blitz y no lo manda en {_pct(tasa)} de sus pases; la liga, en {_pct(liga)}"
    if metrica == "blitz_escondido":
        return f"{equipo} esconde el blitz en {_pct(tasa)} de sus pases; la liga, en {_pct(liga)}"
    return (f"Con 2 safeties profundos al snap, {equipo} juega cobertura de un safety en {_pct(tasa)} "
            f"de las jugadas; la liga, en {_pct(liga)}")


def calcular_resumen(df: pd.DataFrame, metrica: str) -> dict:
    """Ranking de los 32 equipos para una métrica (forma de /api/resumen)."""
    liga = estimacion_tasa(df, metrica)
    lista = sorted(df.loc[df[metrica].notna(), "defensiveTeam"].unique())
    m = len(lista)   # comparaciones de ESTA métrica (Bonferroni por métrica)
    filas = []
    for equipo in lista:
        sub = df[df["defensiveTeam"] == equipo]
        valores = sub[metrica].dropna()
        dif, p, decision = diferencia_vs_liga(df, metrica, equipo, m)
        filas.append({"equipo": equipo, "tasa": estimacion_tasa(sub, metrica), "diferencia_vs_liga": dif,
                      "decision": decision, "p": np.nan if p is None else p,
                      "exitos": float(valores.sum()), "n": float(len(valores))})
    t = pd.DataFrame(filas)
    t["encogida"] = shrink_rates(t["exitos"], t["n"])["tasa_encogida"].to_numpy()
    t["q"] = benjamini_hochberg(t["p"], q=Q_FDR)["p_ajustado_BH"].to_numpy()
    t = t.sort_values(["encogida", "equipo"], ascending=[False, True]).reset_index(drop=True)
    equipos = [{"equipo": r.equipo, "posicion": i + 1, "tasa": r.tasa, "diferencia_vs_liga": r.diferencia_vs_liga,
                "distinto_de_liga": _distinto(r.decision), "q_bh": _num(r.q), "q_bh_nota": NOTA_Q}
               for i, r in enumerate(t.itertuples())]
    arriba = [e for e in equipos if e["distinto_de_liga"] and (e["diferencia_vs_liga"]["estimado"] or 0) > 0]
    if arriba:
        titulo = _titulo_resumen(metrica, arriba[0]["equipo"], arriba[0]["tasa"]["estimado"], liga["estimado"])
    else:
        titulo = _titulo_resumen(metrica, None, None, liga["estimado"])
    return {"metrica": metrica, "titulo": titulo, "liga": liga, "equipos": equipos}


# ----------------------------------------------------------------------------- /api/meta
def calcular_meta(df: pd.DataFrame) -> dict:
    return {
        "fuente": f"NFL Big Data Bowl: tracking + PFF, temporada {TEMPORADA}, "
                  f"semanas {int(df['week'].min())}-{int(df['week'].max())}",
        "temporada": TEMPORADA,
        "semanas": [int(df["week"].min()), int(df["week"].max())],
        "partidos": int(df["gameId"].nunique()),
        "jugadas": int(len(df)),
        "equipos": sorted(df["defensiveTeam"].unique().tolist()),
        "metricas": [{"id": k, **v} for k, v in METRICAS.items()],
        "umbrales": {"linea_profundidad_yd": UMBRAL_LINEA_PROF, "linea_ancho_yd": UMBRAL_LINEA_ANCHO,
                     "safety_profundo_yd": UMBRAL_SAFETY},
        "limitaciones": LIMITACIONES + [limitacion_bonferroni(int(df["defensiveTeam"].nunique()))],
        "criterio_distinto": criterio_distinto(int(df["defensiveTeam"].nunique())),
        "generado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ----------------------------------------------------------------------------- /api/comparacion
def calcular_comparacion(resumenes: dict[str, dict], equipo: str) -> dict:
    """Perfil del equipo en las 3 métricas; reutiliza lo ya calculado para /api/resumen."""
    metricas = []
    for m in METRICAS:
        r = resumenes[m]
        fila = next(e for e in r["equipos"] if e["equipo"] == equipo)
        metricas.append({"metrica": m, "etiqueta": METRICAS[m]["etiqueta"], "equipo": fila["tasa"],
                         "liga": r["liga"], "diferencia_vs_liga": fila["diferencia_vs_liga"],
                         "posicion": fila["posicion"], "distinto_de_liga": fila["distinto_de_liga"]})
    arriba = sum(1 for x in metricas if x["distinto_de_liga"] and (x["diferencia_vs_liga"]["estimado"] or 0) > 0)
    if arriba:
        titulo = f"{equipo} disfraza claramente más que la liga en {arriba} de {len(metricas)} métricas"
    else:
        titulo = f"{equipo} no disfraza claramente más que la liga en ninguna de las {len(metricas)} métricas"
    return {"equipo": equipo, "titulo": titulo, "metricas": metricas}


# ----------------------------------------------------------------------------- /api/serie
def liga_por_situacion(df: pd.DataFrame, metrica: str) -> dict[str, dict]:
    """Tasa de la liga en cada situación (se calcula una vez al arrancar)."""
    return {s: estimacion_tasa(df[df["situacion"] == s], metrica) for s in SITUACIONES}


def calcular_serie(df: pd.DataFrame, liga: dict[str, dict], equipo: str, metrica: str) -> dict:
    """Equipo vs liga por situación (main.py lo guarda en caché tras el primer request)."""
    sub = df[df["defensiveTeam"] == equipo]
    puntos = [{"situacion": s, "equipo": estimacion_tasa(sub[sub["situacion"] == s], metrica), "liga": liga[s]}
              for s in SITUACIONES]
    # Título: la situación con mayor exceso sobre la liga entre las que el IC del equipo queda arriba de la liga
    cand = [p for p in puntos
            if p["equipo"]["n"] >= N_MIN and p["equipo"]["ic_inf"] is not None and p["liga"]["estimado"] is not None
            and p["equipo"]["ic_inf"] > p["liga"]["estimado"]]
    verbo = "simula más el blitz" if metrica == "muestra_no_manda" else "esconde más el blitz"
    if cand:
        p = max(cand, key=lambda x: x["equipo"]["estimado"] - x["liga"]["estimado"])
        titulo = (f"{equipo} {verbo} en {p['situacion']}: {_pct(p['equipo']['estimado'])} "
                  f"contra {_pct(p['liga']['estimado'])} de la liga")
    else:
        titulo = f"En ninguna situación {equipo} se separa claramente por encima de la liga en «{METRICAS[metrica]['etiqueta']}»"
    return {"equipo": equipo, "metrica": metrica, "titulo": titulo,
            "eje_x": "Situación (down y yardas por ganar)", "eje_y": "% de jugadas de pase", "puntos": puntos}
