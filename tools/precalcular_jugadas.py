"""Precalcula UNA fila por jugada: lo que la defensa MUESTRA al snap (tracking) y lo que JUEGA (PFF).

Lee data/ (solo lectura) y escribe backend/datos/jugadas_disfraz.csv (~8.5k filas, < 1 MB).
La API (backend/main.py) carga ese archivo al arrancar; así no lee 825 MB de tracking en cada arranque
y funciona aunque data/ no esté (data/ no va al repo público).

Uso (desde la raíz del proyecto, ~4 min):
    .venv\\Scripts\\python tools\\precalcular_jugadas.py
Bitácora con conteos de control: docs/precalculo_salida.txt
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
OUT = ROOT / "backend" / "datos" / "jugadas_disfraz.csv"
LOG = ROOT / "docs" / "precalculo_salida.txt"
K = ["gameId", "playId"]
SAFE = {"FS", "FSL", "FSR", "SS", "SSL", "SSR"}
# [SUPUESTO] umbrales (ver PLAN.md, Registro). El primero es el principal; el resto, sensibilidad.
LINEA = [(2.0, 8.0), (3.0, 8.0), (2.0, 6.0), (2.0, 10.0)]   # (profundidad, ancho) en yardas
PROF_SAFETY = [10.0, 8.0, 12.0]                              # yardas desde el balón


def col_linea(u: float, l: float) -> str:
    return f"n_linea_u{u:g}_l{l:g}"


def col_prof(p: float) -> str:
    return f"n_saf_prof{p:g}"


def main() -> None:
    t0 = time.time()
    log = open(LOG, "w", encoding="utf-8")

    def say(*a):
        print(*a, file=log, flush=True)

    pl = pd.read_csv(D / "plays.csv", usecols=K + ["defensiveTeam", "possessionTeam", "down", "yardsToGo",
                                                   "offenseFormation", "passResult", "pff_passCoverage",
                                                   "pff_passCoverageType", "pff_playAction"])
    g = pd.read_csv(D / "games.csv", usecols=["gameId", "week"])
    pf = pd.read_csv(D / "pffScoutingData.csv", usecols=K + ["nflId", "pff_role", "pff_positionLinedUp"])
    defn = pf[pf.pff_role.isin(["Coverage", "Pass Rush"])].copy()
    defn["rush"] = (defn.pff_role == "Pass Rush").astype(int)
    defn["safety"] = defn.pff_positionLinedUp.isin(SAFE).astype(int)
    defn = defn[K + ["nflId", "rush", "safety"]]

    partes = []
    archivos = sorted((D / "tracking").glob("tracking_*.csv"))
    for f in archivos:
        d = pd.read_csv(f, usecols=["gameId", "playId", "nflId", "frameId", "team", "x", "y", "event"],
                        dtype={"gameId": "int64", "playId": "int64", "frameId": "int32",
                               "x": "float32", "y": "float32"})
        ev = d[d.event.isin(["ball_snap", "autoevent_ballsnap"])]
        manual = ev[ev.event == "ball_snap"].groupby(K).frameId.min()
        auto = ev[ev.event == "autoevent_ballsnap"].groupby(K).frameId.min()
        snap = manual.combine_first(auto).rename("f_snap")   # regla: ball_snap si existe; si no, autoevent
        d = d.join(snap, on=K)
        d = d[d.frameId == d.f_snap]
        balon = d[d.team == "football"][K + ["x", "y"]].rename(columns={"x": "bx", "y": "by"})
        j = d[d.team != "football"].dropna(subset=["nflId"]).copy()
        j["nflId"] = j.nflId.astype("int64")
        j = (j.merge(defn, on=K + ["nflId"], how="inner", validate="one_to_one")
              .merge(balon, on=K, how="inner", validate="many_to_one"))
        prof = (j.x - j.bx).abs()
        lat = (j.y - j.by).abs()
        cols = ["rush", "safety"]
        for u, l in LINEA:
            j[col_linea(u, l)] = ((prof <= u) & (lat <= l)).astype(int)
            cols.append(col_linea(u, l))
        for p in PROF_SAFETY:
            j[col_prof(p)] = ((j.safety == 1) & (prof >= p)).astype(int)
            cols.append(col_prof(p))
        r = j.groupby(K)[cols].sum()
        r["n_def_snap"] = j.groupby(K).size()
        partes.append(r.reset_index())

    R = pd.concat(partes, ignore_index=True).rename(columns={"rush": "n_rush", "safety": "n_saf"})
    out = (pl.merge(g, on="gameId", how="left", validate="many_to_one")
             .merge(R, on=K, how="left", validate="one_to_one"))
    for c in R.columns:
        if c not in K:
            out[c] = out[c].astype("Int64")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    # ---- conteos de control (deben coincidir con docs/disfraz_viabilidad_salida.txt)
    v = out[(out.down != 0) & out.n_def_snap.notna()]
    lin = v[col_linea(2.0, 8.0)]
    say("archivos de tracking:", len(archivos))
    say("filas escritas:", len(out), "->", OUT.relative_to(ROOT).as_posix())
    say("jugadas con snap y defensores medidos:", int(out.n_def_snap.notna().sum()))
    say("válidas (sin 2pt):", len(v))
    say("defensores medidos al snap por jugada:", v.n_def_snap.value_counts().sort_index().to_dict())
    say("control muestra_no_manda (5+ en línea y <=4 atacan):", int(((lin >= 5) & (v.n_rush <= 4)).sum()), "(esperado 1653)")
    say("control blitz_escondido (<=4 en línea y 5+ atacan):", int(((lin <= 4) & (v.n_rush >= 5)).sum()), "(esperado 751)")
    say("jugadas con 2 safeties a >=10 yd al snap:", int((v[col_prof(10.0)] == 2).sum()))
    say(f"tiempo: {time.time() - t0:.0f} s")
    log.close()


if __name__ == "__main__":
    sys.exit(main())
