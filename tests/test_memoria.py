import pytest

pytest.importorskip("langgraph.checkpoint.sqlite")

import memoria


def test_memoria_sqlite(monkeypatch, tmp_path):
    banco = tmp_path / "historico.sqlite"
    monkeypatch.setattr(memoria, "BANCO_MEMORIA", banco)
    saver = memoria.criar_memoria()
    assert banco.exists()
    assert saver is not None
    memoria._memoria_por_caminho.cache_clear()
    saver.conn.close()


def test_historico_persiste_ao_recriar_agente(monkeypatch, tmp_path):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage

    import agente

    class ModeloLocalDeTeste(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    banco = tmp_path / "historico-reaberto.sqlite"
    monkeypatch.setattr(memoria, "BANCO_MEMORIA", banco)
    monkeypatch.setattr(agente, "criar_modelo", lambda: ModeloLocalDeTeste(responses=[AIMessage(content="Receita encontrada.")]))

    primeiro = agente.criar_agente("conversa-persistente")
    resposta, _ = agente.responder(primeiro, "Quero preparar uma receita", "conversa-persistente")
    assert resposta == "Receita encontrada."

    saver = memoria.criar_memoria()
    saver.conn.close()
    memoria._memoria_por_caminho.cache_clear()

    segundo = agente.criar_agente("conversa-persistente")
    historico = agente.carregar_historico(segundo, "conversa-persistente")
    assert [mensagem["papel"] for mensagem in historico] == ["user", "assistant"]
    assert historico[-1]["texto"] == "Receita encontrada."
    memoria.criar_memoria().conn.close()
    memoria._memoria_por_caminho.cache_clear()
