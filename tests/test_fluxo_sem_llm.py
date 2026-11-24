import ast
from pathlib import Path

import compras
import receitas
from test_receitas import REFEICAO


def test_receita_e_compras_na_mesma_sessao(monkeypatch, tmp_path):
    monkeypatch.setattr(compras, "BANCO_DADOS", tmp_path / "compras.sqlite")
    monkeypatch.setattr(receitas, "_consultar", lambda caminho, parametros: ([REFEICAO], "https://www.themealdb.com/api/json/v1/1/lookup.php"))
    monkeypatch.setattr(compras, "detalhes_receita", receitas.detalhes_receita)
    resultado = receitas.buscar_por_nome("frango")
    assert resultado["resultados"]
    codigo = resultado["resultados"][0]["id"]
    receita = receitas.detalhes_receita(codigo)
    assert receita["ingredientes"]
    lista = compras.executar_compras("sessao-teste", "criar", codigo, "frango")
    assert lista["receita_id"] == codigo
    assert lista["itens"]
    assert compras.ver_lista("sessao-teste")["itens"] == lista["itens"]


def test_lista_persistida_entre_acessos(monkeypatch, tmp_path):
    monkeypatch.setattr(compras, "BANCO_DADOS", tmp_path / "compras.sqlite")
    monkeypatch.setattr(compras, "detalhes_receita", lambda codigo: {
        "id": codigo, "nome_original": "Exemplo", "ingredientes": [
            {"nome": "sal", "nome_original": "Salt", "quantidade_original": "1 tsp"}
        ]
    })
    compras.criar_lista("sessao", "12345")
    item = compras.ver_lista("sessao")["itens"][0]
    compras.alterar_item("sessao", str(item["id"]), "marcar")
    assert compras.ver_lista("sessao")["itens"][0]["comprado"] is True
    assert "erro" in compras.ver_lista("outra-sessao")


def test_estrutura_do_agente_e_interface():
    raiz = Path(__file__).resolve().parents[1]
    agente = ast.parse((raiz / "agente.py").read_text(encoding="utf-8"))
    interface = ast.parse((raiz / "app.py").read_text(encoding="utf-8"))
    nome_funcoes = {item.name for item in agente.body if isinstance(item, ast.FunctionDef)}
    assert {"criar_agente", "responder", "carregar_historico"}.issubset(nome_funcoes)
    assert any(isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "create_agent" for item in ast.walk(agente))
    assert any(isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == "chat_input" for item in ast.walk(interface))
