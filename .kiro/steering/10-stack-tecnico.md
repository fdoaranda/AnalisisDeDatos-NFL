---
inclusion: always
---

# Stack OBLIGATORIO (versiones fijas, vienen de la plantilla)

Con otras versiones el proyecto podría no poder publicarse. NO actualices, NO cambies, NO agregues dependencias pesadas sin avisar.

| Componente | Versión |
|---|---|
| Python | 3.12.12 |
| uv | 0.11.19 |
| Node.js / npm | 22.23.1 / 10.x |
| fastapi / uvicorn / pydantic | 0.115.14 / 0.34.3 / 2.11.7 |
| pandas / numpy | 2.2.3 / 2.1.3 |
| strands-agents / boto3 | 1.64.0 / 1.44.0 |
| React / Vite / TypeScript | 18.3.1 / 5.4.21 / 5.7.3 |
| Tailwind CSS / Recharts | 3.4.19 / 3.10.1 |

## Convenciones
- Backend: FastAPI + pydantic v2. Datos con pandas/numpy. Gestiona paquetes con `uv` (no pip a mano).
- Frontend: React 18 + TypeScript + Vite + Tailwind 3 + Recharts. Sin librerías de UI extra salvo necesidad real.
- IA (si el reto la pide): `strands-agents` con `boto3` (AWS Bedrock). Credenciales las maneja el entorno, nunca en código.
- Pandas 2.2: no uses APIs eliminadas; numpy 2.1: cuidado con dtypes.
- Usa rutas relativas y CORS habilitado para el origen del frontend en desarrollo.
- Validar con `.\.hackathon\setup.cmd --check` (Windows) o `sh .hackathon/setup.sh --check` (Mac/Linux) después de cada bloque grande de cambios.
