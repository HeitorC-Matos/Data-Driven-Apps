import pytest

import receitas


class RespostaInvalida:
    url = "https://www.themealdb.com/api/json/v1/1/search.php"

    def raise_for_status(self):
        return None

    def json(self):
        return {"erro": "serviço indisponível"}


def test_resposta_inesperada_nao_produz_receita(monkeypatch):
    monkeypatch.setattr(receitas.requests, "get", lambda *args, **kwargs: RespostaInvalida())
    with pytest.raises(receitas.ErroReceita):
        receitas.buscar_por_nome("lasanha")


def test_mais_de_tres_ingredientes(monkeypatch):
    consultas = []

    class Resposta:
        url = "https://www.themealdb.com/teste"

        def raise_for_status(self):
            return None

        def json(self):
            return {"meals": []}

    def pesquisar(url, params, timeout):
        consultas.append(params["i"])
        return Resposta()

    monkeypatch.setattr(receitas.requests, "get", pesquisar)
    resultado = receitas.buscar_por_ingredientes("frango, batata, cebola, tomate")
    assert len(consultas) == 3
    assert len(resultado["ingredientes_considerados"]) == 3
    assert resultado["resultados"] == []


def test_resposta_de_tipo_incorreto(monkeypatch):
    class Resposta:
        url = "https://www.themealdb.com/teste"

        def raise_for_status(self):
            return None

        def json(self):
            return {"meals": "valor inválido"}

    monkeypatch.setattr(receitas.requests, "get", lambda *args, **kwargs: Resposta())
    with pytest.raises(receitas.ErroReceita):
        receitas.buscar_por_nome("lasanha")
