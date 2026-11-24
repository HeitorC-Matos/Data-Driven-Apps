import sqlite3
from contextlib import closing

from config import BANCO_DADOS
from receitas import detalhes_receita, disponivel, interpretar_itens, normalizar


# A base local guarda as listas e é criada automaticamente no primeiro acesso.
def conectar():
    BANCO_DADOS.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(str(BANCO_DADOS), timeout=10)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


# As tabelas são criadas somente se ainda não existirem no banco SQLite.
def iniciar_banco():
    with closing(conectar()) as conexao:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS listas (
                conversa_id TEXT PRIMARY KEY,
                receita_id TEXT NOT NULL,
                nome_receita TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversa_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                quantidade TEXT NOT NULL DEFAULT '',
                comprado INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (conversa_id) REFERENCES listas(conversa_id) ON DELETE CASCADE
            );
        """)
        conexao.commit()


# As consultas sempre filtram pelo ID da conversa para não misturar listas.
def ver_lista(conversa_id):
    iniciar_banco()
    with closing(conectar()) as conexao:
        lista = conexao.execute("SELECT * FROM listas WHERE conversa_id = ?", (conversa_id,)).fetchone()
        if lista is None:
            return {"erro": "Nenhuma lista foi criada nesta conversa."}
        registros = conexao.execute("SELECT * FROM itens WHERE conversa_id = ? ORDER BY id", (conversa_id,)).fetchall()
        return {
            "receita_id": lista["receita_id"],
            "receita": lista["nome_receita"],
            "itens": [
                {"id": item["id"], "nome": item["nome"], "quantidade": item["quantidade"], "comprado": bool(item["comprado"])}
                for item in registros
            ],
        }


# A lista utiliza dados da receita consultada e nunca presume quantidades suficientes em casa.
def criar_lista(conversa_id, receita_id, disponiveis=""):
    iniciar_banco()
    receita = detalhes_receita(receita_id)
    if receita is None:
        return {"erro": "Receita não encontrada. Pesquise outra receita."}
    existentes = interpretar_itens(disponiveis)
    faltantes = [item for item in receita["ingredientes"] if not disponivel(item["nome_original"], existentes)]
    # Ao escolher uma nova receita, a lista anterior é substituída na mesma transação.
    with closing(conectar()) as conexao:
        with conexao:
            conexao.execute("INSERT OR REPLACE INTO listas (conversa_id, receita_id, nome_receita) VALUES (?, ?, ?)", (conversa_id, receita["id"], receita["nome_original"]))
            conexao.execute("DELETE FROM itens WHERE conversa_id = ?", (conversa_id,))
            conexao.executemany(
                "INSERT INTO itens (conversa_id, nome, quantidade) VALUES (?, ?, ?)",
                [(conversa_id, item["nome"], item["quantidade_original"]) for item in faltantes],
            )
    resultado = ver_lista(conversa_id)
    resultado["observacao"] = "Itens informados como disponíveis foram omitidos. Confira se as quantidades em casa são suficientes. Medidas seguem a receita original."
    return resultado


def adicionar_item(conversa_id, nome, quantidade=""):
    nome = nome.strip()
    if not nome or len(nome) > 120 or len(quantidade) > 80:
        return {"erro": "Informe um item válido (até 120 caracteres) e uma quantidade de até 80 caracteres."}
    if "erro" in ver_lista(conversa_id):
        return {"erro": "Crie uma lista antes de adicionar itens."}
    with closing(conectar()) as conexao:
        with conexao:
            conexao.execute("INSERT INTO itens (conversa_id, nome, quantidade) VALUES (?, ?, ?)", (conversa_id, nome, quantidade))
    return ver_lista(conversa_id)


# Aceita nome ou ID do item, mas só modifica registros da conversa ativa.
def alterar_item(conversa_id, item, acao):
    if acao not in ("marcar", "desmarcar", "remover"):
        return {"erro": "Ação inválida."}
    lista = ver_lista(conversa_id)
    if "erro" in lista:
        return lista
    texto = str(item).strip()
    selecionado = next(
        (entrada for entrada in lista["itens"] if str(entrada["id"]) == texto or normalizar(entrada["nome"]) == normalizar(texto)),
        None,
    )
    if selecionado is None:
        return {"erro": "Item não encontrado na lista de compras."}
    with closing(conectar()) as conexao:
        with conexao:
            if acao == "remover":
                conexao.execute("DELETE FROM itens WHERE conversa_id = ? AND id = ?", (conversa_id, selecionado["id"]))
            else:
                conexao.execute("UPDATE itens SET comprado = ? WHERE conversa_id = ? AND id = ?", (1 if acao == "marcar" else 0, conversa_id, selecionado["id"]))
    return ver_lista(conversa_id)


# Centraliza as ações que a ferramenta de compras disponibiliza ao agente.
def executar_compras(conversa_id, acao, receita_id="", ingredientes_disponiveis="", item="", quantidade=""):
    if acao == "criar":
        if not receita_id:
            return {"erro": "Informe o identificador da receita selecionada."}
        return criar_lista(conversa_id, receita_id, ingredientes_disponiveis)
    if acao == "ver":
        return ver_lista(conversa_id)
    if acao == "adicionar":
        return adicionar_item(conversa_id, item, quantidade)
    if acao in ("marcar", "desmarcar", "remover"):
        return alterar_item(conversa_id, item, acao)
    return {"erro": "Ação desconhecida. Utilize criar, ver, adicionar, marcar, desmarcar ou remover."}
