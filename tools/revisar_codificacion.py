"""Revisa la codificación de los archivos de texto del dashboard y del backend (no modifica nada).
Detecta: UTF-8 inválido, BOM, y mojibake típico (texto UTF-8 leído como Latin-1/cp1252: 'Ã¡', 'Ã­', 'Â').
También pide /api/meta y revisa el encabezado Content-Type si la API está corriendo.
Uso: .venv\\Scripts\\python tools\\revisar_codificacion.py   -> docs/_codificacion.txt
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "_codificacion.txt"
EXT = {".ts", ".tsx", ".json", ".html", ".css", ".py", ".md", ".js"}
MOJIBAKE = re.compile("[ÃÂ][\u0080-\u00bf]|â€")
CARPETAS = [ROOT / "dashboard" / "src", ROOT / "dashboard", ROOT / "backend"]

lineas = []
vistos = set()
for base in CARPETAS:
    patron = "*" if base == ROOT / "dashboard" else "**/*"
    for f in base.glob(patron):
        if not f.is_file() or f.suffix not in EXT or "node_modules" in f.parts or f in vistos:
            continue
        vistos.add(f)
        crudo = f.read_bytes()
        rel = f.relative_to(ROOT).as_posix()
        bom = crudo.startswith(b"\xef\xbb\xbf")
        try:
            texto = crudo.decode("utf-8")
        except UnicodeDecodeError as e:
            lineas.append(f"NO-UTF8  {rel}: {e}")
            continue
        malos = [(i + 1, l.strip()[:90]) for i, l in enumerate(texto.splitlines()) if MOJIBAKE.search(l)]
        estado = "OK" if not malos and not bom else ("BOM" if bom and not malos else "MOJIBAKE")
        lineas.append(f"{estado:8} {rel}" + (f"  ({len(malos)} líneas)" if malos else ""))
        for n, l in malos[:5]:
            lineas.append(f"           línea {n}: {l}")

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/meta", timeout=5) as r:
        ct = r.headers.get("content-type")
        cuerpo = r.read()
    texto = cuerpo.decode("utf-8")
    lineas.append(f"API /api/meta Content-Type: {ct}")
    lineas.append(f"API /api/meta contiene 'más' bien codificado: {'más' in texto}; mojibake: {bool(MOJIBAKE.search(texto))}")
except Exception as e:  # la API puede no estar corriendo
    lineas.append(f"API no disponible: {e}")

OUT.write_text("\n".join(lineas) + "\n", encoding="utf-8")
