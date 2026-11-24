import compras

from test_receitas import REFEICAO


def preparar(monkeypatch, tmp_path):
    monkeypatch.setattr(compras, "BANCO_DADOS", tmp_path / "compras.sqlite")
    monkeypatch.setattr(compras, "detalhes_receita", lambda codigo: {
        "id": codigo,
        "nome_original": REFEICAO["strMeal"],
        "ingredientes": [
            {"nome": "peito de frango", "nome_original": "Chicken Breast", "quantidade_original": "500 g"},
            {"nome": "batatas", "nome_original": "Potatoes", "quantidade_original": "3"},
            {"nome": "cebola", "nome_original": "Onion", "quantidade_original": "1"},
            {"nome": "sal", "nome_original": "Salt", "quantidade_original": "1 tsp"},
        ],
    })


def test_criar_lista_com_ingredientes_existentes(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    lista = compras.criar_lista("conversa-a", "12345", "frango, batata e cebola")
    assert len(lista["itens"]) == 1
    assert lista["itens"][0]["nome"] == "sal"
    assert lista["itens"][0]["quantidade"] == "1 tsp"


def test_criar_lista_sem_ingredientes(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    lista = compras.criar_lista("conversa-a", "12345")
    assert len(lista["itens"]) == 4


def test_adicionar_marcar_desmarcar_e_remover(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    compras.criar_lista("conversa-a", "12345", "frango, batata e cebola")
    lista = compras.adicionar_item("conversa-a", "pão", "2 unidades")
    assert len(lista["itens"]) == 2
    marcado = compras.alterar_item("conversa-a", "pão", "marcar")
    assert marcado["itens"][1]["comprado"]
    desmarcado = compras.alterar_item("conversa-a", "pão", "desmarcar")
    assert not desmarcado["itens"][1]["comprado"]
    removido = compras.alterar_item("conversa-a", "pão", "remover")
    assert len(removido["itens"]) == 1


def test_isolamento_por_conversa(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    compras.criar_lista("conversa-a", "12345")
    assert "erro" in compras.ver_lista("conversa-b")
    compras.criar_lista("conversa-b", "12345", "frango, batata, cebola, sal")
    assert len(compras.ver_lista("conversa-a")["itens"]) == 4
    assert len(compras.ver_lista("conversa-b")["itens"]) == 0


def test_erro_item_nao_encontrado(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    compras.criar_lista("conversa-a", "12345")
    assert "erro" in compras.alterar_item("conversa-a", "item inexistente", "marcar")
    assert "erro" in compras.adicionar_item("conversa-a", "")


def test_recriar_lista_substitui_anterior(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    compras.criar_lista("conversa-a", "12345")
    compras.adicionar_item("conversa-a", "extra")
    nova = compras.criar_lista("conversa-a", "12345", "frango, batata, cebola")
    assert [item["nome"] for item in nova["itens"]] == ["sal"]
