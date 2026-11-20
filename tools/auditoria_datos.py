"""Auditoría de calidad de data/ (NO modifica los datos). Uso:
    .venv\\Scripts\\python tools\\auditoria_datos.py > docs\\auditoria_salida.txt
Imprime resultados crudos; docs/datos.md se redacta a partir de esta salida.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from stats_toolkit import audit_dataframe  # noqa: E402

D = ROOT / "data"
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 200)


def titulo(t: str) -> None:
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


def resumen(nombre: str, df: pd.DataFrame, key: list[str]) -> dict:
    titulo(f"AUDIT {nombre}  key={key}")
    r = audit_dataframe(df, key=key)
    print(f"filas={r['filas']:,} columnas={r['columnas']}")
    print(f"filas_duplicadas_exactas={r['filas_duplicadas_exactas']:,}  duplicados_en_llave={r['duplicados_en_llave']:,}")
    print("constantes:", r["columnas_constantes"])
    print("con >20% nulos:", r["columnas_con_>20%_nulos"])
    t = pd.DataFrame(r["detalle_columnas"]).set_index("columna")
    print(t.to_string())
    return r


def cuentas(df: pd.DataFrame, col: str, n: int = 40) -> None:
    print(f"\n-- value_counts({col}) dropna=False (top {n}) --")
    print(df[col].value_counts(dropna=False).head(n).to_string())


# ------------------------------------------------------------------ games
g = pd.read_csv(D / "games.csv")
resumen("games", g, ["gameId"])
for c in ["season", "week"]:
    cuentas(g, c)
g["fecha"] = pd.to_datetime(g["gameDate"], format="%m/%d/%Y", errors="coerce")
print("gameDate no parseables:", int(g["fecha"].isna().sum()), "rango:", g["fecha"].min(), g["fecha"].max())
print("equipos local:", g["homeTeamAbbr"].nunique(), " visita:", g["visitorTeamAbbr"].nunique(),
      " union:", len(set(g["homeTeamAbbr"]) | set(g["visitorTeamAbbr"])))
print("partidos por semana:\n", g.groupby("week").size().to_string())

# ------------------------------------------------------------------ players
p = pd.read_csv(D / "players.csv")
resumen("players", p, ["nflId"])
cuentas(p, "officialPosition")
print("\nformato height (patrón):\n", p["height"].astype(str).str.replace(r"\d", "9", regex=True).value_counts(dropna=False).to_string())
p["bd"] = pd.to_datetime(p["birthDate"], errors="coerce")
print("birthDate nulos/no parseables:", int(p["bd"].isna().sum()), "de", len(p), "| rango", p["bd"].min(), p["bd"].max())
fmt = p["birthDate"].astype(str).str.replace(r"\d", "9", regex=True).value_counts(dropna=False)
print("formatos birthDate:\n", fmt.to_string())
print("nombres repetidos en displayName:", int(p["displayName"].duplicated().sum()))

# ------------------------------------------------------------------ plays
pl = pd.read_csv(D / "plays.csv")
resumen("plays", pl, ["gameId", "playId"])
for c in ["quarter", "down", "passResult", "offenseFormation", "dropBackType", "pff_playAction",
          "pff_passCoverage", "pff_passCoverageType", "personnelD", "foulName1"]:
    cuentas(pl, c, 25)
print("\nyardsToGo describe:\n", pl["yardsToGo"].describe().to_string())
print("defendersInBox describe:\n", pl["defendersInBox"].describe().to_string())
print("playResult describe:\n", pl["playResult"].describe().to_string())
print("absoluteYardlineNumber describe:\n", pl["absoluteYardlineNumber"].describe().to_string())
print("plays con playResult != prePenaltyPlayResult - penaltyYards (sin penalización)", end=": ")
print(int(((pl["penaltyYards"].isna()) & (pl["playResult"] != pl["prePenaltyPlayResult"])).sum()))
print("nulos por passResult:")
print(pl.assign(pr=pl["passResult"].fillna("NA_")).groupby("pr")[["defendersInBox", "pff_passCoverage", "offenseFormation", "dropBackType", "down"]]
      .apply(lambda x: x.isna().sum()).to_string())
print("plays con down nulo, por quarter:\n", pl[pl["down"].isna()].groupby("quarter").size().to_string())

# ------------------------------------------------------------------ pff
pf = pd.read_csv(D / "pffScoutingData.csv", na_values=["NA"])
resumen("pffScoutingData", pf, ["gameId", "playId", "nflId"])
for c in ["pff_role", "pff_positionLinedUp", "pff_hit", "pff_hurry", "pff_sack", "pff_beatenByDefender",
          "pff_hitAllowed", "pff_hurryAllowed", "pff_sackAllowed", "pff_blockType", "pff_backFieldBlock"]:
    cuentas(pf, c, 30)
print("\nnulos de pff_hurry por pff_role:")
print(pf.groupby("pff_role", dropna=False)[["pff_hit", "pff_hurry", "pff_sack", "pff_hurryAllowed", "pff_nflIdBlockedPlayer", "pff_blockType"]]
      .apply(lambda x: x.notna().sum()).to_string())
print("\nfilas por jugada (pff): ", pf.groupby(["gameId", "playId"]).size().describe().to_string())

# ------------------------------------------------------------------ tracking
titulo("TRACKING: carga completa")
files = sorted((D / "tracking").glob("tracking_*.csv"))
print("archivos:", len(files))
dt = {"gameId": "int32", "playId": "int32", "nflId": "Int32", "frameId": "int16", "jerseyNumber": "Int16",
      "team": "category", "playDirection": "category", "x": "float32", "y": "float32", "s": "float32",
      "a": "float32", "dis": "float32", "o": "float32", "dir": "float32", "event": "category"}
partes, hdr_distintos, game_vs_name = [], [], []
for f in files:
    d = pd.read_csv(f, dtype={**dt, "time": "string"}, na_values=["NA"], keep_default_na=False)
    # 'None' en event es un texto observado; se conserva como categoría
    d["time"] = pd.to_datetime(d["time"], utc=True, errors="coerce")
    if list(d.columns) != ["gameId", "playId", "nflId", "frameId", "time", "jerseyNumber", "team", "playDirection",
                           "x", "y", "s", "a", "dis", "o", "dir", "event"]:
        hdr_distintos.append(f.name)
    gid_nombre = int(f.stem.split("_")[1])
    game_vs_name.append((f.name, gid_nombre, sorted(d["gameId"].unique().tolist())))
    partes.append(d)
t = pd.concat(partes, ignore_index=True)
for c in ["team", "playDirection", "event"]:
    t[c] = t[c].astype("category")
del partes
print("archivos con encabezado distinto:", hdr_distintos)
malos = [(n, a, b) for n, a, b in game_vs_name if b != [a]]
print("archivos cuyo gameId interno != nombre de archivo:", malos)
KEY = ["gameId", "playId", "nflId", "frameId"]
resumen("tracking", t, KEY)
for c in ["team", "playDirection", "event"]:
    cuentas(t, c, 40)
print("\nnflId nulo: filas=", int(t["nflId"].isna().sum()), "| team en esas filas:", t.loc[t["nflId"].isna(), "team"].value_counts().to_dict())
print("jerseyNumber nulo por team:", t.loc[t["jerseyNumber"].isna(), "team"].value_counts(dropna=False).to_dict())
print("\nnulos por team (columnas con nulos):")
print(t.groupby("team", observed=True)[["x", "y", "s", "a", "dis", "o", "dir", "jerseyNumber"]].apply(lambda x: x.isna().sum()).to_string())

titulo("TRACKING: rangos físicos")
print("x fuera [0,120]:", int(((t.x < 0) | (t.x > 120)).sum()), " y fuera [0,53.3]:", int(((t.y < 0) | (t.y > 53.3)).sum()))
print("s<0:", int((t.s < 0).sum()), " s>14 (yd/s, umbral arbitrario de inspección):", int((t.s > 14).sum()), " a<-15 o a>15:", int(((t.a < -15) | (t.a > 15)).sum()))
print("dis<0:", int((t.dis < 0).sum()), " dis>1.5 (yd en 0.1 s):", int((t.dis > 1.5).sum()))
print("o fuera [0,360]:", int(((t.o < 0) | (t.o > 360)).sum()), " dir fuera [0,360]:", int(((t.dir < 0) | (t.dir > 360)).sum()))
print("cuantiles:")
print(t[["x", "y", "s", "a", "dis", "o", "dir"]].quantile([0, .001, .01, .5, .99, .999, 1]).to_string())
print("s máx por team:", t.groupby("team", observed=True)["s"].max().to_dict())

titulo("TRACKING: estructura por jugada")
jug = t.groupby(["gameId", "playId"]).agg(frames_max=("frameId", "max"), frames_min=("frameId", "min"),
                                          n_filas=("frameId", "size"), n_ids=("nflId", "nunique"))
print("jugadas en tracking:", len(jug))
print("frame mínimo (distribución):", jug["frames_min"].value_counts().to_dict())
print("frames_max describe:\n", jug["frames_max"].describe().to_string())
print("n jugadores distintos (sin balón) por jugada:\n", jug["n_ids"].value_counts().sort_index().to_string())
fr = t.groupby(KEY).size()
print("(game,play,nflId) con frames no contiguos: ", end="")
g3 = t.groupby(["gameId", "playId", "nflId"], dropna=False)["frameId"].agg(["min", "max", "count"])
print(int(((g3["max"] - g3["min"] + 1) != g3["count"]).sum()), "de", len(g3))
print("(game,play,nflId) cuyo nº de frames != frames_max de la jugada:", end=" ")
mx = jug["frames_max"]
g3 = g3.join(mx.rename("fmax"), on=["gameId", "playId"])
print(int((g3["count"] != g3["fmax"]).sum()))

titulo("TRACKING: eventos por jugada")
ev = t[t["event"].astype(str) != "None"][["gameId", "playId", "event", "frameId"]]
n_play = ev.drop_duplicates(["gameId", "playId", "event"]).groupby("event", observed=True).size().sort_values(ascending=False)
print("jugadas con cada evento (de", len(jug), "):\n", n_play.to_string())
print("eventos repetidos dentro de una jugada (mismo evento en >1 frame):")
rep = ev.groupby(["gameId", "playId", "event"], observed=True)["frameId"].nunique()
print(rep[rep > 1].groupby("event", observed=True).size().to_string())
print("event es el mismo en todas las filas de un frame?  frames con >1 valor distinto de event:",
      int((t.groupby(["gameId", "playId", "frameId"], observed=True)["event"].nunique() > 1).sum()))

titulo("TRACKING: dirección de juego y tiempo")
pd_play = t.groupby(["gameId", "playId"], observed=True)["playDirection"].nunique()
print("jugadas con >1 playDirection:", int((pd_play > 1).sum()))
print("time nulos/no parseables:", int(t["time"].isna().sum()))
dts = t.sort_values(KEY[:3] + ["frameId"]).groupby(["gameId", "playId", "nflId"], dropna=False)["time"].diff().dt.total_seconds()
print("diferencia de time entre frames consecutivos (s):\n", dts.describe().to_string())
print("time idéntico entre frames consecutivos (diff==0):", int((dts == 0).sum()), " de", int(dts.notna().sum()))

# ------------------------------------------------------------------ cruces
titulo("CRUCES (cardinalidad y filas sin pareja)")
def cruz(nombre, izq, der, on, validate):
    n0 = len(izq)
    m = izq.merge(der, on=on, how="left", validate=validate, indicator=True)
    print(f"{nombre}: filas izq={n0:,} -> {len(m):,}; sin pareja={int((m['_merge'] == 'left_only').sum()):,} (validate={validate} OK)")

cruz("plays -> games", pl[["gameId", "playId"]], g[["gameId"]], ["gameId"], "many_to_one")
cruz("pff -> plays", pf[["gameId", "playId", "nflId"]], pl[["gameId", "playId"]], ["gameId", "playId"], "many_to_one")
cruz("pff -> players", pf[["nflId"]], p[["nflId"]], ["nflId"], "many_to_one")
jug_r = jug.reset_index()[["gameId", "playId"]]
cruz("tracking(jugadas) -> plays", jug_r, pl[["gameId", "playId"]], ["gameId", "playId"], "one_to_one")
cruz("plays -> tracking(jugadas)", pl[["gameId", "playId"]], jug_r, ["gameId", "playId"], "one_to_one")
cruz("games -> tracking(juegos)", g[["gameId"]], t[["gameId"]].drop_duplicates(), ["gameId"], "one_to_one")
ids_t = t[["nflId"]].dropna().drop_duplicates()
ids_t["nflId"] = ids_t["nflId"].astype("int64")
cruz("tracking(nflId) -> players", ids_t, p[["nflId"]], ["nflId"], "many_to_one")
tp = t[["gameId", "playId", "nflId"]].dropna().drop_duplicates()
tp["nflId"] = tp["nflId"].astype("int64")
cruz("tracking(game,play,nflId) -> pff", tp, pf[["gameId", "playId", "nflId"]], ["gameId", "playId", "nflId"], "one_to_one")
cruz("pff -> tracking(game,play,nflId)", pf[["gameId", "playId", "nflId"]], tp, ["gameId", "playId", "nflId"], "one_to_one")

titulo("COBERTURA")
pl2 = pl.merge(g[["gameId", "week"]], on="gameId")
print("jugadas por semana (plays.csv):\n", pl2.groupby("week").size().to_string())
print("jugadas por posesión (top/bottom 5):\n", pl["possessionTeam"].value_counts().head(5).to_string(), "\n", pl["possessionTeam"].value_counts().tail(5).to_string())
print("equipos en possessionTeam:", pl["possessionTeam"].nunique(), "| jugadas por partido describe:\n", pl.groupby("gameId").size().describe().to_string())
print("¿hay jugadas no de pase? passResult nulo:", int(pl["passResult"].isna().sum()), "| dropBackType nulo:", int(pl["dropBackType"].isna().sum()))
print("equipo de tracking 'team' vs home/visitor: valores en t.team:", sorted(t["team"].astype(str).unique()))
print("\nOK fin auditoría")
