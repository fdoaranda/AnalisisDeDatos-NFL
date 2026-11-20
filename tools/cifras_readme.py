"""Extrae de la API en marcha (http://127.0.0.1:8000) todas las cifras que cita el README.
Uso: .venv\\Scripts\\python tools\\cifras_readme.py  -> docs/cifras_readme.txt
Cada cifra del README debe aparecer en esta salida.
"""
import json
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000/"
OUT = Path(__file__).resolve().parent.parent / "docs" / "cifras_readme.txt"


def get(ruta):
    with urllib.request.urlopen(BASE + ruta, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def p(e):
    if e["estimado"] is None:
        return f"sin dato (n={e['n']})"
    return f"{100 * e['estimado']:.1f} % [IC {100 * e['ic_inf']:.1f}–{100 * e['ic_sup']:.1f}] n={e['n']}"


def pp(e):
    return f"{100 * e['estimado']:+.1f} pp [IC {100 * e['ic_inf']:+.1f} a {100 * e['ic_sup']:+.1f}] n={e['n']}"


with open(OUT, "w", encoding="utf-8") as o:
    meta = get("api/meta")
    print("health:", get("health"), file=o)
    print(f"meta: {meta['fuente']} | partidos={meta['partidos']} jugadas={meta['jugadas']} equipos={len(meta['equipos'])}", file=o)
    print("criterio:", meta["criterio_distinto"]["texto"], file=o)
    print("umbrales:", meta["umbrales"], file=o)
    for m in ["rotacion_cascara", "muestra_no_manda", "blitz_escondido"]:
        r = get(f"api/resumen?metrica={m}")
        print(f"\n## {m}\ntitulo: {r['titulo']}\nliga: {p(r['liga'])}", file=o)
        for e in r["equipos"]:
            if e["distinto_de_liga"]:
                lado = "ARRIBA" if e["diferencia_vs_liga"]["estimado"] > 0 else "ABAJO"
                print(f"  distinto {lado} #{e['posicion']} {e['equipo']}: tasa {p(e['tasa'])} | dif {pp(e['diferencia_vs_liga'])}", file=o)
        for eq in ["MIA", "SF", "CLE", "NYJ"]:
            e = next(x for x in r["equipos"] if x["equipo"] == eq)
            print(f"  {eq} #{e['posicion']}: tasa {p(e['tasa'])} | dif {pp(e['diferencia_vs_liga'])} | distinto={e['distinto_de_liga']}", file=o)
    c = get("api/comparacion?equipo=MIA")
    print(f"\n## comparacion MIA\ntitulo: {c['titulo']}", file=o)
    for m in c["metricas"]:
        print(f"  {m['metrica']}: equipo {p(m['equipo'])} | liga {p(m['liga'])} | distinto={m['distinto_de_liga']}", file=o)
    print("\nOK", file=o)
