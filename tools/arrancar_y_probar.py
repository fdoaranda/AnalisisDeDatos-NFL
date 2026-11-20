"""Arranca la API (8000) y, con --vite, el dashboard en desarrollo (5173); espera a que respondan,
corre las pruebas y deja ambos servidores encendidos. Bitácora: docs/_arranque.txt
Uso (desde la raíz): .venv\\Scripts\\python tools\\arrancar_y_probar.py [--vite]
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "docs" / "_arranque.txt"
PY = Path(sys.executable)
UVICORN = PY.parent / "uvicorn.exe"
NODE_DIR = ROOT / ".hackathon" / ".tools" / "node"
CON_VITE = "--vite" in sys.argv


def esperar(url: str, proc: subprocess.Popen, limite: float, o) -> bool:
    t0 = time.time()
    while time.time() - t0 < limite:
        if proc.poll() is not None:
            print(f"el proceso de {url} terminó con código {proc.returncode}", file=o, flush=True)
            return False
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    print(f"{url} listo en {time.time() - t0:.1f} s", file=o, flush=True)
                    return True
        except Exception:
            pass
        time.sleep(2)
    print(f"{url} no respondió en {limite:.0f} s", file=o, flush=True)
    return False


with open(LOG, "w", encoding="utf-8") as o:
    subprocess.run([str(PY), str(ROOT / "tools" / "liberar_puerto.py")], cwd=ROOT)
    api = subprocess.Popen([str(UVICORN), "backend.main:app", "--port", "8000"], cwd=ROOT,
                           stdout=open(ROOT / "docs" / "_uvicorn.txt", "w", encoding="utf-8"), stderr=subprocess.STDOUT)
    ok = esperar("http://127.0.0.1:8000/api/meta", api, 300, o)
    if ok:
        r = subprocess.run([str(PY), str(ROOT / "tools" / "probar_api.py")], cwd=ROOT, capture_output=True, text=True)
        print(f"probar_api.py código {r.returncode} {r.stdout.strip()} {r.stderr.strip()[-500:]}", file=o, flush=True)
    if ok and CON_VITE:
        env = {**os.environ, "PATH": f"{NODE_DIR}{os.pathsep}{os.environ.get('PATH', '')}"}
        vite = subprocess.Popen([str(NODE_DIR / "node.exe"), str(ROOT / "dashboard" / "node_modules" / "vite" / "bin" / "vite.js"),
                                 "--port", "5173", "--strictPort", "--host", "127.0.0.1"],
                                cwd=ROOT / "dashboard", env=env,
                                stdout=open(ROOT / "docs" / "_vite.txt", "w", encoding="utf-8"), stderr=subprocess.STDOUT)
        esperar("http://127.0.0.1:5173/", vite, 120, o)
    if ok:
        try:
            # La misma petición que hace el dashboard, pasando por el proxy de Vite (si está corriendo).
            with urllib.request.urlopen("http://127.0.0.1:5173/api/meta", timeout=10) as r:
                ct, meta = r.headers.get("content-type"), json.loads(r.read().decode("utf-8"))
            print(f"proxy /api/meta -> Content-Type: {ct}", file=o)
            print(f"proxy fuente: {meta['fuente']}", file=o)
            print(f"proxy criterio_distinto: {json.dumps(meta['criterio_distinto'], ensure_ascii=False)}", file=o)
            print(f"proxy descripcion[0]: {meta['metricas'][0]['descripcion']}", file=o)
            with urllib.request.urlopen("http://127.0.0.1:5173/api/resumen?metrica=blitz_escondido", timeout=10) as r:
                print(f"proxy titulo blitz_escondido: {json.loads(r.read().decode('utf-8'))['titulo']}", file=o, flush=True)
        except Exception as e:
            print(f"proxy de Vite no disponible: {e}", file=o, flush=True)
    subprocess.run([str(PY), str(ROOT / "tools" / "revisar_codificacion.py")], cwd=ROOT)
    print("fin", file=o, flush=True)
