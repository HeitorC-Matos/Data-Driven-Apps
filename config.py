import os
from pathlib import Path

from dotenv import load_dotenv


PASTA_PROJETO = Path(__file__).resolve().parent
load_dotenv(PASTA_PROJETO / ".env")

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
BANCO_DADOS = PASTA_PROJETO / "dados" / "compras.sqlite"
BANCO_MEMORIA = PASTA_PROJETO / "dados" / "conversas.sqlite"
URL_RECEITAS = "https://www.themealdb.com/api/json/v1/1"


def verificar_configuracao():
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        raise ValueError("Chave do Gemini não encontrada. Configure GOOGLE_API_KEY no arquivo .env.")
    if not MODELO:
        raise ValueError("Configure GEMINI_MODEL no arquivo .env.")


def verificar_chave():
    verificar_configuracao()
