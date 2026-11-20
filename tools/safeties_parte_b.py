"""Parte B: viabilidad de la pregunta 'safeties se mueven antes del snap en Cover-3'.
SOLO conteos, ruido de medición y solapamiento de estratos. NO compara grupos ni estima efectos.
Salida: docs/safeties_parte_b_salida.txt.  Uso: .venv\\Scripts\\python tools\\safeties_parte_b.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
sys.stdout = open(ROOT / "docs" / "safeties_parte_b_salida.txt", "w", encoding="utf-8")
pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 200)

SAFE = {"FS", "FSL", "FSR", "SS", "SSL", "SSR"}
OL = {"C", "LG", "RG", "LT", "RT"}
VENT = 5  # frames antes del snap (hallazgo 2 de docs/datos.md)
K = ["gameId", "playId"]

pl = pd.read_csv(D / "plays.csv")
pf = pd.read_csv(D / "pffScoutingData.csv", na_values=["NA"])
saf = pf[(pf.pff_role == "Coverage") & pf.pff_positionLinedUp.isin(SAFE)][K + ["nflId", "pff_positionLinedUp"]]
ol = pf[(pf.pff_role == "Pass Block") & pf.pff_positionLinedUp.isin(OL)][K + ["nflId"]]
saf = saf.assign(grupo="safety")
ol = ol.assign(grupo="ol")
roles = pd.concat([saf[K + ["nflId", "grupo"]], ol[K + ["nflId", "grupo"]]])

filas, snaps, bola = [], [], []
for f in sorted((D / "tracking").glob("tracking_*.csv")):
    d = pd.read_csv(f, usecols=["gameId", "playId", "nflId", "frameId", "team", "x", "y", "event"],
                    dtype={"gameId": "int64", "playId": "int64", "frameId": "int32", "x": "float32", "y": "float32"})
    ev = d[d.event.isin(["ball_snap", "autoevent_ballsnap"])]
    s_man = ev[ev.event == "ball_snap"].groupby(K).frameId.min()
    s_aut = ev[ev.event == "autoevent_ballsnap"].groupby(K).frameId.min()
    snap = s_man.combine_first(s_aut).rename("f_snap")
    todas = d[K].drop_duplicates().set_index(K)
    snaps.append(todas.join(snap).reset_index())
    d = d.join(snap, on=K)
    d = d[d.f_snap.notna()]
    d = d[(d.frameId >= d.f_snap - VENT) & (d.frameId <= d.f_snap)]
    b = d[(d.team == "football") & (d.frameId == d.f_snap)][K + ["x", "y"]].rename(columns={"x": "bx", "y": "by"})
    bola.append(b)
    j = d[d.team != "football"].copy()
    j["nflId"] = j.nflId.astype("int64")
    j = j.merge(roles, on=K + ["nflId"], how="inner", validate="many_to_one")
    j = j.sort_values(K + ["nflId", "frameId"])
    j["dx"] = j.groupby(K + ["nflId"]).x.diff()
    j["dy"] = j.groupby(K + ["nflId"]).y.diff()
    j["paso"] = np.sqrt(j.dx ** 2 + j.dy ** 2)
    g = j.groupby(K + ["nflId", "grupo"]).agg(n_frames=("frameId", "size"), x0=("x", "first"), y0=("y", "first"),
                                                x1=("x", "last"), y1=("y", "last"), camino=("paso", "sum")).reset_index()
    filas.append(g)

snaps = pd.concat(snaps, ignore_index=True)
bola = pd.concat(bola, ignore_index=True)
J = pd.concat(filas, ignore_index=True).merge(bola, on=K, validate="many_to_one")
print("filas jugador-jugada con ventana incompleta (<6 frames) que se EXCLUYEN:", int((J.n_frames < VENT + 1).sum()),
      "| en jugadas:", J.loc[J.n_frames < VENT + 1, K].drop_duplicates().shape[0])
J = J[J.n_frames == VENT + 1].copy()
J["despl"] = np.sqrt((J.x1 - J.x0) ** 2 + (J.y1 - J.y0) ** 2)
J["prof"] = (J.x1 - J.bx).abs()  # distancia en x al balón en el snap (no depende del sentido de juego)

print("=" * 80, "\nVENTANA Y COBERTURA DEL SNAP\n", "=" * 80)
print("jugadas en tracking:", len(snaps), "| con snap (manual o auto):", int(snaps.f_snap.notna().sum()),
      "| sin snap:", int(snaps.f_snap.isna().sum()))
print("jugadas con snap en frame < 6 (no hay 5 frames previos):", int((snaps.f_snap < VENT + 1).sum()))
print("jugadas con snap en frame >= 6:", int((snaps.f_snap >= VENT + 1).sum()))
print("frames de ventana por jugador (n_frames):", J.n_frames.value_counts().to_dict())

print("\n", "=" * 80, "\nSAFETIES POR JUGADA (pff_role=Coverage y posición en", sorted(SAFE), ")\n", "=" * 80)
S = J[J.grupo == "safety"]
P = S.groupby(K).agg(n_saf=("nflId", "size"), max_desp=("despl", "max"), prof_max=("prof", "max"),
                     n_prof10=("prof", lambda s: int((s >= 10).sum()))).reset_index()
print("jugadas con >=1 safety y ventana completa:", len(P))
print("distribución de nº de safeties por jugada:", P.n_saf.value_counts().sort_index().to_dict())

print("\n", "=" * 80, "\nRUIDO DE MEDICIÓN (todas las jugadas juntas, sin separar por cobertura)\n", "=" * 80)
q = [.5, .9, .95, .99]
print("Desplazamiento neto en 5 frames, yardas [CALCULADO] (linieros ofensivos = referencia casi inmóvil):")
print(pd.DataFrame({"OL": J[J.grupo == "ol"].despl.quantile(q), "safeties": S.despl.quantile(q)}).round(2).to_string())
print("n filas jugador-jugada: OL", int((J.grupo == "ol").sum()), "| safeties", len(S))
print("Camino recorrido en 5 frames (yardas):")
print(pd.DataFrame({"OL": J[J.grupo == "ol"].camino.quantile(q), "safeties": S.camino.quantile(q)}).round(2).to_string())
for dl in [0.5, 1, 2, 3]:
    print(f"safeties con desplazamiento > {dl} yd: {int((S.despl > dl).sum())} de {len(S)} | OL con > {dl} yd: {int((J[J.grupo=='ol'].despl > dl).sum())} de {int((J.grupo=='ol').sum())}")

print("\n", "=" * 80, "\nTAMAÑO DE GRUPOS POR COBERTURA\n", "=" * 80)
W = pl.merge(P, on=K, how="left", validate="one_to_one")
W["valida"] = W.n_saf.notna() & (W.down != 0)
tab = W.groupby(["pff_passCoverage", "pff_passCoverageType"]).agg(
    jugadas_sin_2pt=("down", lambda s: int((s != 0).sum())), validas=("valida", "sum"),
    partidos=("gameId", lambda s: s[W.loc[s.index, "valida"]].nunique()),
    equipos_def=("defensiveTeam", lambda s: s[W.loc[s.index, "valida"]].nunique())).reset_index()
print(tab.to_string(index=False))
print("TOTAL válidas:", int(W.valida.sum()), "de", int((W.down != 0).sum()), "jugadas sin 2pt")
print("Pérdida por ventana/snap/safeties:", int((W.down != 0).sum() - W.valida.sum()))

V = W[W.valida].copy()
V["c3"] = (V.pff_passCoverage == "Cover-3").astype(int)
zona_otra = {"Cover-2", "Quarters", "Cover-6"}
V["comparador"] = np.where(V.pff_passCoverage == "Cover-3", "Cover-3",
                           np.where(V.pff_passCoverage == "Cover-1", "Cover-1",
                                    np.where(V.pff_passCoverage.isin(zona_otra), "Otra zona (C2/C4/C6)", "Otra (0, 2-Man, situacional)")))
print("\nGrupos candidatos (jugadas válidas):")
print(V.comparador.value_counts().to_string())
print("\nCover-3 válidas: partidos", V[V.c3 == 1].gameId.nunique(), "| equipos defensivos", V[V.c3 == 1].defensiveTeam.nunique(),
      "| jugadas por equipo defensivo (min/mediana/max):",
      V[V.c3 == 1].groupby("defensiveTeam").size().agg(["min", "median", "max"]).tolist())

print("\n", "=" * 80, "\nFORMACIÓN DE LA 'CÁSCARA' AL SNAP: nº de safeties a >=10 yd del balón (n_prof10) por cobertura (conteos)\n", "=" * 80)
print(pd.crosstab(V.pff_passCoverage, V.n_prof10).to_string())

print("\n", "=" * 80, "\nSUBGRUPOS DENTRO DE COVER-3 SEGÚN UMBRAL DE MOVIMIENTO (max desplazamiento de un safety)\n", "=" * 80)
C3 = V[V.c3 == 1]
for dl in [0.5, 1, 2, 3]:
    m = C3.max_desp > dl
    print(f"umbral {dl} yd: movió n={int(m.sum())} | no movió n={int((~m).sum())} | equipos def. con >=1 movió: {C3[m].defensiveTeam.nunique()} | partidos: {C3[m].gameId.nunique()}")

print("\n", "=" * 80, "\nSOLAPAMIENTO DE ESTRATOS (solo conteos; regla de stratified_comparison: >=5 por brazo)\n", "=" * 80)
V["form3"] = V.offenseFormation.where(V.offenseFormation.isin(["SHOTGUN", "EMPTY", "SINGLEBACK"]), "OTRA")
V["ytg"] = pd.cut(V.yardsToGo, [-1, 3, 7, 100], labels=["1-3", "4-7", "8+"])
V["zona_campo"] = pd.cut(V.absoluteYardlineNumber, [-1, 20, 90, 120], labels=["rojo_def(<=20)", "medio", "zona_roja_of(>90)"])


def solap(df, treat, estratos, etiqueta, min_arm=5):
    d = df.dropna(subset=estratos + [treat])
    t = d.groupby(estratos, observed=True)[treat].agg(n1="sum", n=lambda s: len(s)).reset_index()
    t["n0"] = t.n - t.n1
    ok = (t.n1 >= min_arm) & (t.n0 >= min_arm)
    print(f"{etiqueta} | estratos={estratos}: celdas={len(t)}, usables={int(ok.sum())}, "
          f"filas excluidas={int(t.loc[~ok, 'n'].sum())} de {int(t.n.sum())} ({100 * t.loc[~ok, 'n'].sum() / t.n.sum():.1f}%), "
          f"n1 usado={int(t.loc[ok, 'n1'].sum())} n0 usado={int(t.loc[ok, 'n0'].sum())}")


for comp in ["Cover-1", "Otra zona (C2/C4/C6)"]:
    sub = V[V.comparador.isin(["Cover-3", comp])].copy()
    sub["t"] = sub.c3
    print(f"\n--- Cover-3 (1) vs {comp} (0): n1={int(sub.t.sum())}, n0={int((1 - sub.t).sum())}")
    solap(sub, "t", ["down"], "estr. down", 5)
    solap(sub, "t", ["down", "form3"], "estr. down x formación", 5)
    solap(sub, "t", ["down", "form3", "ytg"], "estr. down x formación x yardas", 5)
    solap(sub, "t", ["down", "form3", "ytg", "zona_campo"], "estr. ... x zona", 5)
C3 = V[V.c3 == 1].copy()
C3["t"] = (C3.max_desp > 1).astype(int)
print("\n--- Dentro de Cover-3: 'movió > 1 yd' (1) vs 'no movió' (0): n1=", int(C3.t.sum()), "n0=", int((1 - C3.t).sum()))
solap(C3, "t", ["down"], "estr. down", 5)
solap(C3, "t", ["down", "form3"], "estr. down x formación", 5)
solap(C3, "t", ["down", "form3", "ytg"], "estr. down x formación x yardas", 5)

print("\n", "=" * 80, "\nRESULTADO (variable de desenlace): conteos disponibles en Cover-3 válidas\n", "=" * 80)
print("passResult:", C3.passResult.value_counts().to_dict())
print("jugadas con dropBackType nulo:", int(C3.dropBackType.isna().sum()))
print("\nOK fin")
sys.stdout.close()
