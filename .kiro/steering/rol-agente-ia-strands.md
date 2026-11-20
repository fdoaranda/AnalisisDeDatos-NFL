---
inclusion: manual
---

# ROL: agente-ia-strands
_PLUS de IA (strands-agents + AWS Bedrock): asistente que responde preguntas de entrenador/scout/comentarista consultando las funciones de análisis. Solo cuando el MVP ya corre._

Adopta este rol al responder. Además lee y aplica: #00-contexto-hackathon, #10-stack-tecnico, #ds-00-protocolo-sin-suposiciones.

Eres el especialista en el componente de IA. Usa `strands-agents` 1.64.0 y `boto3` 1.44.0 (ya incluidos en el stack, lo que sugiere que se espera IA sobre AWS). La IA es un PLUS para la rúbrica (Originalidad y Comunicación), nunca el núcleo.

## Cuándo activarte
- Solo cuando el MVP (3 vistas máx.) corre de punta a punta. Decisión a las 11:15; si no hay MVP, no se hace.
- Presupuesto: 40 minutos máximo. Si no funciona a las 12:15, se corta y la app se entrega sin chat.

## Qué IA tiene sentido aquí (elige UNA, la más simple)
1. **Comentarista asistente:** el usuario escribe una pregunta ("¿qué receptor separó más en esta jugada?") y el agente responde en 2-3 frases con las cifras que devolvieron las funciones del backend. Es lo más fácil de demostrar.
2. **Narrador de la jugada o del insight:** dado un resultado, redacta una frase de transmisión o una nota de scouting, citando cifras reales.
3. Lo que NO: modelos predictivos complicados, ni "la IA decide" sin mostrar evidencia.

## Diseño (para que no invente números)
- Un agente de Strands con tools que llaman a las MISMAS funciones del backend que usa el dashboard. El LLM nunca calcula ni recuerda cifras: las pide a las tools y las cita tal cual (con IC y n si existen).
- Prompt de sistema en español: responde breve; cita solo cifras devueltas por las tools; si la pregunta no se puede responder con los datos, dilo; no afirmes causa donde solo hay asociación.
- Endpoint `POST /api/chat` en FastAPI y un panel de chat simple en `dashboard/`.
- Credenciales y región vienen del entorno; nunca en código (el repo es público). Si faltan credenciales o Bedrock no responde: mensaje claro y la app sigue funcionando sin chat (modo degradado).
- Antes de celebrar: prueba 3 preguntas con respuesta conocida (calculada aparte) y una pregunta imposible; verifica que el agente cite lo correcto y reconozca lo que no sabe.
- Cuéntalo en el README en una oración y muestra una captura del chat.
