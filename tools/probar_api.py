"""Prueba rápida de la API corriendo en http://localhost:8000 (no modifica nada).
Uso: .venv\\Scripts\\python tools\\probar_api.py   -> salida en docs/prueba_api_salida.txt
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000/"
OUT = Path(__file__).resolve().parent.parent / "docs" / "prueba_api_salida.txt"
CASOS = ["health", "api/meta",
         "api/resumen?metrica=muestra_no_manda", "api/resumen?metrica=blitz_escondido",
         "api/resumen?metrica=rotacion_cascara",
         "api/comparacion?equipo=MIA", "api/comparacion?equipo=kc",
         "api/serie?equipo=MIA&metrica=muestra_no_manda", "api/serie?equipo=TB&metrica=blitz_escondido",
         # errores esperados
         "api/resumen", "api/resumen?metrica=xyz", "api/comparacion", "api/comparacion?equipo=XYZ",
         "api/serie?equipo=MIA", "api/serie?equipo=MIA&metrica=rotacion_cascara", "api/noexiste"]


def fmt(e):
    if e["estimado"] is None:
        return f"null n={e['n']}"
    return f"{e['estimado']:+.3f} [{e['ic_inf']:+.3f}, {e['ic_sup']:+.3f}] n={e['n']}"


with open(OUT, "w", encoding="utf-8") as o:
    for ruta in CASOS:
        t0 = time.time()
        try:
            with urllib.request.urlopen(BASE + ruta) as r:
                status, cuerpo = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, cuerpo = e.code, e.read()
        ms = 1000 * (time.time() - t0)
        datos = json.loads(cuerpo.decode("utf-8"))
        print(f"### {ruta} -> HTTP {status} ({ms:.0f} ms)", file=o)
        if "error" in datos or ruta in ("health",):
            print(json.dumps(datos, ensure_ascii=False), file=o)
        elif ruta == "api/meta":
            print(json.dumps({k: v for k, v in datos.items() if k != "equipos"}, ensure_ascii=False), file=o)
            print("equipos:", len(datos["equipos"]), datos["equipos"][:5], "...", file=o)
        elif "equipos" in datos:
            print("titulo:", datos["titulo"], "| liga:", fmt(datos["liga"]), file=o)
            dist = [e["equipo"] for e in datos["equipos"] if e["distinto_de_liga"]]
            d95 = [e["equipo"] for e in datos["equipos"]
                   if e["diferencia_vs_liga"]["ic_inf"] is not None
                   and (e["diferencia_vs_liga"]["ic_inf"] > 0 or e["diferencia_vs_liga"]["ic_sup"] < 0)]
            arriba = [e["equipo"] for e in datos["equipos"]
                      if e["distinto_de_liga"] and e["diferencia_vs_liga"]["estimado"] > 0]
            print(f"distinto_de_liga (Bonferroni): {len(dist)} {dist} | por encima: {arriba}", file=o)
            print(f"solo con IC 95 % sin 0 (referencia): {len(d95)} {d95}", file=o)
            for e in datos["equipos"][:3] + datos["equipos"][-2:]:
                print(f"  #{e['posicion']} {e['equipo']}: tasa {fmt(e['tasa'])} | dif {fmt(e['diferencia_vs_liga'])}"
                      f" | q_bh={e['q_bh']:.2g} ({e['q_bh_nota']})", file=o)
            print("  nota dif:", datos["equipos"][0]["diferencia_vs_liga"]["nota"], file=o)
        elif "metricas" in datos:
            print("titulo:", datos["titulo"], file=o)
            for m in datos["metricas"]:
                print(f"  {m['metrica']}: equipo {fmt(m['equipo'])} | liga {fmt(m['liga'])} | dif "
                      f"{fmt(m['diferencia_vs_liga'])} | #{m['posicion']} distinto={m['distinto_de_liga']}", file=o)
        elif "puntos" in datos:
            print("titulo:", datos["titulo"], file=o)
            for p in datos["puntos"]:
                print(f"  {p['situacion']}: equipo {fmt(p['equipo'])} | liga {fmt(p['liga'])}"
                      f"{' | nota: ' + p['equipo']['nota'] if p['equipo']['nota'] else ''}", file=o)
print("ok")
