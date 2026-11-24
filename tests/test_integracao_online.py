import os

import pytest

import receitas


pytestmark = pytest.mark.skipif(
    os.getenv("TESTAR_APIS_REAIS") != "1",
    reason="Testes online opcionais: defina TESTAR_APIS_REAIS=1.",
)


def test_busca_nome_online():
    resultado = receitas.buscar_por_nome("Arrabiata")
    assert resultado["resultados"]
    assert all(item["id"].isdigit() for item in resultado["resultados"])


def test_detalhes_online():
    receita = receitas.detalhes_receita("52771")
    assert receita is not None
    assert receita["ingredientes"]
    assert receita["preparo_original"]
