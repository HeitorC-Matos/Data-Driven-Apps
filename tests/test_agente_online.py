import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("TESTAR_AGENTE_REAL") != "1",
    reason="O teste de ponta a ponta usa um modelo real e a API TheMealDB. Habilite TESTAR_AGENTE_REAL=1.",
)


def test_ponta_a_ponta_com_react_e_memoria(monkeypatch, tmp_path):
    import agente
    import compras
    import memoria

    monkeypatch.setattr(compras, "BANCO_DADOS", tmp_path / "compras.sqlite")
    monkeypatch.setattr(memoria, "BANCO_MEMORIA", tmp_path / "memoria.sqlite")
    conversa_id = str(uuid.uuid4())
    fluxo = agente.criar_agente(conversa_id)

    primeira, observacoes = agente.responder(
        fluxo,
        "Use a ferramenta buscar_receitas com tipo nome e consulta Arrabiata. Mostre as receitas encontradas e os respectivos IDs.",
        conversa_id,
    )
    buscas = [obs for obs in observacoes if obs["ferramenta"] == "buscar_receitas"]
    assert buscas, primeira
    resultados = next((obs["resultado"].get("resultados", []) for obs in buscas if obs["resultado"].get("resultados")), [])
    assert resultados, observacoes
    receita_id = resultados[0]["id"]

    segunda, observacoes = agente.responder(
        fluxo,
        f"Agora use gerenciar_lista_compras com ação criar para a receita de ID {receita_id}. Não tenho nenhum ingrediente em casa. Mostre a lista criada.",
        conversa_id,
    )
    assert any(obs["ferramenta"] == "gerenciar_lista_compras" for obs in observacoes), segunda
    lista = compras.ver_lista(conversa_id)
    assert lista["receita_id"] == receita_id
    assert lista["itens"]
    assert len(agente.carregar_historico(fluxo, conversa_id)) >= 4
