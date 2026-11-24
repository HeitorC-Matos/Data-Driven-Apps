import pytest

pytest.importorskip("langchain")
pytest.importorskip("langgraph")

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

import agente
import compras
import ferramentas


# Respostas simuladas reproduzem chamadas de ferramentas sem consumir cota Gemini.
class ModeloSimulado(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def resposta_ferramenta(nome, argumentos, identificador):
    return AIMessage(content="", tool_calls=[{"name": nome, "args": argumentos, "id": identificador}])


# Verifica seleção das duas ferramentas, continuidade da conversa e isolamento entre sessões.
def test_ciclo_com_duas_ferramentas_e_memoria(monkeypatch, tmp_path):
    monkeypatch.setattr(compras, "BANCO_DADOS", tmp_path / "compras.sqlite")
    monkeypatch.setattr(ferramentas, "buscar_por_nome", lambda termo: {"resultados": [{"id": "12345", "nome_original": "Frango com batatas"}]})
    monkeypatch.setattr(compras, "detalhes_receita", lambda codigo: {
        "id": codigo,
        "nome_original": "Frango com batatas",
        "ingredientes": [
            {"nome": "frango", "nome_original": "Chicken", "quantidade_original": "500 g"},
            {"nome": "sal", "nome_original": "Salt", "quantidade_original": "1 tsp"},
        ],
    })
    modelo = ModeloSimulado(responses=[
        resposta_ferramenta("buscar_receitas", {"tipo": "nome", "consulta": "frango"}, "chamada-1"),
        AIMessage(content="Encontrei Frango com batatas (ID 12345)."),
        resposta_ferramenta("gerenciar_lista_compras", {"acao": "criar", "receita_id": "12345", "ingredientes_disponiveis": "frango"}, "chamada-2"),
        AIMessage(content="A lista foi criada com sal."),
        resposta_ferramenta("gerenciar_lista_compras", {"acao": "ver"}, "chamada-3"),
        AIMessage(content="Ainda falta comprar sal."),
    ])
    monkeypatch.setattr(agente, "criar_modelo", lambda: modelo)
    monkeypatch.setattr(agente, "criar_memoria", lambda: InMemorySaver())
    fluxo = agente.criar_agente("sessao-teste")

    primeira, chamadas_1 = agente.responder(fluxo, "Quero uma receita com frango", "sessao-teste")
    segunda, chamadas_2 = agente.responder(fluxo, "Crie a lista. Tenho frango.", "sessao-teste")
    terceira, chamadas_3 = agente.responder(fluxo, "O que falta comprar?", "sessao-teste")

    assert "12345" in primeira
    assert "sal" in segunda
    assert "sal" in terceira
    assert [chamada["ferramenta"] for chamada in chamadas_1] == ["buscar_receitas"]
    assert [chamada["ferramenta"] for chamada in chamadas_2] == ["gerenciar_lista_compras"]
    assert [chamada["ferramenta"] for chamada in chamadas_3] == ["gerenciar_lista_compras"]
    assert compras.ver_lista("sessao-teste")["itens"][0]["nome"] == "sal"
    historico = agente.carregar_historico(fluxo, "sessao-teste")
    assert len(historico) == 6
    assert len([m for m in historico if m["papel"] == "assistant" and m["ferramentas"]]) == 3
    assert agente.carregar_historico(fluxo, "outra-sessao") == []
