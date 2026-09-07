"""
models/schemas.py — Contratos de datos (Pydantic)
=================================================

Pydantic valida y convierte datos de entrada/salida de la API.
Definir los modelos aquí es como firmar un "contrato": garantiza
que lo que entra y sale del servidor cumple siempre una forma
esperada, evitando errores silenciosos.

¿Por qué es útil?
- Si el cliente manda un JSON sin el campo "message" → 422 (error
  de validación) automático, sin escribir ni una línea de lógica.
- La documentación automática de FastAPI (Swagger en /docs) se
  genera a partir de estos modelos, con descripciones y todo.
"""

from pydantic import BaseModel, Field

# ----------------------------------------------------------------
# BaseModel: base de Pydantic. Al heredar de ella, cada atributo de
# la clase valida automáticamente el dato que recibe.
#
# Field(..., ...): configuración por atributo:
#   Field(..., min_length=1): el "..." significa "requerido/obligatorio"
#     (no tiene valor por defecto). Si lo omitimos, el campo es opcional.
#     min_length=1 evita mensajes vacíos ("") de un solo carácter.
#
# El tipo con `| None` (p. ej. `str | None`) indica que el campo es
# opcional y puede ser nulo. Equivale a: o es str, o es None.
# ----------------------------------------------------------------


class ChatRequest(BaseModel):
    """Estructura del JSON que el cliente debe enviar para chatear.

    Ejemplo de POST a /chat:
        {
            "message": "¿Qué significa el bautismo?",
            "conversation_id": "abc-123"   ← opcional
        }
    """
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    conversation_id: str | None = Field(None, description="ID de la conversación para mantener contexto")


class ChatResponse(BaseModel):
    """Estructura del JSON que la API devuelve al cliente.

    Ejemplo de respuesta:
        {
            "response": "El bautismo significa...",
            "conversation_id": "abc-123",
            "tools_used": ["theological_search"]
        }
    """
    response: str = Field(..., description="Respuesta del agente")
    conversation_id: str = Field(..., description="ID de la conversación")
    tools_used: list[str] = Field(default_factory=list, description="Herramientas utilizadas")
    # Nota sobre default_factory=list: usamos una función () -> [] en
    # vez de "default=[]" por seguridad. Si usáramos default=[] (una
    # misma lista compartida), todas las instancias del modelo podrían
    # compartir el MISMO objeto lista y mutarse entre ellas. Con la
    # factory, cada instancia crea SU PROPIA lista. Detalle importante
    # de Python: nunca uses listas/dicts mutables como valor por defecto.

# ----------------------------------------------------------------
# Modelo mental
# ----------------------------------------------------------------
# FastAPI usa estos modelos en dos momentos:
#   1. request_model / el parámetro del endpoint → valida la ENTRADA.
#   2. response_model en el decorador              → valida la SALIDA.
# La API queda "auto-documentada" y a prueba de errores de formato.
# ----------------------------------------------------------------