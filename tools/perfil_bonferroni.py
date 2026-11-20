"""Reproduce el cálculo de arranque de la API (sin uvicorn): tiempo y conteo de equipos distintos.
Uso: .venv\\Scripts\\python tools\\perfil_bonferroni.py  -> docs/_perfil.txt
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "_perfil.txt"
sys.stderr = open(ROOT / "docs" / "_perfil_err.txt", "w", encoding="utf-8")
from backend import analisis  # noqa: E402

with open(OUT, "w", encoding="utf-8") as o:
    t0 = time.time()
    df = analisis.cargar_jugadas()
    for m in analisis.METRICAS:
        t1 = time.time()
        r = analisis.calcular_resumen(df, m)
        eq = r["equipos"]
        bonf = [e["equipo"] for e in eq if e["distinto_de_liga"]]
        arriba = [e["equipo"] for e in eq if e["distinto_de_liga"] and e["diferencia_vs_liga"]["estimado"] > 0]
        d95 = [e["equipo"] for e in eq if e["diferencia_vs_liga"]["ic_inf"] is not None
               and (e["diferencia_vs_liga"]["ic_inf"] > 0 or e["diferencia_vs_liga"]["ic_sup"] < 0)]
        print(f"[{m}] {time.time() - t1:.1f} s | equipos={len(eq)}", file=o, flush=True)
        print(f"  titulo: {r['titulo']}", file=o)
        print(f"  distinto_de_liga (Bonferroni): {len(bonf)} {bonf}", file=o)
        print(f"    por encima de la liga: {len(arriba)} {arriba}", file=o)
        print(f"  referencia, IC 95 % sin 0: {len(d95)} {d95}", file=o)
        print(f"  metodo diferencia: {eq[0]['diferencia_vs_liga']['metodo']}", file=o)
        print(f"  nota ejemplo ({eq[0]['equipo']}): {eq[0]['diferencia_vs_liga']['nota']}", file=o, flush=True)
    meta = analisis.calcular_meta(df)
    print("limitación nueva en /api/meta:", meta["limitaciones"][-1], file=o)
    print(f"total: {time.time() - t0:.1f} s", file=o, flush=True)
