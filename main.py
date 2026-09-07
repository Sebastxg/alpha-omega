"""
main.py — Punto de entrada de la API del Agente Teológico
==========================================================

Este archivo define un servidor web (API REST) que expone el agente
de IA al mundo exterior. Flask/FastAPI funcionan como la "capa de
comunicación": reciben peticiones HTTP de cualquier cliente (un
teléfono, una web, curl, etc.) y devuelven respuestas HTTP en JSON.

Flujo completo de una petición:

  1. El cliente hace POST /chat con un JSON { "message": "..." }
  2. FastAPI lee el cuerpo y lo valida contra el modelo ChatRequest
     (definido en models/schemas.py). Si falta o sobra algo, devuelve
     automáticamente un error 422.
  3. Se busca (o crea) el historial de esa conversación.
  4. Se invoca al agente de LangChain con el mensaje + historial.
  5. El agente decide si llamar a DuckDuckGo o responder directamente.
  6. Se guarda el intercambio en memoria y se responde un ChatResponse.

¿Por qué un servidor web? Porque así el agente NO está atado a una
terminal: cualquier aplicación puede hablar con él por HTTP.
"""

import uuid  # Genera IDs únicos para cada conversación.
from fastapi import FastAPI, HTTPException  # Web framework + manejador de errores HTTP.
from dotenv import load_dotenv  # Carga las claves del archivo .env a variables de entorno.

# Importamos nuestros propios módulos:
#   - ChatRequest/ChatResponse: contratos de datos (qué entra y qué sale).
#   - create_agent: fabrica y devuelve el agente de LangChain listo para usar.
#   - format_history: convierte nuestra lista de dicts en mensajes de LangChain.
from models.schemas import ChatRequest, ChatResponse
from agent.agent import create_agent, format_history

# IMPORTANTE: esto lee el archivo .env (que contiene OPENAI_API_KEY)
# y lo mete en os.environ. Sin esto, ChatOpenAI no encontraría la clave
# y fallaría con un error de "API key no encontrada".
load_dotenv()

# Creamos la aplicación FastAPI. El parámetro "title/description" solo
# es informativo: FastAPI genera automáticamente una documentación
# interactiva (Swagger UI) en http://localhost:8000/docs con esta info.
app = FastAPI(
    title="Theological Agent API",
    description="API para agente teológico con herramientas de búsqueda",
    version="1.0.0",
)

# ----------------------------------------------------------------
# Memoria de la conversación (en RAM).
# ----------------------------------------------------------------
# Estructura: { "id-conversación": [ {role, content}, {role, content}, ... ] }
#
# NOTA IMPORTANTE: al ser un dict en memoria, los historiales se PIERDEN
# si el servidor se reinicia. Para producción real se usaría una base de
# datos (PostgreSQL, Redis, etc.). Aquí lo mantenemos simple para aprender.
conversations: dict[str, list[dict]] = {}

# Instanciamos el agente UNA sola vez al arrancar (no dentro de cada
# request). Crear el agente es relativamente caro (configura el modelo,
# las herramientas y el prompt), así que reutilizamos la misma instancia
# para todas las peticiones. Por eso está fuera de la función "chat".
agent_executor = create_agent()


@app.get("/health")
async def health_check():
    """Endpoint de salud: permite saber si el servidor se está ejecutando.

    GET /health → { "status": "ok" }

    Útil para orquestadores (Docker, Kubernetes, monitors) que hacen
    ping periódico para verificar que la API sigue viva."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal: recibe un mensaje del usuario y devuelve la
    respuesta del agente.

    El parámetro `request` es de tipo ChatRequest, por lo que FastAPI:
      1. Valida el JSON recibido contra el modelo Pydantic.
      2. Si es válido, construye una instancia y me la pasa aquí.
      3. Si NO es válido, responde 422 sin ejecutar esta función.

    El `response_model=ChatResponse` hace lo mismo a la salida: fastAPI
    serializa lo que devolvamos a JSON, garantizando que coincida con
    el contrato definido.
    """
    # Si el cliente no mandó conversation_id, generamos uno nuevo.
    # Así el usuario decide si quiere continuar una charla (manda el
    # mismo id) o empezar otra (no manda nada u otro id).
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Primera vez que vemos este id → creamos su historial vacío.
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    # Referencia al historial de ESTA conversación.
    history = conversations[conversation_id]

    try:
        # --------------------------------------------------------
        # El corazón de todo: invocar al agente de LangChain.
        # --------------------------------------------------------
        # invoke() recibe un dict con dos claves:
        #   "input":        el mensaje actual del usuario.
        #   "chat_history": mensajes previos formateados como objetos
        #                   HumanMessage/AIMessage (ver format_history).
        # Esta información se inyecta en el prompt del modelo: así el
        # modelo "recuerda" lo que se dijo antes en la conversación.
        result = agent_executor.invoke({
            "input": request.message,
            "chat_history": format_history(history),
        })

        # --------------------------------------------------------
        # Extraer qué herramientas usó el agente.
        # --------------------------------------------------------
        # El resultado del AgentExecutor contiene "intermediate_steps":
        # una lista de pasos (action, observation) que el agente ejecutó.
        # Cada "action" es un objeto que tiene un atributo .tool con el
        # nombre de la herramienta llamada (p. ej. "web_search").
        tools_used = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if hasattr(step[0], "tool"):
                    tools_used.append(step[0].tool)

        # --------------------------------------------------------
        # Guardar el intercambio en el historial (memoria).
        # --------------------------------------------------------
        history.append({"role": "human", "content": request.message})
        history.append({"role": "ai", "content": result["output"]})

        # Control de tamaño: si la conversación crece demasiado, nos
        # quedamos con los últimos 20 mensajes. Motivo: cada mensaje
        # extra ocupa tokens del modelo (los modelos cobran y tienen
        # límite de contexto, así que conviene no acumular indefinidamente).
        if len(history) > 20:
            conversations[conversation_id] = history[-20:]

        # Devolvemos la respuesta al cliente con el contrato ChatResponse.
        return ChatResponse(
            response=result["output"],
            conversation_id=conversation_id,
            tools_used=tools_used,
        )
    except Exception as e:
        # Cualquier error interno se convierte en HTTP 500 con el detalle.
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Esto solo se ejecuta si corres "python main.py" directamente.
    # Si lo importas desde otro módulo, no arranca el servidor.
    import uvicorn
    # host="0.0.0.0" → escucha en todas las interfaces de red
    #   (permite que otros dispositivos de tu red accedan).
    # port=8000 → puerto por defecto.
    uvicorn.run(app, host="0.0.0.0", port=8000)