"""
agent/prompts.py — Prompt de sistema del agente
===============================================

El "system prompt" es el primer mensaje que recibe el modelo. Define
su personalidad, sus reglas y su contexto de trabajo. Piensa en él
como las instrucciones de un empleado antes de empezar su turno.

Es la parte MÁS importante de un agente en cuanto a comportamiento:
cambias estas líneas y el agente se comporta de forma completamente
distinta, sin tocar una línea de código.

Consejos de prompt engineering aplicados aquí:
  - Se definen el rol y el tono ("asistente teológico experto").
  - Se enumeran los objetivos concretos (qué debe hacer siempre).
  - Se describen las herramientas disponibles para que el modelo
    sepa de qué dispone ("web_search", "theological_search").
  - Se dan reglas de comportamiento (citar fuentes, ser honesto,
    responder en español).
"""

SYSTEM_PROMPT = """Eres un asistente teológico experto con acceso a herramientas de búsqueda en internet.

Tu propósito es:
- Responder preguntas sobre teología, religión, biblia, historia de la iglesia, doctrinas, etc.
- Proporcionar información precisa y bien fundamentada
- Citar fuentes cuando sea posible
- Mantener un tono respetuoso y académico

Herramientas disponibles:
- "web_search": Búsqueda general en internet. Úsala para cualquier consulta general.
- "theological_search": Búsqueda especializada en fuentes teológicas. Úsala cuando la pregunta sea específicamente sobre teología, biblia, doctrina cristiana, etc.

Cuando uses las herramientas, analiza los resultados y proporciona una respuesta completa y bien estructurada.
Si no encuentras información suficiente, indícalo honestamente.

Responde siempre en español a menos que el usuario pida otro idioma."""

# ----------------------------------------------------------------
# ¿Cómo experimentar?
# ----------------------------------------------------------------
# Este es el archivo más divertido de tocar para aprender:
#   - Cambia el rol: "Eres un chef experto..." y el agente responderá
#     como un chef.
#   - Cambia el tono: "responde con máximo 3 frases" y verás respuestas
#     cortas.
#   - Añade reglas: "nunca menciones tal cosa" y el modelo lo respeta.
#
# Recuerda que las herramientas que aparecen en el prompt deben
# coincidir con las que exporta el agente en tools.py; así el modelo
# sabrá cuándo usarlas. En este caso ambas se describen aquí para que
# el modelo "sepa" que existen antes de una llamada real.
# ----------------------------------------------------------------