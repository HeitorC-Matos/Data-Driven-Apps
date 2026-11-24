import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("TESTAR_MODELO_REAL") != "1",
    reason="Habilite TESTAR_MODELO_REAL=1 quando houver um modelo configurado e disponível.",
)


def test_resposta_modelo_real():
    from agente import criar_modelo
    from langchain_core.messages import HumanMessage

    resposta = criar_modelo().invoke([HumanMessage(content="Responda apenas: OK")])
    assert str(resposta.content).strip()
