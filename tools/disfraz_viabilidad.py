"""Viabilidad del 'Índice de disfraz defensivo' ampliado a línea, linebackers y corners.
Solo conteos y distribuciones (NO compara grupos ni estima efectos).
Usa 2 frames por jugada: snap y pase. Salida: docs/disfraz_viabilidad_salida.txt
Uso: .venv\\Scripts\\python tools\\disfraz_viabilidad.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
OUT = ROOT / "docs" / "disfraz_viabilidad_salida.txt"
sys.stdout = open(OUT, "w", encoding="utf-8")
sys.stderr = sys.stdout
print("version 2 (con filtro lateral y signo por playDirection)", flush=True)
pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 300)
K = ["gameId", "playId"]

GRUPO = {}
for p in ["DLT", "DRT", "NT", "NLT", "NRT", "LE", "RE", "LEO", "REO"]:
    GRUPO[p] = "DL"
for p in ["LOLB", "ROLB", "LILB", "RILB", "LLB", "RLB", "MLB"]:
    GRUPO[p] = "LB"
for p in ["LCB", "RCB", "SCBL", "SCBR", "SCBiL", "SCBiR", "SCBoL", "SCBoR"]:
    GRUPO[p] = "CB"
for p in ["FS", "FSL", "FSR", "SS", "SSL", "SSR"]:
    GRUPO[p] = "S"


def tit(t):
    print("\n" + "=" * 90 + f"\n{t}\n" + "=" * 90, flush=True)


pl = pd.read_csv(D / "plays.csv")
pf = pd.read_csv(D / "pffScoutingData.csv", na_values=["NA"])
defn = pf[pf.pff_role.isin(["Coverage", "Pass Rush"])][K + ["nflId", "pff_role", "pff_positionLinedUp"]].copy()
defn["grupo"] = defn.pff_positionLinedUp.map(GRUPO).fillna("OTRO")
recs = pf[pf.pff_role == "Pass Route"][K + ["nflId"]]

FR = []
for f in sorted((D / "tracking").glob("tracking_*.csv")):
    d = pd.read_csv(f, usecols=["gameId", "playId", "nflId", "frameId", "team", "playDirection", "x", "y", "event"],
                    dtype={"gameId": "int64", "playId": "int64", "frameId": "int32", "x": "float32", "y": "float32"})

    def ff(e):
        return d[d.event == e].groupby(K).frameId.min()

    fr = pd.concat([ff("ball_snap"), ff("autoevent_ballsnap"), ff("pass_forward"), ff("autoevent_passforward")], axis=1)
    fr.columns = ["sm", "sa", "pm", "pa"]
    fr["f_snap"] = fr.sm.fillna(fr.sa)
    fr["f_pase"] = fr.pm.fillna(fr.pa)
    fr = fr[["f_snap", "f_pase"]]
    d = d.join(fr, on=K)
    ball = d[(d.team == "football") & (d.frameId == d.f_snap)][K + ["x", "y"]].rename(columns={"x": "bx", "y": "by"})
    pj = d[(d.team != "football") & ((d.frameId == d.f_snap) | (d.frameId == d.f_pase))].copy()
    pj["nflId"] = pj.nflId.astype("int64")
    pj["cuando"] = np.where(pj.frameId == pj.f_snap, "snap", "pase")
    pj = pj.merge(ball, on=K)
    # receptores al snap (para distancia corner-receptor)
    rr = pj[pj.cuando == "snap"].merge(recs, on=K + ["nflId"])[K + ["x", "y"]].rename(columns={"x": "rx", "y": "ry"})
    dd = pj.merge(defn, on=K + ["nflId"], validate="many_to_one")
    ds = dd[dd.cuando == "snap"][K + ["nflId", "x", "y", "bx", "by"]]
    cr = ds.merge(rr, on=K)
    cr["dr"] = np.hypot(cr.x - cr.rx, cr.y - cr.ry)
    near = cr.groupby(K + ["nflId"]).dr.min().rename("dist_rec_snap").reset_index()
    wide = dd.pivot_table(index=K + ["nflId", "bx", "by", "playDirection"], columns="cuando", values="x").reset_index()
    ysnap = ds.set_index(K + ["nflId"]).y.rename("y_snap").reset_index()
    wide = wide.merge(near, on=K + ["nflId"], how="left").merge(ysnap, on=K + ["nflId"], how="left")
    FR.append(wide)

T = pd.concat(FR, ignore_index=True).merge(defn, on=K + ["nflId"], validate="one_to_one")
T["prof_snap"] = (T.snap - T.bx).abs()      # yardas detrás de la línea de golpeo al snap
T["prof_pase"] = (T.pase - T.bx).abs()
T["lat_snap"] = (T.y_snap - T.by).abs()     # yardas a lo ancho desde el balón al snap
SGN = np.where(T.playDirection == "right", 1.0, -1.0)  # ofensiva avanza hacia +x si 'right' [SUPUESTO, ver docs/datos.md #6]
T["prof_signo_snap"] = (T.snap - T.bx) * SGN     # >0 = del lado defensivo
T["retro_signo"] = (T.pase - T.snap) * SGN       # >0 = se aleja de la ofensiva (retrocede)
T = T.merge(pl[K + ["down", "defensiveTeam", "passResult", "pff_passCoverage", "pff_passCoverageType"]], on=K, validate="many_to_one")
T = T[T.down != 0]
T["rush"] = (T.pff_role == "Pass Rush").astype(int)
print("filas defensor-jugada con posición al snap:", int(T.snap.notna().sum()), "| jugadas:", T[K].drop_duplicates().shape[0])
print("filas por grupo:", T.grupo.value_counts().to_dict())

tit("A) ¿QUIÉN ATACA? rol PFF por grupo (conteos de defensor-jugada)")
print(pd.crosstab(T.grupo, T.pff_role).to_string())

tit("B) PROFUNDIDAD AL SNAP (yd desde el balón) por grupo y rol: cuantiles")
q = T.groupby(["grupo", "pff_role"]).prof_snap.quantile([.05, .25, .5, .75, .95]).unstack().round(2)
q["n"] = T.groupby(["grupo", "pff_role"]).size()
print(q.to_string())

tit("B2) VERIFICACIÓN DEL SIGNO: profundidad con signo al snap (>0 = lado defensivo) por grupo")
print(T.groupby("grupo").prof_signo_snap.quantile([.01, .05, .5, .95]).unstack().round(2).to_string())
print("filas con prof_signo_snap < -1 (defensor del lado ofensivo al snap):", int((T.prof_signo_snap < -1).sum()), "de", int(T.prof_signo_snap.notna().sum()))

tit("C) FRENTE: defensores 'mostrando presión' al snap (prof <= U y a lo ancho <= L del balón) vs rol real")
for U, L in [(2.0, 6.0), (2.0, 8.0), (3.0, 8.0), (2.0, 10.0)]:
    T["en_linea"] = ((T.prof_snap <= U) & (T.lat_snap <= L)).astype(int)
    print(f"\n-- U = {U} yd de profundidad, L = {L} yd a lo ancho --")
    print(pd.crosstab([T.grupo], [T.en_linea, T.pff_role]).to_string())
U, L = 2.0, 8.0
T["en_linea"] = ((T.prof_snap <= U) & (T.lat_snap <= L)).astype(int)
J = T.groupby(K).agg(n_muestra=("en_linea", "sum"), n_rush=("rush", "sum"),
                     muestra_y_cae=("en_linea", lambda s: int(((s == 1) & (T.loc[s.index, "rush"] == 0)).sum())),
                     oculto_ataca=("en_linea", lambda s: int(((s == 0) & (T.loc[s.index, "rush"] == 1)).sum())),
                     defensiveTeam=("defensiveTeam", "first"), passResult=("passResult", "first"),
                     cov=("pff_passCoverageType", "first")).reset_index()
print(f"\nPor jugada (U={U}, L={L}): jugadas={len(J)}")
print("n que muestran (en la línea):", J.n_muestra.value_counts().sort_index().to_dict())
print("n que atacan (PFF):", J.n_rush.value_counts().sort_index().to_dict())
print("jugadas con >=1 'muestra y cae':", int((J.muestra_y_cae >= 1).sum()), "| con >=1 'oculto que ataca':", int((J.oculto_ataca >= 1).sum()),
      "| con ambos (presión simulada) :", int(((J.muestra_y_cae >= 1) & (J.oculto_ataca >= 1)).sum()))
print("muestra >=5 y ataca <=4 (amenaza de blitz sin blitz):", int(((J.n_muestra >= 5) & (J.n_rush <= 4)).sum()))
print("muestra <=4 y ataca >=5 (blitz escondido):", int(((J.n_muestra <= 4) & (J.n_rush >= 5)).sum()))
pe = J.groupby("defensiveTeam").agg(n=("n_rush", "size"), mc=("muestra_y_cae", lambda s: int((s >= 1).sum())), oa=("oculto_ataca", lambda s: int((s >= 1).sum())))
print("por equipo defensivo (min/mediana/max): n", pe.n.agg(["min", "median", "max"]).tolist(),
      "| jugadas 'muestra y cae'", pe.mc.agg(["min", "median", "max"]).tolist(), "| 'oculto ataca'", pe.oa.agg(["min", "median", "max"]).tolist())

tit("D) CORNERS (LCB/RCB/SCB*): profundidad y distancia al receptor más cercano al snap, por Man/Zone")
C = T[T.grupo == "CB"].copy()
print("filas CB:", len(C), "| con rol Coverage:", int((C.pff_role == "Coverage").sum()))
C = C[C.pff_role == "Coverage"]
print("profundidad al snap por tipo de cobertura (cuantiles):")
print(C.groupby("pff_passCoverageType").prof_snap.quantile([.1, .25, .5, .75, .9]).unstack().round(2).assign(n=C.groupby("pff_passCoverageType").size()).to_string())
print("distancia al receptor más cercano al snap por tipo de cobertura (cuantiles):")
print(C.groupby("pff_passCoverageType").dist_rec_snap.quantile([.1, .25, .5, .75, .9]).unstack().round(2).to_string())
for P in [2.0, 3.0]:
    C["press"] = (C.prof_snap <= P).astype(int)
    print(f"\npress (prof <= {P} yd) x tipo de cobertura (conteos CB-jugada):")
    print(pd.crosstab(C.press, C.pff_passCoverageType).to_string())
print("\nCB-jugada sin distancia a receptor (sin receptor medido):", int(C.dist_rec_snap.isna().sum()))

tit("E) RETROCESO CON SIGNO entre snap y pase (>0 = se aleja de la ofensiva) por grupo y rol")
r = T.dropna(subset=["retro_signo"]).groupby(["grupo", "pff_role"]).retro_signo.quantile([.1, .5, .9]).unstack().round(2)
r["n"] = T.dropna(subset=["retro_signo"]).groupby(["grupo", "pff_role"]).size()
print(r.to_string())
print("\nOK fin", flush=True)
sys.stdout.close()
