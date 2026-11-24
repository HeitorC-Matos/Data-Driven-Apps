import json
from typing import Literal

from langchain.tools import tool

from compras import executar_compras
from receitas import ErroReceita, buscar_por_ingredientes, buscar_por_nome, detalhes_receita


# O formato JSON padroniza as observações que o agente recebe após cada ação.
def serializar(dados):
    return json.dumps(dados, ensure_ascii=False)


# Ferramenta 1: consulta a API pública de receitas e devolve dados estruturados ao agente.
@tool(
    "buscar_receitas",
    description="Pesquisa receitas reais na API TheMealDB. tipo='nome': usa consulta com nome de prato; tipo='ingredientes': usa consulta com ingredientes separados por vírgula; tipo='detalhe': usa id_receita de uma receita encontrada para obter ingredientes, quantidades, instruções e fonte. Use a ferramenta antes de recomendar ou explicar uma receita.",
)
def buscar_receitas(tipo: Literal["nome", "ingredientes", "detalhe"], consulta: str = "", id_receita: str = "") -> str:
    try:
        if tipo == "nome":
            return serializar(buscar_por_nome(consulta))
        if tipo == "ingredientes":
            return serializar(buscar_por_ingredientes(consulta))
        receita = detalhes_receita(id_receita)
        if receita is None:
            return serializar({"erro": "Receita não encontrada."})
        return serializar(receita)
    except (ErroReceita, ValueError) as erro:
        return serializar({"erro": str(erro)})


# Ferramenta 2: gerencia a lista persistente associada à conversa atual.
def criar_ferramenta_compras(conversa_id):
    # A função interna captura o ID da conversa, mantendo as compras isoladas por sessão.
    @tool(
        "gerenciar_lista_compras",
        description="Controla a lista de compras da conversa atual em SQLite. Ações: criar (precisa de receita_id e ingredientes_disponiveis, com itens separados por vírgula), ver, adicionar (item e quantidade), marcar, desmarcar ou remover (item: nome ou ID). Ao criar, consulta a receita original e inclui apenas os ingredientes que não foram informados como disponíveis. Não presume quantidades existentes.",
    )
    def gerenciar_lista_compras(
        acao: Literal["criar", "ver", "adicionar", "marcar", "desmarcar", "remover"],
        receita_id: str = "",
        ingredientes_disponiveis: str = "",
        item: str = "",
        quantidade: str = "",
    ) -> str:
        try:
            return serializar(executar_compras(conversa_id, acao, receita_id, ingredientes_disponiveis, item, quantidade))
        except (ErroReceita, ValueError) as erro:
            return serializar({"erro": str(erro)})

    return gerenciar_lista_compras
