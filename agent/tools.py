"""
agent/tools.py — Herramientas del agente
========================================

Una "herramienta" (tool) es una función normal de Python que el agente
puede decidir llamar. Es la forma de dar PODER DE ACCIÓN al LLM: el
modelo por sí solo no tiene acceso a internet; para eso le damos estas
funciones.

¿Cómo sabe el modelo qué herramienta usar?
------------------------------------------
Cuando decoramos una función con @tool, LangChain:
  1. Lee el nombre de la función → será el identificador de la tool.
  2. Lee su docstring → se convierte en la DESCRIPCIÓN que el modelo
     ve. El modelo elige la tool leyendo esta descripción.
  3. Lee los parámetros (con tipo y docstring de argumentos si usas
     Google Style) → define el "schema" de entrada que el modelo debe
     rellenar.

Por eso es CRÍTICO escribir docstrings descriptivos: son el "menú"
del modelo. Un buen docstring = el modelo sabrá cuándo usar la tool.
"""

# -*- Importaciones -*-
# `tool`: decorador de LangChain que convierte una función Python en
#   una herramienta que el LLM puede invocar de forma nativa.
from langchain_core.tools import tool

# DDGS: cliente síncrono del buscador DuckDuckGo. Nos permite hacer
#   búsquedas web sin necesidad de una API key (a diferencia de
#   Google/Bing). Funciona "scrapeando" los resultados de DuckDuckGo.
from duckduckgo_search import DDGS


@tool
def web_search(query: str) -> str:
    """Realiza una búsqueda general en internet. Úsala para cualquier consulta de información general."""
    try:
        # "with DDGS() as ddgs": abrimos una sesión de búsqueda.
        # ddgs.text(query, max_results=5):
        #   - query: texto a buscar.
        #   - max_results=5: cuántos resultados queremos.
        # Devuelve una lista de dicts con título, resumen (body) y URL.
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No se encontraron resultados para la búsqueda."

            # Formateamos los resultados en un texto legible. Este
            # string es el "observation" que se le devuelve al LLM:
            # el modelo lo leerá para redactar su respuesta final.
            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. **{r['title']}**\n   {r['body']}\n   Fuente: {r['href']}")
            return "\n\n".join(formatted)
    except Exception as e:
        # Buenas prácticas: nunca dejamos que una tool "reviente" la
        # ejecución. Devolvemos un mensaje de error amigable para que
        # el LLM pueda, por ejemplo, disculparse o intentar otra cosa.
        return f"Error al realizar la búsqueda: {str(e)}"


@tool
def theological_search(query: str) -> str:
    """Realiza una búsqueda especializada en fuentes teológicas, bíblicas y religiosas. Úsala para preguntas sobre teología, biblia, doctrina, historia de la iglesia, etc."""
    try:
        # Diferencia clave con web_search: construimos una consulta
        # ENRIQUECIDA con términos teológicos. Así DuckDuckGo devuelve
        # resultados más relevantes para el dominio del agente.
        theological_query = f"{query} teología biblia doctrina cristiana"
        with DDGS() as ddgs:
            results = list(ddgs.text(theological_query, max_results=5))
            if not results:
                return "No se encontraron resultados teológicos para la búsqueda."

            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. **{r['title']}**\n   {r['body']}\n   Fuente: {r['href']}")
            return "\n\n".join(formatted)
    except Exception as e:
        return f"Error al realizar la búsqueda teológica: {str(e)}"


# ----------------------------------------------------------------
# ¿Cómo añadir más herramientas?
# ----------------------------------------------------------------
# Solo tienes que:
#   1. Crear una función con @tool y un buen docstring.
#   2. Importarla y añadirla a la lista `tools` de agent.py.
# Por ejemplo:
#
#   @tool
#   def get_time(city: str) -> str:
#       """Devuelve la hora actual de una ciudad. Úsala para preguntas sobre la hora."""
#       ... # llamada a una API de tiempo
#
# Y en create_agent():  tools = [web_search, theological_search, get_time]
# El LLM automaticamente sabrá que existe y cuándo usarla.
# ----------------------------------------------------------------