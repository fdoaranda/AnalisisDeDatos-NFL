---
inclusion: always
---

# Estructura y entrega

- La estructura de carpetas la crea la plantilla (`setup`). RESPÉTALA. Si esta guía contradice a la plantilla, gana la plantilla.
- Trabaja dentro de la carpeta del PROYECTO (la que crea el script), no en la carpeta del zip.
- `.hackathon/` es del evento: no la edites ni la borres.
- Datos grandes: no los subas a git ni los metas al zip de entrega si no son necesarios; usa muestras o agregados precalculados.

## Comandos del evento
- Revisar alineación (no modifica código): `--check`
- Validar y generar `entrega-<proyecto>-<fecha>.zip` (publica en AWS): `--entregar`
  - Exige `README.md` en la raíz.
  - Se puede ejecutar las veces que haga falta: entrega una versión temprana (~11:50) y otra final (~12:50).

## Definición de "terminado"
1. `--check` pasa sin errores.
2. La app arranca desde cero siguiendo el README.
3. README: arriba 3 a 5 oraciones (qué construiste, qué revela, quién lo usaría); debajo, detalle técnico y cómo correr.
3b. Repositorio de GitHub PÚBLICO, sin secretos, con el mismo código del .zip. Incluir una captura o GIF del resultado.
4. Se corrió `--entregar` y se verificó el resultado publicado.
