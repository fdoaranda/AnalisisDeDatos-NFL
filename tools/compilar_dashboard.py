"""Corre el typecheck y el build del dashboard con el Node de la plantilla (no instala nada).
Uso: .venv\\Scripts\\python tools\\compilar_dashboard.py   -> docs/_build.txt
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE_DIR = ROOT / ".hackathon" / ".tools" / "node"
DASH = ROOT / "dashboard"
OUT = ROOT / "docs" / "_build.txt"
env = {**os.environ, "PATH": f"{NODE_DIR}{os.pathsep}{os.environ.get('PATH', '')}"}
node = str(NODE_DIR / "node.exe")
pasos = [
    ("tsc --noEmit", [node, str(DASH / "node_modules" / "typescript" / "bin" / "tsc"), "--noEmit"]),
    ("vite build", [node, str(DASH / "node_modules" / "vite" / "bin" / "vite.js"), "build"]),
]
with open(OUT, "w", encoding="utf-8") as o:
    for nombre, cmd in pasos:
        r = subprocess.run(cmd, cwd=DASH, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(f"### {nombre} -> código {r.returncode}", file=o)
        print((r.stdout + r.stderr).strip()[-3000:], file=o, flush=True)
        if r.returncode != 0:
            break
