"""
models/__init__.py — ¿Para qué sirve este archivo?
==================================================

Igual que en agent/: convierte la carpeta models/ en un paquete de
Python e "importable". Y de paso expone los modelos que definimos en
schemas.py para que se puedan importar cómodamente.

Recuerda que "models/__init__.py" vacío también funcionaría (un archivo
vacío ya convierte la carpeta en paquete); pero aquí aprovechamos para
re-exportar los nombres principales.

Fíjate en cómo main.py lo usa en realidad:
    from models.schemas import ChatRequest, ChatResponse
Es decir, main.py importa directamente desde el módulo interno
"schemas". Entonces, ¿por qué re-exportar? Por convención y por
comodidad: si alguien prefiere "from models import ChatRequest",
también funciona. Ambas vías son válidas.
"""

from .schemas import ChatRequest, ChatResponse

# __all__ indica qué se exporta con "from models import *".
# Al igual que en agent/, es la "carta de presentación" del paquete.
__all__ = ["ChatRequest", "ChatResponse"]