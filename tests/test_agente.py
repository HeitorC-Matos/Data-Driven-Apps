import pytest

pytest.importorskip("langchain")

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agente import carregar_historico, configurar_conversa, mensagem_erro, responder


class AgenteFalso:
    def invoke(self, dados, config):
        self.config = config
        return {
            "messages": [
                HumanMessage(content=dados["messages"][0]["content"]),
                AIMessage(content="", tool_calls=[{"name": "buscar_receitas", "args": {"tipo": "nome"}, "id": "chamada-1"}]),
                ToolMessage(content='{"resultados":[{"id":"12345"}]}', name="buscar_receitas", tool_call_id="chamada-1"),
                AIMessage(content="Encontrei uma receita."),
            ]
        }

    def get_state(self, config):
        class Estado:
            values = {"messages": [
                HumanMessage(content="Quero lasanha"),
                AIMessage(content="", tool_calls=[{"name": "buscar_receitas", "args": {"tipo": "nome"}, "id": "chamada-1"}]),
                ToolMessage(content='{"resultados":[{"id":"12345"}]}', name="buscar_receitas", tool_call_id="chamada-1"),
                AIMessage(content="Encontrei uma receita."),
            ]}
        return Estado()


def test_registro_da_ferramenta():
    agente = AgenteFalso()
    resposta, observacoes = responder(agente, "Quero lasanha", "sessao-1")
    assert resposta == "Encontrei uma receita."
    assert observacoes[0]["ferramenta"] == "buscar_receitas"
    assert observacoes[0]["resultado"]["resultados"][0]["id"] == "12345"
    assert agente.config == configurar_conversa("sessao-1")


def test_recuperar_historico_com_observacoes():
    historico = carregar_historico(AgenteFalso(), "sessao-1")
    assert [mensagem["papel"] for mensagem in historico] == ["user", "assistant"]
    assert historico[1]["ferramentas"][0]["resultado"]["resultados"][0]["id"] == "12345"


def test_mensagens_de_erro():
    assert "cota" in mensagem_erro(Exception("429 RESOURCE_EXHAUSTED")).lower()
    assert "indisponível" in mensagem_erro(Exception("503 UNAVAILABLE")).lower()
    assert "modelo" in mensagem_erro(Exception("404 NOT_FOUND")).lower()
    assert "conectar" in mensagem_erro(Exception("Connection refused")).lower()
