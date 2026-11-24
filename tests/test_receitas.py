import pytest
import requests

import receitas


class Resposta:
    def __init__(self, dados, url="https://www.themealdb.com/teste"):
        self.dados = dados
        self.url = url

    def raise_for_status(self):
        return None

    def json(self):
        return self.dados


REFEICAO = {
    "idMeal": "12345",
    "strMeal": "Chicken Potato Bake",
    "strMealThumb": "https://www.themealdb.com/images/test.jpg",
    "strIngredient1": "Chicken Breast",
    "strMeasure1": "500 g",
    "strIngredient2": "Potatoes",
    "strMeasure2": "3",
    "strIngredient3": "Onion",
    "strMeasure3": "1",
    "strIngredient4": "Salt",
    "strMeasure4": "1 tsp",
    "strInstructions": "Bake the chicken and potatoes.",
    "strSource": "https://example.com/recipe",
}


def fake_get(url, params, timeout):
    if url.endswith("search.php"):
        return Resposta({"meals": [REFEICAO]})
    if url.endswith("lookup.php"):
        return Resposta({"meals": [REFEICAO]})
    if url.endswith("filter.php"):
        return Resposta({"meals": [{"idMeal": "12345", "strMeal": "Chicken Potato Bake"}]})
    raise AssertionError(url)


def test_normalizar_e_traduzir():
    assert receitas.normalizar("  Cebóla, ") == "cebola"
    assert receitas.nome_ingles("lasanha") == "lasagne"
    assert receitas.ingrediente_ingles("batata") == "potato"


def test_ingredientes_compativeis():
    itens = receitas.interpretar_itens("frango, batata e cebola")
    assert itens == ["chicken", "potato", "onion"]
    assert receitas.disponivel("Chicken Breast", itens)
    assert receitas.disponivel("Potatoes", itens)
    assert not receitas.disponivel("Salt", itens)


def test_buscar_por_nome(monkeypatch):
    monkeypatch.setattr(receitas.requests, "get", fake_get)
    resultado = receitas.buscar_por_nome("lasanha")
    assert len(resultado["resultados"]) == 1
    assert resultado["resultados"][0]["id"] == "12345"


def test_buscar_por_ingredientes(monkeypatch):
    monkeypatch.setattr(receitas.requests, "get", fake_get)
    resultado = receitas.buscar_por_ingredientes("frango, batata e cebola")
    assert len(resultado["resultados"]) == 1
    assert len(resultado["resultados"][0]["ingredientes_aproveitados"]) == 3
    assert resultado["resultados"][0]["faltam_itens"] == 1


def test_detalhes_receita(monkeypatch):
    monkeypatch.setattr(receitas.requests, "get", fake_get)
    resultado = receitas.detalhes_receita("12345")
    assert resultado["ingredientes"][0]["nome"] == "peito de frango"
    assert resultado["ingredientes"][1]["quantidade_original"] == "3"
    assert resultado["preparo_original"] == "Bake the chicken and potatoes."


def test_receita_invalida():
    with pytest.raises(ValueError):
        receitas.detalhes_receita("abc123")
    with pytest.raises(ValueError):
        receitas.buscar_por_nome("")


def test_sem_resultados(monkeypatch):
    monkeypatch.setattr(receitas.requests, "get", lambda url, params, timeout: Resposta({"meals": None}))
    assert receitas.buscar_por_nome("prato desconhecido")["resultados"] == []
    assert receitas.detalhes_receita("12345") is None


def test_erro_http(monkeypatch):
    def falhar(url, params, timeout):
        raise requests.Timeout("Timeout")

    monkeypatch.setattr(receitas.requests, "get", falhar)
    with pytest.raises(receitas.ErroReceita):
        receitas.buscar_por_nome("lasanha")
