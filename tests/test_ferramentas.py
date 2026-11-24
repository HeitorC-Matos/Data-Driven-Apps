import json

import pytest

pytest.importorskip("langchain")

import ferramentas


def test_duas_ferramentas(monkeypatch):
    ferramenta_lista = ferramentas.criar_ferramenta_compras("sessao-1")
    assert ferramentas.buscar_receitas.name == "buscar_receitas"
    assert ferramenta_lista.name == "gerenciar_lista_compras"
    monkeypatch.setattr(ferramentas, "buscar_por_nome", lambda termo: {"resultados": [{"id": "12345"}]})
    resposta = json.loads(ferramentas.buscar_receitas.invoke({"tipo": "nome", "consulta": "lasanha"}))
    assert resposta["resultados"][0]["id"] == "12345"


def test_ferramenta_compras_usa_sessao(monkeypatch):
    observado = {}

    def simulador(conversa_id, acao, receita_id, ingredientes_disponiveis, item, quantidade):
        observado["conversa"] = conversa_id
        return {"itens": []}

    monkeypatch.setattr(ferramentas, "executar_compras", simulador)
    ferramenta = ferramentas.criar_ferramenta_compras("minha-sessao")
    resposta = json.loads(ferramenta.invoke({"acao": "ver"}))
    assert observado["conversa"] == "minha-sessao"
    assert resposta["itens"] == []
