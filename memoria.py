import sqlite3
from functools import lru_cache

from langgraph.checkpoint.sqlite import SqliteSaver

from config import BANCO_MEMORIA


# Reutiliza uma única instância do checkpointer para evitar conexões repetidas no Streamlit.
@lru_cache(maxsize=4)
def _memoria_por_caminho(caminho):
    conexao = sqlite3.connect(caminho, check_same_thread=False, timeout=30)
    return SqliteSaver(conexao)


def criar_memoria():
    BANCO_MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    return _memoria_por_caminho(str(BANCO_MEMORIA))
