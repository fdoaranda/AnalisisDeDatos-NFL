# Prompts para copiar y pegar (en orden)

## 0. Antes de empezar (5 min)
Plantillas para llenar JUNTOS en los primeros 20 min: `PLAN.md` y `docs/api.md` (cópialos a la raíz del proyecto).

1. Instala la plantilla (setup) y corre `--check`.
2. Copia la carpeta `.kiro/` de este kit DENTRO de la carpeta del proyecto (la que crea el script, no la del zip).
3. Abre la carpeta en Kiro. Los steering se cargan solos. Los agentes: selector de agente en la barra inferior del chat.

## 1. Agente `lider-reto` — cuando den el reto
```
Este es el enunciado del reto: <PEGA TODO EL TEXTO / SUBE CAPTURAS>.
Datos en: <carpeta>. Somos <N> personas, tenemos <horas> horas.
Clasifica el reto, propón 3 ideas, elige una y crea PLAN.md. Dime qué agentes usar en qué orden.
```

## 2. Agente `auditor-calidad` y luego `experto-datos`
```
Inspecciona todos los datos y crea docs/datos.md con esquema y calidad.
Luego prueba las 3 ideas del PLAN.md y dime cuál tiene el insight más fuerte, con números.
```

## 3. Spec en Kiro (modo Spec) para el MVP
```
Crea un spec para el MVP descrito en PLAN.md: API FastAPI + dashboard React.
Requisitos cortos, diseño simple, tareas pequeñas y ordenadas. Respeta el stack fijo.
```
Aprueba requirements -> design -> tasks sin editarlos mucho (velocidad) y ejecuta las tareas.

## 4. Agente `backend-fastapi`, luego `frontend-dashboard`
```
Implementa los endpoints del PLAN.md usando las funciones de analytics y documenta el contrato en docs/api.md.
```
```
Construye el dashboard consumiendo docs/api.md. Máximo 3 vistas, con el hallazgo principal como título.
```
(Si trabajan en equipo: uno backend, otro frontend, en paralelo, con docs/api.md como contrato.)

## 5. Plus de IA: `agente-ia-strands` (solo si el MVP ya corre; decidir a las 11:15; corte 12:15)
```
Agrega un chat que responda preguntas sobre los datos usando tools que llamen a las funciones de analytics. Debe degradarse bien si Bedrock falla.
```

## 6. Agente `revisor-entrega` (a las 11:50 y al final)
```
Haz la auditoría de entrega completa y corrige lo mínimo. Escribe el README final con los hallazgos reales y el guion de demo de 3 minutos.
```
Luego: `--check` y `--entregar`.

## EXPERTO EN DATOS (agente `experto-datos` + 4 mini-agentes)
Copia también la carpeta `tools/` a la raíz del proyecto (`stats_toolkit.py` solo con numpy+pandas, y `test_retos.py`).
Antes de usarlos, haz los retos de `RETOS.md` (8 pruebas de comportamiento, 5-10 min) y corre `python tools/test_retos.py` en tu máquina.

Flujo recomendado con el agente `experto-datos`:
```
Pregunta del reto: <PEGA LA PREGUNTA>. Datos en <carpeta>.
Sigue el protocolo: reformula la pregunta, audita los datos con audit_dataframe, y dime qué análisis
es válido y cuál NO se puede hacer con estos datos. No supongas nada que no veas en los datos.
```
Después, en este orden (cambia de agente o pide su rol):
1. `auditor-calidad`: "Audita todos los archivos y escribe docs/calidad-datos.md."
2. `experto-datos`: "Ejecuta el análisis y dame la conclusión con IC, n, supuestos y límites."
3. `estadistico-rigor`: "Revisa que los métodos e intervalos sean correctos para datos agrupados."
4. `escepticista-revisor`: "Intenta romper esta conclusión. Dame el veredicto."
5. `narrador-visual`: "Convierte lo verificado en gráficas y README honestos."

Preguntas tipo "¿qué es mejor, A o B?": dile al experto
`Aplica ds-04: define la pregunta causal, estratifica por contexto, verifica solapamiento, calcula la diferencia con IC y n por contexto, y dime dónde NO se puede concluir.`

## Trucos de velocidad
- Sube a Kiro las capturas/PDF del reto tal cual; no lo reescribas.
- Si Kiro se enreda: "Simplifica. Dame la versión más pequeña que funcione end-to-end."
- Haz `--entregar` temprano (hacia las 11:50) como respaldo; se puede repetir.
- Guarda créditos: pide cambios concretos, no regeneraciones completas.
