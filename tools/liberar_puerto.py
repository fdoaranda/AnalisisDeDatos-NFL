"""Detiene el proceso que escucha en el puerto 8000 (solo desarrollo local, Windows).
Uso: .venv\\Scripts\\python tools\\liberar_puerto.py  -> resultado en docs/_puerto.txt
"""
import re
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "_puerto.txt"
salida = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
pids = sorted({int(m.group(1)) for m in re.finditer(r":8000\s+\S+\s+LISTENING\s+(\d+)", salida)})
lineas = [f"pids escuchando en 8000: {pids}"]
for pid in pids:
    r = subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], capture_output=True, text=True)
    lineas.append(f"taskkill {pid}: código {r.returncode}")
OUT.write_text("\n".join(lineas) + "\n", encoding="utf-8")
