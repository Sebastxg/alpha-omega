"""
agent/agent.py — Construcción del Agente con LangChain
=======================================================

Este módulo es el "cerebro" del proyecto: aquí se junta el modelo de
lenguaje (LLM) con las herramientas y el prompt para formar un AGENTE.

¿Qué es un agente en LangChain?
-------------------------------
Es un programa que usa un LLM como "cerebro de decisión". En vez de
responder directamente, el LLM puede decidir llamar a herramientas
externas (búsquedas web, calculadoras, APIs...) y luego usar esos
resultados para componer su respuesta final.

El concepto clave es el LOOP del agente:

    LLM piensa → ¿necesita una herramienta? → la llama
                                   ↓
                   ¿ya tiene suficiente info?
                                   ↓
                Responde directamente al usuario

Este bucle de "pensar-actuar-observar" es lo que diferencia un agente
de un simple LLM con un prompt.
"""

# -*- Importaciones de LangChain -*-
# ChatOpenAI: envuelve la API de OpenAI para que LangChain pueda hablar
#   con GPT-4o-mini. Se encarga de autenticación, formato de mensajes,
#   y (clave) de exponer el soporte de "tool calling": la capacidad del
#   modelo de declarar "quiero llamar a la herramienta X con estos
#   argumentos" en vez de escribir texto plano.
from langchain_openai import ChatOpenAI

# Tipos de mensajes que entiende LangChain. La mayoría de los LLMs
# esperan una lista de mensajes con roles:
#   SystemMessage  → instrucciones del sistema (personalidad/reglas).
#   HumanMessage   → un mensaje del usuario.
#   AIMessage      → una respuesta anterior del modelo (contexto).
# Estos objetos son la moneda de cambio para la memoria de la conversación.
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Funciones para crear el agente y ejecutarlo:
#   create_tool_calling_agent: ensambla LLM + herramientas + prompt en
#     un agente capaz de llamar herramientas (usa el protocolo nativo
#     de "tool calling" del modelo).
#   AgentExecutor: se encarga de ejecutar el LOOP del agente (cómo te
#     quedan los pasos del scratchpad, gestionar errores, límite de
#     iteraciones, etc.). Es la pieza que "orquesta" la interacción.
from langchain.agents import create_tool_calling_agent, AgentExecutor

# ChatPromptTemplate: plantilla de prompt. Permite construir el mensaje
#   que se le envía al modelo con "huecos" ({chat_history}, {input},
#   {agent_scratchpad}) que se rellenan en cada llamada.
from langchain_core.prompts import ChatPromptTemplate

# Nuestras piezas:
#   SYSTEM_PROMPT: el prompt de sistema (personalidad del agente).
#   web_search y theological_search: las herramientas que puede usar.
from .prompts import SYSTEM_PROMPT
from .tools import web_search, theological_search


def create_agent():
    """Fabrica y devuelve un AgentExecutor completamente configurado.

    Esta función se llama UNA sola vez en main.py (al arrancar el
    servidor), porque construir el agente implica configuración que
    no queremos repetir en cada petición.

    Paso a paso:
      1. Crear el modelo (LLM) → ChatOpenAI.
      2. Definir las herramientas disponibles → lista `tools`.
      3. Definir la plantilla de prompt → ChatPromptTemplate.
      4. Ensamblar → create_tool_calling_agent(llm, tools, prompt).
      5. Envolver en un ejecutor → AgentExecutor (loop + control de errores).

    Ejemplo de uso:
        agent = create_agent()
        resultado = agent.invoke({"input": "¿Qué es la Trinidad?",
                                  "chat_history": []})
    """
    # ------------------------------------------------------------
    # 1. El modelo de lenguaje (LLM).
    # ------------------------------------------------------------
    # "gpt-4o-mini": modelo de OpenAI, pequeño, rápido y barato, ideal
    #   para un agente con búsquedas.
    # "temperature=0.7": controla la "creatividad" de las respuestas.
    #   - Cerca de 0.0 → respuestas deterministas, predecibles (bueno
    #     para código o hechos).
    #   - Cerca de 1.0 → respuestas variadas, más "fluidas" (utópico
    #     para chat o escritura creativa).
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # ------------------------------------------------------------
    # 2. Herramientas disponibles.
    # ------------------------------------------------------------
    # Cada elemento es una función decorada con @tool (ver tools.py).
    # El LLM verá el docstring de cada una y decidirá cuál usar según
    # la pregunta del usuario. Poder elegir es lo que "habilita" el
    # comportamiento agéntico.
    tools = [web_search, theological_search]

    # ------------------------------------------------------------
    # 3. Plantilla de prompt.
    # ------------------------------------------------------------
    # Construimos el mensaje que se le enviará al modelo. Fíjate en
    # los "placeholders" (huecos entre llaves):
    #   ("system", SYSTEM_PROMPT)          → mensaje de sistema.
    #   ("placeholder", "{chat_history}")  → mensajes anteriores de la
    #       conversación (se rellena con HumanMessage/AIMessage).
    #   ("human", "{input}")               → el mensaje actual del usuario.
    #   ("placeholder", "{agent_scratchpad}") → MUY IMPORTANTE: aquí
    #       LangChain coloca el registro de las acciones que el agente
    #       YA ejecutó en esta misma llamada (qué herramientas llamó y
    #       qué observó). Sin este placeholder, el modelo no sabría
    #       en qué paso va del bucle.
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # ------------------------------------------------------------
    # 4. Ensamblar el agente.
    # ------------------------------------------------------------
    # create_tool_calling_agent junta las tres piezas. A partir de aquí
    # tenemos un agente que el modelo puede usar para llamar herramientas.
    agent = create_tool_calling_agent(llm, tools, prompt)

    # ------------------------------------------------------------
    # 5. El ejecutor (la maquinaria del loop).
    # ------------------------------------------------------------
    # AgentExecutor es el "director de orquesta". Cada invoke() suyo:
    #   a) Envía el prompt inicial al modelo.
    #   b) Si el modelo quiere llamar una herramienta, LA EJECUTA.
    #   c) Junta el resultado (observation) al scratchpad.
    #   d) Reenvía todo al modelo.
    #   e) Repite hasta que el modelo responda texto final (o agote
    #      el límite de iteraciones).
    #
    # Opciones de configuración:
    #   verbose=True: imprime en la consola los pasos del agente
    #     (¡útil para ver exactamente qué hace y aprender con él!).
    #   handle_parsing_errors=True: si el modelo responde algo que no
    #     puede parsearse como acción, no rompe todo: lo reintenta.
    #   max_iterations=5: límite de vueltas del bucle. Sin esto un
    #     agente podría quedarse llamando herramientas para siempre.
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
    )

    return executor


def format_history(messages: list[dict]) -> list:
    """Convierte el historial guardado (listas de dicts) en mensajes
    de LangChain (HumanMessage/AIMessage).

    ¿Por qué es necesario? En main.py guardamos el historial como
    dicts simples:
        [{"role": "human", "content": "Hola"},
         {"role": "ai", "content": "Hola, ¿qué deseas?"}]

    Pero LangChain espera objetos de mensaje con su tipo correspondiente:
        [HumanMessage(content="Hola"),
         AIMessage(content="Hola, ¿qué deseas?")]

    Este formato es esencial para que el modelo distinga quién dijo cada
    cosa y para que el prompt incluya correctamente el historial.

    Parámetros:
        messages: lista de dicts con las claves "role" y "content".

    Devuelve:
        Lista de objetos HumanMessage/AIMessage lista para el agente.
    """
    history = []
    for msg in messages:
        if msg["role"] == "human":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            history.append(AIMessage(content=msg["content"]))
        # Nota: si algún día guardamos mensajes de sistema en el
        # historial, aquí se añadiría su rama (SystemMessage).
    return history