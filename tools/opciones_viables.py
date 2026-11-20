"""Viabilidad de 3 opciones (solo conteos, ruido y solapamiento; NO compara grupos ni estima efectos).
  1) Presión: distancia rusher-QB entre snap y pase/sack.
  2) Separación del receptor objetivo al soltar (objetivo inferido de playDescription).
  3) Rotación de safeties entre el snap y el pase.
Salida: docs/opciones_viables_salida.txt   Uso: .venv\\Scripts\\python tools\\opciones_viables.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
sys.stdout = open(ROOT / "docs" / "opciones_viables_salida.txt", "w", encoding="utf-8")
pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 200)
K = ["gameId", "playId"]
SAFE = {"FS", "FSL", "FSR", "SS", "SSL", "SSR"}
PROF = 10.0  # yardas desde el balón al snap para llamar "profundo" a un safety [SUPUESTO]
RAD = 2.0    # yardas rusher-QB para llamar "presión" [SUPUESTO]


def tit(t):
    print("\n" + "=" * 90 + f"\n{t}\n" + "=" * 90)


pl = pd.read_csv(D / "plays.csv")
pf = pd.read_csv(D / "pffScoutingData.csv", na_values=["NA"])
pla = pd.read_csv(D / "players.csv")

# descripción -> objetivo (inicial, apellido normalizado)
m = pl.playDescription.str.extract(r"\bto ([A-Z])\.(?:[A-Z]\.)?\s?([A-Za-z'\-]+)")
pl["tgt_ini"] = m[0].str.lower()
pl["tgt_last"] = m[1].str.lower().str.replace(r"[^a-z]", "", regex=True)


def _last(n):
    t = re.sub(r"[^A-Za-z' \-]", "", n).split()
    return re.sub(r"[^a-z]", "", (t[1] if len(t) >= 2 else t[0]).lower())


pla["oi"] = pla.displayName.str[0].str.lower()
pla["ol"] = pla.displayName.map(_last)
pl["form3"] = pl.offenseFormation.where(pl.offenseFormation.isin(["SHOTGUN", "EMPTY", "SINGLEBACK"]), "OTRA")
pl["ytg"] = pd.cut(pl.yardsToGo, [-1, 3, 7, 100], labels=["1-3", "4-7", "8+"])

qb = pf[pf.pff_role == "Pass"][K + ["nflId"]]
rush = pf[pf.pff_role == "Pass Rush"][K + ["nflId"]]
saf = pf[(pf.pff_role == "Coverage") & pf.pff_positionLinedUp.isin(SAFE)][K + ["nflId"]]
nr = rush.groupby(K).size().rename("n_rush")
pres_pff = (pf[pf.pff_role == "Pass Rush"].assign(p=lambda x: ((x.pff_hit.fillna(0) + x.pff_hurry.fillna(0) + x.pff_sack.fillna(0)) > 0))
            .groupby(K).p.max().rename("pres_pff"))

FRL, R1, R2, R3, ST2 = [], [], [], [], []
for f in sorted((D / "tracking").glob("tracking_*.csv")):
    d = pd.read_csv(f, usecols=["gameId", "playId", "nflId", "frameId", "team", "x", "y", "event"],
                    dtype={"gameId": "int64", "playId": "int64", "frameId": "int32", "x": "float32", "y": "float32"})

    def ff(evs):
        return d[d.event.isin(evs)].groupby(K).frameId.min()

    fr = d.groupby(K).frameId.max().rename("f_last").to_frame()
    for nm, evs in [("sm", ["ball_snap"]), ("sa", ["autoevent_ballsnap"]), ("pm", ["pass_forward"]),
                    ("pa", ["autoevent_passforward"]), ("fk", ["qb_sack", "qb_strip_sack"])]:
        fr = fr.join(ff(evs).rename(nm))
    fr["f_snap"] = fr.sm.fillna(fr.sa)
    fr["f_pase"] = fr.pm.fillna(fr.pa)
    fr["f_end"] = fr.f_pase.fillna(fr.fk).fillna(fr.f_last)
    fr["src_end"] = np.where(fr.f_pase.notna(), "pase", np.where(fr.fk.notna(), "sack", "ultimo_frame"))
    fr = fr[["f_snap", "f_pase", "f_end", "src_end"]]
    FRL.append(fr.reset_index())

    ball = d[d.team == "football"].join(fr[["f_snap"]], on=K)
    ball = ball[ball.frameId == ball.f_snap][K + ["x"]].rename(columns={"x": "bx"})
    P = d[d.team != "football"].copy()
    P["nflId"] = P.nflId.astype("int64")
    P = P.join(fr[["f_snap", "f_pase", "f_end"]], on=K)

    # ---------- 1) presión
    w = P[P.f_snap.notna() & (P.frameId >= P.f_snap) & (P.frameId <= P.f_end)]
    q = w.merge(qb, on=K + ["nflId"])[K + ["frameId", "x", "y"]].rename(columns={"x": "qx", "y": "qy"})
    r = w.merge(rush, on=K + ["nflId"])[K + ["frameId", "nflId", "x", "y"]]
    mm = r.merge(q, on=K + ["frameId"])
    mm["dist"] = np.hypot(mm.x - mm.qx, mm.y - mm.qy)
    g = mm.groupby(K + ["frameId"]).dist.min().rename("mind").reset_index().join(fr[["f_snap", "f_end"]], on=K)
    g["rel"] = g.frameId - g.f_snap
    a = g.groupby(K).agg(mind_min=("mind", "min"), n_fr=("frameId", "size"))
    b = g[g.frameId == g.f_end].set_index(K).mind.rename("mind_end")
    c = g[g.mind <= RAD].groupby(K).rel.min().rename("t_presion")
    R1.append(a.join(b).join(c).reset_index())

    # ---------- 3) rotación de safeties
    s = P.merge(saf, on=K + ["nflId"])
    s = s[(s.frameId == s.f_snap) | (s.frameId == s.f_pase)].merge(ball, on=K)
    s["prof"] = (s.x - s.bx).abs()
    s["es_snap"] = s.frameId == s.f_snap
    s["deep"] = s.prof >= PROF
    r3 = s.groupby(K).apply(lambda z: pd.Series({
        "n_saf": int(z.es_snap.sum()),
        "deep_snap": int((z.es_snap & z.deep).sum()),
        "deep_pase": int((~z.es_snap & z.deep).sum()) if z.f_pase.notna().any() else np.nan,
        "n_saf_pase": int((~z.es_snap).sum())}), include_groups=False)
    R3.append(r3.reset_index())

    # ---------- 2) separación del objetivo
    pp = P[P.f_pase.notna() & (P.frameId == P.f_pase)].merge(
        pl[K + ["possessionTeam", "defensiveTeam", "tgt_ini", "tgt_last"]], on=K, validate="many_to_one")
    off = pp[pp.team == pp.possessionTeam].merge(pla[["nflId", "oi", "ol", "officialPosition"]], on="nflId", how="left")
    dfn = pp[pp.team == pp.defensiveTeam][K + ["x", "y"]].rename(columns={"x": "dx", "y": "dy"})
    qbm = qb.assign(is_qb=1)
    off = off.merge(qbm, on=K + ["nflId"], how="left")
    qpos = off[off.is_qb == 1][K + ["x"]].rename(columns={"x": "qx"})
    cand = off[(off.is_qb != 1) & (off.oi == off.tgt_ini) & (off.ol == off.tgt_last)]
    nmatch = cand.groupby(K).size().rename("n_match").reset_index()
    ST2.append(nmatch)
    tg = cand.merge(nmatch, on=K)
    tg = tg[tg.n_match == 1][K + ["nflId", "x", "y", "officialPosition"]].rename(columns={"nflId": "tgt_id", "x": "tx", "y": "ty"})
    dd = tg.merge(dfn, on=K)
    dd["dist"] = np.hypot(dd.tx - dd.dx, dd.ty - dd.dy)
    sep = dd.groupby(K).dist.min().rename("sep").reset_index()
    R2.append(tg.merge(sep, on=K).merge(qpos, on=K, how="left"))

FR = pd.concat(FRL, ignore_index=True)
R1 = pd.concat(R1, ignore_index=True)
R2 = pd.concat(R2, ignore_index=True)
R3 = pd.concat(R3, ignore_index=True)
NM = pd.concat(ST2, ignore_index=True)

V = pl[pl.down != 0].merge(FR, on=K, how="left", validate="one_to_one")
print("jugadas totales:", len(pl), "| sin 2pt:", len(V))


def solap(df, treat, estratos, etiqueta, min_arm=5):
    dd_ = df.dropna(subset=estratos + [treat])
    t = dd_.groupby(estratos, observed=True)[treat].agg(n1="sum", n="size").reset_index()
    t["n0"] = t.n - t.n1
    ok = (t.n1 >= min_arm) & (t.n0 >= min_arm)
    print(f"   {etiqueta}: celdas={len(t)}, usables={int(ok.sum())}, filas excluidas={int(t.loc[~ok, 'n'].sum())} de {int(t.n.sum())}, "
          f"n1 usado={int(t.loc[ok, 'n1'].sum())}, n0 usado={int(t.loc[ok, 'n0'].sum())}")


# =========================================================== 1) PRESIÓN
tit("OPCIÓN 1: PRESIÓN (distancia rusher-QB, snap -> pase/sack)")
A = V.merge(nr.reset_index(), on=K, how="left").merge(R1, on=K, how="left").merge(pres_pff.reset_index(), on=K, how="left")
A["n_rush"] = A.n_rush.fillna(0).astype(int)
A["dur"] = A.f_end - A.f_snap
ok1 = A.f_snap.notna() & A.mind_min.notna() & (A.dur > 0)
print("jugadas con snap, QB y >=1 rusher medidos, dur>0:", int(ok1.sum()), "de", len(A))
B = A[ok1].copy()
print("\nCómo termina la ventana (src_end) por passResult (n jugadas):")
print(pd.crosstab(B.src_end, B.passResult).to_string())
print("\nDuración snap->fin (frames; 10 fps [SUPUESTO]) cuantiles pooled:", B.dur.quantile([.05, .25, .5, .75, .95]).round(0).to_dict())
print("n_rush (pff_role=Pass Rush) por jugada:", B.n_rush.value_counts().sort_index().to_dict())
B["g_rush"] = np.select([B.n_rush <= 3, B.n_rush == 4], ["<=3", "4"], default="5+")
print("\nGrupos: ", B.g_rush.value_counts().to_dict())
print("Evento 'rusher a <=2 yd del QB antes del fin' (conteos) por grupo:")
B["evento"] = B.t_presion.notna().astype(int)
print(B.groupby("g_rush").agg(n=("evento", "size"), eventos=("evento", "sum"), partidos=("gameId", "nunique"), equipos_of=("possessionTeam", "nunique")).to_string())
print("\nCobertura tipo x grupo de rushers (conteos):")
print(pd.crosstab(B.pff_passCoverageType, B.g_rush).to_string())
print("\nPresión PFF (algún hit/hurry/sack) por grupo (conteos):")
print(pd.crosstab(B.g_rush, B.pres_pff.fillna(False)).to_string())
print("\nValidación pooled: evento medido vs presión PFF (conteos):")
print(pd.crosstab(B.evento, B.pres_pff.fillna(False)).to_string())
print("\nDistancia mínima rusher-QB al fin de ventana (yd), cuantiles pooled:", B.mind_end.quantile([.05, .5, .95]).round(2).to_dict())
for lab, t in [("5+ rushers (1) vs 4 (0)", B[B.g_rush.isin(["5+", "4"])].assign(t=lambda x: (x.g_rush == "5+").astype(int)))]:
    print("\nSolapamiento", lab, "n1=", int(t.t.sum()), "n0=", int((1 - t.t).sum()))
    solap(t, "t", ["down"], "estr. down")
    solap(t, "t", ["down", "form3"], "estr. down x formación")
    solap(t, "t", ["down", "form3", "ytg"], "estr. down x formación x yardas")
    solap(t, "t", ["down", "form3", "ytg", "pff_passCoverageType"], "estr. ... x tipo cobertura")

# =========================================================== 2) SEPARACIÓN
tit("OPCIÓN 2: SEPARACIÓN DEL RECEPTOR OBJETIVO AL SOLTAR")
E = V[V.passResult.isin(["C", "I", "IN"])].copy()
print("pases C/I/IN (sin 2pt):", len(E), E.passResult.value_counts().to_dict())
print("playDescription con patrón ' to X.Apellido':", int(E.tgt_last.notna().sum()), "| sin patrón:", int(E.tgt_last.isna().sum()))
E = E.merge(NM, on=K, how="left")
E["n_match"] = E.n_match.fillna(0).astype(int)
E.loc[E.f_pase.isna(), "n_match"] = -1
print("coincidencia con jugadores ofensivos en el frame del pase (n_match): ", E.n_match.value_counts().sort_index().to_dict(),
      "(-1 = sin evento de pase; 0 = sin coincidencia; 1 = único; >1 = ambiguo)")
C2 = E.merge(R2, on=K, how="inner", validate="one_to_one")
C2["prof_air"] = (C2.tx - C2.qx).abs()
C2["prof_cat"] = pd.cut(C2.prof_air, [-1, 5, 15, 200], labels=["<=5", "5-15", ">15"])
C2["completo"] = (C2.passResult == "C").astype(int)
print("\nANÁLISIS: pases con objetivo único y separación medida:", len(C2), "de", len(E), "pases C/I/IN")
print("por passResult:", C2.passResult.value_counts().to_dict(), "| partidos:", C2.gameId.nunique(), "| equipos defensivos:", C2.defensiveTeam.nunique())
print("\nSeparación (yd) cuantiles pooled:", C2.sep.quantile([.05, .25, .5, .75, .95]).round(2).to_dict())
print("\nPosición del objetivo (officialPosition):", C2.officialPosition.value_counts().to_dict())
print("\ntipo cobertura x completo (conteos):")
print(pd.crosstab(C2.pff_passCoverageType, C2.completo).to_string())
print("\nprofundidad x completo (conteos):")
print(pd.crosstab(C2.prof_cat, C2.completo).to_string())
print("\nSolapamiento completo (1) vs no completo (0):")
solap(C2, "completo", ["pff_passCoverageType"], "estr. tipo cobertura")
solap(C2, "completo", ["pff_passCoverageType", "prof_cat"], "estr. tipo cobertura x profundidad")
solap(C2, "completo", ["pff_passCoverageType", "prof_cat", "down"], "estr. ... x down")
qn = C2.merge(qb.rename(columns={"nflId": "qb_id"}).merge(R2[K].drop_duplicates(), on=K), on=K, how="left")
cnt = qn.groupby("qb_id").size()
print("\nQBs con >=1 pase analizable:", len(cnt), "| con >=30:", int((cnt >= 30).sum()), "| con >=100:", int((cnt >= 100).sum()),
      "| máx:", int(cnt.max()), "| mediana:", float(cnt.median()))
rc = C2.groupby("tgt_id").size()
print("Objetivos distintos:", len(rc), "| con >=30 blancos:", int((rc >= 30).sum()), "| con >=50:", int((rc >= 50).sum()), "| máx:", int(rc.max()))

# =========================================================== 3) ROTACIÓN
tit("OPCIÓN 3: ROTACIÓN DE SAFETIES ENTRE EL SNAP Y EL PASE")
H = V.merge(R3, on=K, how="inner", validate="one_to_one")
print("jugadas con >=1 safety medido al snap:", len(H), "| con evento de pase (deep_pase medido):", int(H.deep_pase.notna().sum()))
H = H[H.deep_pase.notna() & H.f_snap.notna() & (H.n_saf_pase == H.n_saf)].copy()
print("ANÁLISIS: con snap, pase, y mismos safeties en ambos frames:", len(H))
H["dur_sp"] = H.f_pase - H.f_snap
print("frames snap->pase cuantiles:", H.dur_sp.quantile([.05, .25, .5, .75, .95]).round(0).to_dict())
print("nº de safeties:", H.n_saf.value_counts().sort_index().to_dict())
print("\nCáscara al snap (nº de safeties a >=10 yd del balón):", H.deep_snap.value_counts().sort_index().to_dict())
print("\nTransición cáscara snap (filas) x cáscara al pase (columnas), conteos:")
print(pd.crosstab(H.deep_snap, H.deep_pase).to_string())
H["rota"] = (H.deep_pase != H.deep_snap).astype(int)
H["shell"] = np.select([H.deep_snap == 2, H.deep_snap == 1], ["2-alto", "1-alto"], default="otra")
print("\nGrupos por cáscara al snap, con eventos 'cambió nº de safeties profundos' (conteos):")
print(H.groupby("shell").agg(n=("rota", "size"), cambios=("rota", "sum"), partidos=("gameId", "nunique"), equipos_def=("defensiveTeam", "nunique")).to_string())
print("\nCobertura PFF x cáscara al snap (conteos):")
print(pd.crosstab(H.pff_passCoverage, H.shell).to_string())
t3 = H[H.shell.isin(["2-alto", "1-alto"])].assign(t=lambda x: (x.shell == "2-alto").astype(int))
print("\nSolapamiento 2-alto (1) vs 1-alto (0): n1=", int(t3.t.sum()), "n0=", int((1 - t3.t).sum()))
solap(t3, "t", ["down"], "estr. down")
solap(t3, "t", ["down", "form3"], "estr. down x formación")
solap(t3, "t", ["down", "form3", "ytg"], "estr. down x formación x yardas")
solap(t3, "t", ["down", "form3", "ytg", "pff_playAction"], "estr. ... x play action")
pe = t3.groupby("defensiveTeam").size()
print("Jugadas por equipo defensivo (min/mediana/max):", pe.agg(["min", "median", "max"]).tolist())
print("\nOK fin")
sys.stdout.close()
