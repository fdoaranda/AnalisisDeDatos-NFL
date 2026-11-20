"""Verificaciones de seguimiento a tools/auditoria_datos.py (NO modifica datos).
    .venv\\Scripts\\python -u tools\\auditoria_extra.py > docs\\auditoria_extra_salida.txt
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

D = Path(__file__).resolve().parent.parent / "data"
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 200)


def titulo(t):
    print("\n" + "=" * 90 + f"\n{t}\n" + "=" * 90, flush=True)


# ---------------- tablas pequeñas
pl = pd.read_csv(D / "plays.csv")
p = pd.read_csv(D / "players.csv")
titulo("plays: casos raros")
print("down==0:", int((pl.down == 0).sum()), "| passResult en down==0:", pl.loc[pl.down == 0, "passResult"].value_counts().to_dict(),
      "| quarter:", pl.loc[pl.down == 0, "quarter"].value_counts().to_dict())
print(pl.loc[pl.down == 0, ["quarter", "yardsToGo", "yardlineNumber", "playDescription"]].head(4).to_string())
print("yardsToGo==0:", int((pl.yardsToGo == 0).sum()), "| down por yardsToGo==0:", pl.loc[pl.yardsToGo == 0, "down"].value_counts().to_dict())
x = pl[(pl.penaltyYards.isna()) & (pl.playResult != pl.prePenaltyPlayResult)]
print("playResult != prePenaltyPlayResult sin penaltyYards:", len(x), "| foulName1 nulo en ellas:", int(x.foulName1.isna().sum()),
      "| passResult:", x.passResult.value_counts().to_dict())
print(x[["prePenaltyPlayResult", "playResult", "passResult"]].head(5).to_string())
print("filas con penaltyYards notna pero foulName1 nulo:", int((pl.penaltyYards.notna() & pl.foulName1.isna()).sum()))
print("filas con foulName1 notna pero penaltyYards nulo:", int((pl.penaltyYards.isna() & pl.foulName1.notna()).sum()))
print("yardlineSide nulo:", int(pl.yardlineSide.isna().sum()), "| yardlineNumber en esas:", pl.loc[pl.yardlineSide.isna(), "yardlineNumber"].value_counts().to_dict())
print("dropBackType nulo por pff_playAction:", pl.loc[pl.dropBackType.isna(), "pff_playAction"].value_counts().to_dict())
print("passResult por dropBackType nulo vs no nulo (proporciones):")
print(pd.crosstab(pl.dropBackType.isna(), pl.passResult, normalize="index").round(3).to_string())
print("jugadas por posesión==defensa:", int((pl.possessionTeam == pl.defensiveTeam).sum()))

titulo("players: casos raros")
bd = p.birthDate.astype("string")
print("birthDate con formato dd/dd/dddd (ejemplos):", bd[bd.str.contains("/", na=False)].head(6).tolist())
print("displayName repetidos (nflId distintos):")
dup = p[p.displayName.duplicated(keep=False)].sort_values("displayName")[["nflId", "displayName", "officialPosition", "collegeName", "birthDate"]]
print(dup.to_string())
print("weight describe:\n", p.weight.describe().to_string())
inch = p.height.str.split("-", expand=True).astype(int)
p["pulg"] = inch[0] * 12 + inch[1]
print("altura en pulgadas min/max:", int(p.pulg.min()), int(p.pulg.max()), "| inches>11 en formato pies-pulgadas:", int((inch[1] > 11).sum()))
print("nulos de birthDate/collegeName por posición (conteo de nulos):")
print(p.groupby("officialPosition")[["birthDate", "collegeName"]].agg(lambda s: int(s.isna().sum())).T.to_string())
print("peso por posición (min/max):")
print(p.groupby("officialPosition").weight.agg(["count", "min", "median", "max"]).to_string())

# ---------------- tracking
titulo("tracking: carga")
partes = []
for f in sorted((D / "tracking").glob("tracking_*.csv")):
    d = pd.read_csv(f, dtype={"gameId": "int32", "playId": "int32", "nflId": "Int32", "frameId": "int16", "team": "category",
                              "x": "float32", "y": "float32", "s": "float32", "a": "float32", "dis": "float32",
                              "event": "category", "time": "string", "playDirection": "category"},
                    usecols=["gameId", "playId", "nflId", "frameId", "time", "team", "playDirection", "x", "y", "s", "a", "dis", "event"],
                    keep_default_na=False, na_values=["NA"])
    d["sub_seg"] = d["time"].str.contains(".", regex=False)
    d["time"] = pd.to_datetime(d["time"], utc=True)
    partes.append(d)
t = pd.concat(partes, ignore_index=True)
del partes
t["es_balon"] = t["team"].astype(str) == "football"
print("filas:", len(t), flush=True)

titulo("rangos: ¿quién genera valores fuera de rango?")
for nombre, m in {"x fuera [0,120]": (t.x < 0) | (t.x > 120), "y fuera [0,53.3]": (t.y < 0) | (t.y > 53.3),
                  "s>14": t.s > 14, "a>15 o a<-15": (t.a > 15) | (t.a < -15), "dis>1.5": t.dis > 1.5}.items():
    print(f"{nombre}: total={int(m.sum())}  balón={int((m & t.es_balon).sum())}  jugadores={int((m & ~t.es_balon).sum())}")
J = t[~t.es_balon]
print("\nSOLO JUGADORES: cuantiles")
print(J[["x", "y", "s", "a", "dis"]].quantile([0, .001, .5, .99, .999, 1]).to_string())
print("jugadores: s>11:", int((J.s > 11).sum()), " a>10:", int((J.a > 10).sum()), " dis>1.2:", int((J.dis > 1.2).sum()))
print("jugadores fuera de [0,120]x[0,53.3]:", int(((J.x < 0) | (J.x > 120) | (J.y < 0) | (J.y > 53.3)).sum()),
      "| en jugadas distintas:", J.loc[(J.x < 0) | (J.x > 120) | (J.y < 0) | (J.y > 53.3), ["gameId", "playId"]].drop_duplicates().shape[0])
print("balón: fuera de [0,120]x[0,53.3]:", int((t.es_balon & ((t.x < 0) | (t.x > 120) | (t.y < 0) | (t.y > 53.3))).sum()))
print("consistencia dis ~ 0.1*s (jugadores): mediana de dis/(0.1*s) donde s>1:", float((J.dis[J.s > 1] / (0.1 * J.s[J.s > 1])).median()))

titulo("time: resolución")
print("filas con fracción de segundo en time (texto con '.'):", int(t.sub_seg.sum()))
fr = t.groupby(["gameId", "playId", "frameId"], observed=True).time.nunique()
print("frames con >1 valor de time entre sus 23 filas:", int((fr > 1).sum()))
fu = t.groupby(["gameId", "playId"], observed=True).agg(frames=("frameId", "max"), seg=("time", "nunique"))
print("jugadas con segundos únicos == frames (time distingue frames):", int((fu.frames == fu.seg).sum()), "de", len(fu))
print("razón frames/segundos únicos (mediana):", float((fu.frames / fu.seg).median()))

titulo("snap y pase: cobertura por jugada")
ev = t.loc[t.event.astype(str) != "None", ["gameId", "playId", "frameId", "event"]].drop_duplicates()
ev["event"] = ev["event"].astype(str)
snap = ev[ev.event.isin(["ball_snap", "autoevent_ballsnap"])]
snap_m = snap[snap.event == "ball_snap"]
pas = ev[ev.event.isin(["pass_forward", "autoevent_passforward"])]
pas_m = pas[pas.event == "pass_forward"]
idx = pl.set_index(["gameId", "playId"]).index
def cubre(df): return int(idx.isin(df.set_index(["gameId", "playId"]).index.unique()).sum())
print("jugadas con ball_snap:", cubre(snap_m), "| con ball_snap o autoevent:", cubre(snap), "| con ninguno:", len(pl) - cubre(snap))
print("jugadas con pass_forward:", cubre(pas_m), "| con pass_forward o autoevent:", cubre(pas), "| con ninguno:", len(pl) - cubre(pas))
print("jugadas con ball_snap Y autoevent_ballsnap a la vez:", len(set(map(tuple, snap_m[["gameId", "playId"]].values)) & set(map(tuple, snap[snap.event == "autoevent_ballsnap"][["gameId", "playId"]].values))))
w = pl.assign(pf=idx.isin(pas.set_index(["gameId", "playId"]).index.unique()))
print("jugadas SIN evento de pase, por passResult:\n", w[~w.pf].passResult.value_counts().to_string())
print("jugadas CON evento de pase, por passResult:\n", w[w.pf].passResult.value_counts().to_string())
s1 = snap.groupby(["gameId", "playId"]).frameId.min().rename("f_snap")
p1 = pas.groupby(["gameId", "playId"]).frameId.min().rename("f_pase")
fm = fu.frames.rename("f_max")
q = pd.concat([s1, p1, fm], axis=1)
q["pre_snap"] = q.f_snap - 1
q["snap_a_pase"] = q.f_pase - q.f_snap
q["post_pase"] = q.f_max - q.f_pase
print("frames antes del snap / snap->pase / después del pase (describe, frames):")
print(q[["pre_snap", "snap_a_pase", "post_pase"]].describe(percentiles=[.05, .5, .95]).round(1).to_string())
print("jugadas con snap_a_pase <= 0:", int((q.snap_a_pase <= 0).sum()), "| NaN:", int(q.snap_a_pase.isna().sum()))

titulo("equipos en tracking vs plays")
tt = t[~t.es_balon].groupby(["gameId", "playId"], observed=True).team.agg(lambda s: frozenset(s.astype(str).unique()))
pp = pl.set_index(["gameId", "playId"])
ok = (tt.reindex(pp.index) == pp.apply(lambda r: frozenset([r.possessionTeam, r.defensiveTeam]), axis=1))
print("jugadas donde equipos del tracking == {possessionTeam, defensiveTeam}:", int(ok.sum()), "de", len(pp))
print("filas por frame (jugadores+balón) distintas de 23:", int((t.groupby(["gameId", "playId", "frameId"], observed=True).size() != 23).sum()))
print("\nOK fin extra", flush=True)
