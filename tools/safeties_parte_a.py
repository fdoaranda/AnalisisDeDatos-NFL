"""Parte A (sin tracking): tamaños de grupo para la pregunta de safeties vs Cover-3. No modifica datos."""
import sys
from pathlib import Path
import pandas as pd

D = Path(__file__).resolve().parent.parent / "data"
sys.stdout = open(D.parent / "docs" / "safeties_parte_a_salida.txt", "w", encoding="utf-8")
pl = pd.read_csv(D / "plays.csv")
pf = pd.read_csv(D / "pffScoutingData.csv", na_values=["NA"])
pl_ = pl[pl.down != 0]  # sin conversiones de 2 puntos (docs/datos.md #8)

print("n jugadas total:", len(pl), "| sin 2pt (down!=0):", len(pl_))
print("\npff_positionLinedUp x pff_role (todas las posiciones, conteo de filas):")
print(pd.crosstab(pf.pff_positionLinedUp, pf.pff_role).to_string())

print("\nCOBERTURA (todas las jugadas, sin 2pt):")
c = pl_.groupby(["pff_passCoverage", "pff_passCoverageType"]).size().rename("n_jugadas")
print(c.to_string())
print("\nEquipos defensivos distintos por cobertura y jugadas por equipo defensivo en Cover-3:")
c3 = pl_[pl_.pff_passCoverage == "Cover-3"]
print("Cover-3 n:", len(c3), "| equipos defensivos:", c3.defensiveTeam.nunique(), "| partidos:", c3.gameId.nunique())
print(c3.groupby("defensiveTeam").size().describe().round(1).to_string())
print("min/max jugadas Cover-3 por equipo defensivo:", int(c3.groupby("defensiveTeam").size().min()), int(c3.groupby("defensiveTeam").size().max()))
