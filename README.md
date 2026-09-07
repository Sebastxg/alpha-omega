# Alpha-Omega — Agente Teológico con LangChain

API web de un agente de IA especializado en teología. Cuando le haces una
pregunta, decide si le conviene buscar en internet (DuckDuckGo) o si puede
responder directamente con su conocimiento.

```
Usuario ── POST /chat ──► FastAPI ──► Agente LangChain ──► GPT-4o-mini
                                       │    │                │
                                       │    └──► búsquedas   │
                                       │         de internet │
                                       ▼                    ▼
                                   Respuesta final ◄── análisis de resultados
```

## Requisitos

- Python 3.10+
- Una API key de OpenAI (porque el agente usa `gpt-4o-mini`)

## Instalación y ejecución

```bash
# 1. Crear el entorno virtual (solo la primera vez)
python3 -m venv venv

# 2. Activar el entorno
source venv/bin/activate

# 3. Instalar dependencias (solo la primera vez)
pip install -r requirements.txt

# 4. Crear el archivo .env con tu clave de OpenAI
echo "OPENAI_API_KEY=tu-clave-aqui" > .env

# 5. Arrancar el servidor
python main.py
```

La API quedará en `http://localhost:8000`.

Pruébala:

```bash
# Estado del servidor
curl http://localhost:8000/health

# Chatear con el agente
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es la Trinidad?"}'

# Mantener el contexto de una conversación: reenvía el mismo conversation_id
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Y cómo lo explican los primeros credos?", "conversation_id": "abc-123"}'
```

**Tip:** abre `http://localhost:8000/docs` para ver la documentación
interactiva de la API (generada automáticamente por FastAPI).

## Estructura del proyecto

```
alpha-omega/
├── main.py              # Servidor FastAPI: endpoints /health y /chat
├── requirements.txt     # Dependencias de Python
├── .env                 # Claves secretas (NO se sube a git)
├── agent/
│   ├── __init__.py      # Marca la carpeta como módulo de Python
│   ├── agent.py         # Crea el agente (LLM + tools + prompt + loop)
│   ├── tools.py         # Herramientas que el agente puede llamar
│   └── prompts.py       # Prompt de sistema (personalidad del agente)
└── models/
    ├── __init__.py      # Marca la carpeta como módulo de Python
    └── schemas.py       # Modelos Pydantic: validan entrada/salida
```

## Conceptos clave para entender el código

### 1. Agente (paradigma ReAct)

En vez de responder directamente, el modelo decide en un bucle si necesita
"actuar" (llamar una herramienta) u "observar" (leer el resultado). Ese
ciclo **Pensar → Actuar → Observar** se repite hasta que el modelo cree
tener suficiente información para responder. El límite es de 5 iteraciones
(`agent/agent.py`).

### 2. Tool calling (llamada de herramientas)

GPT-4o-mini puede declarar formalmente "quiero llamar a la función X con
estos argumentos". LangChain ejecuta la función por nosotros y le devuelve
el resultado al modelo. Cada función decorada con `@tool` se convierte en
una herramienta que el modelo puede elegir (ver `agent/tools.py`).

### 3. Memoria de conversación

No hay base de datos: el historial vive en un diccionario de Python
(`conversations` en `main.py`). Se reenvía al modelo como mensajes previos
para que "recuerde" el contexto. Se limita a los últimos 20 mensajes.

### 4. Validación con Pydantic

Los modelos en `models/schemas.py` garantizan que la API reciba y devuelva
siempre JSON con la forma correcta. Si el cliente manda datos inválidos,
FastAPI responde `422` automáticamente.

## Tecnologías

| Tecnología | Para qué sirve aquí |
|---|---|
| **Python 3.10** | Lenguaje del proyecto |
| **FastAPI** | Framework web: recibe/da respuestas HTTP |
| **Uvicorn** | Servidor ASGI que ejecuta FastAPI |
| **LangChain** | Orquestación de agentes, tools y memoria |
| **langchain-openai** | Conexión con GPT-4o-mini y tool calling |
| **Pydantic** | Validación de datos de entrada/salida |
| **duckduckgo-search** | Búsquedas web sin necesidad de API key |
| **python-dotenv** | Lectura de claves desde `.env` |

## Aprender más

- **FastAPI:** https://fastapi.tiangolo.com/tutorial/
- **LangChain (conceptos):** https://python.langchain.com/docs/introduction/
- **Agentes y loop:** https://python.langchain.com/docs/concepts/agents/
- **Tool calling:** https://python.langchain.com/docs/how_to/tool_calling/
- **Pydantic (modelos):** https://docs.pydantic.dev/latest/concepts/models/
- **OpenAI API (tool calling):** https://platform.openai.com/docs/guides/function-calling

## Ideas para practicar

1. **Añade una herramienta nueva** (p. ej. `calculate` con aritmética o un
   buscador de versículos bíblicos) y agrégala a la lista de `tools` de
   `agent.py`. Solo necesitas una función con `@tool` y un buen docstring.
2. **Cambia la personalidad** editando `agent/prompts.py` y observa cómo
   cambia el tono sin tocar código.
3. **Baja la temperatura** a `0` en `agent.py` y comprueba si las respuestas
   son más consistentes.
4. **Levanta el límite** de `max_iterations` y da una orden compleja para ver
   el bucle del agente en acción (`verbose=True` ya lo imprime en consola).
5. **Prueba con tu propia clave**: `conversation_id` distinto = historial
   aislado; el mismo = conversación continua.