"""
agent/__init__.py — ¿Para qué sirve este archivo?
=================================================

Un archivo __init__.py dentro de una carpeta convierte esa carpeta en
un "paquete" (package) de Python. Es decir: le dice a Python que esa
carpeta puede importarse como módulo.

Sin este archivo, "import agent" fallaría.

Este __init__.py además hace DOS cosas útiles:
  1. EXPONE una API pública: agrupa los nombres más usados para poder
     hacer "from agent import create_agent" sin importar desde la
     ruta interna completa.
  2. Define __all__: la lista declarada de lo que se exporta al hacer
     "from agent import *".
"""

# ----------------------------------------------------------------
# Importaciones relativas.
# ----------------------------------------------------------------
# El punto "." delante del módulo ("from .agent import ...") significa
# "relativo a esta carpeta". Es decir: importa agent.py desde ESTE
# mismo paquete (agent/), no desde cualquier otro módulo llamado agent
# que haya en el sistema. Es la forma recomendada de importar dentro
# de un paquete.
#
# ¿Por qué re-exportar aquí? Porque quien consuma el paquete no tiene
# por qué saber que create_agent vive en agent/agent.py. Así podrá
# escribir "from agent import create_agent" y ya está.
from .agent import create_agent
from .tools import web_search, theological_search

# ----------------------------------------------------------------
# __all__ — el "índice público" del paquete.
# ----------------------------------------------------------------
# Es opcional pero es una buena práctica: define QUÉ nombres se
# exportan cuando alguien hace "from agent import *".
#
# Ventajas:
#   - El usuario ve de un vistazo todo lo que este paquete ofrece.
#   - Evita exportar cosas internas por accidente (por ejemplo, si
#     importáramos logging ó os aquí, no queremos que salgan con *).
#
# Fíjate: SystemMessage, AgentExecutor, etc. NO aparecen en __all__:
# son detalles de implementación interna, no parte de la API del
# paquete.
__all__ = ["create_agent", "web_search", "theological_search"]