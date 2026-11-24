import json
import uuid

import streamlit as st

from agente import carregar_historico, criar_agente, mensagem_erro, responder
from compras import adicionar_item, alterar_item, ver_lista
from config import MODELO
from ferramentas import buscar_receitas, criar_ferramenta_compras


st.set_page_config(page_title="Receitas & Compras IA", page_icon="🍲", layout="centered")
st.title("🍲 Receitas & Compras IA")
st.caption("Encontre receitas com o que tem em casa e organize sua lista de compras")


# Mantém o mesmo agente por sessão para preservar o estado entre atualizações da interface.
@st.cache_resource
def iniciar_agente(conversa_id):
    return criar_agente(conversa_id)


def exibir_observacoes(observacoes, titulo="Ferramentas utilizadas e resultados"):
    if observacoes:
        with st.expander(titulo):
            for observacao in observacoes:
                st.markdown(f"**{observacao['ferramenta']}**")
                st.json(observacao["resultado"])


# O identificador na URL permite retomar uma conversa após recarregar a página.
conversa_id = st.query_params.get("conversa", "")
try:
    conversa_id = str(uuid.UUID(conversa_id))
except (TypeError, AttributeError, ValueError):
    conversa_id = str(uuid.uuid4())
    st.query_params["conversa"] = conversa_id

# A lista de compras é apresentada separadamente do chat e pertence à conversa atual.
with st.sidebar:
    st.header("Minha cozinha")
    if st.button("Nova conversa", use_container_width=True):
        st.query_params["conversa"] = str(uuid.uuid4())
        st.rerun()
    st.caption(f"Modelo: Gemini ({MODELO})")
    st.divider()
    st.subheader("Lista de compras")
    lista = ver_lista(conversa_id)
    if "erro" in lista:
        st.caption("Ainda não há uma lista nesta conversa.")
    else:
        st.caption(f"Receita: {lista['receita']}")
        if not lista["itens"]:
            st.success("Não há itens pendentes nesta lista.")
        for item in lista["itens"]:
            col_check, col_excluir = st.columns([5, 1])
            with col_check:
                marcado = st.checkbox(
                    f"{item['nome']} · {item['quantidade']}",
                    value=item["comprado"],
                    key=f"comprado_{conversa_id}_{item['id']}",
                )
                if marcado != item["comprado"]:
                    alterar_item(conversa_id, str(item["id"]), "marcar" if marcado else "desmarcar")
                    st.rerun()
            with col_excluir:
                if st.button("✕", key=f"excluir_{conversa_id}_{item['id']}", help="Remover item"):
                    alterar_item(conversa_id, str(item["id"]), "remover")
                    st.rerun()
        with st.form(f"adicionar_{conversa_id}"):
            novo_item = st.text_input("Adicionar ingrediente")
            quantidade = st.text_input("Quantidade (opcional)")
            if st.form_submit_button("Adicionar à lista", use_container_width=True):
                resultado = adicionar_item(conversa_id, novo_item, quantidade)
                if "erro" in resultado:
                    st.warning(resultado["erro"])
                else:
                    st.rerun()
    st.divider()
    st.markdown("[Fonte das receitas: TheMealDB](https://www.themealdb.com/api.php)")
    st.caption("Histórico e listas são salvos neste computador.")

# Este painel chama as tools diretamente, sem enviar solicitações ao Gemini.
with st.expander("Testar as duas ferramentas sem gastar cota de IA"):
    st.caption("Executa as ferramentas reais diretamente. Isso permite verificar consultas e compras mesmo quando o modelo estiver indisponível; não substitui o teste do agente ReAct.")
    with st.form("teste_receitas"):
        tipo_busca = st.selectbox("Tipo de consulta", ["nome", "ingredientes", "detalhe"])
        busca = st.text_input("Nome do prato ou ingredientes", placeholder="lasanha ou frango, batata e cebola")
        identificador = st.text_input("ID da receita para consultar detalhes")
        if st.form_submit_button("Executar buscar_receitas"):
            try:
                resultado = json.loads(buscar_receitas.invoke({"tipo": tipo_busca, "consulta": busca, "id_receita": identificador}))
                st.session_state["teste_receitas_resultado"] = resultado
            except Exception as erro:
                st.session_state["teste_receitas_resultado"] = {"erro": mensagem_erro(erro)}
    if "teste_receitas_resultado" in st.session_state:
        st.json(st.session_state["teste_receitas_resultado"])
    with st.form("teste_compras"):
        receita_id = st.text_input("ID da receita para criar a lista")
        itens_casa = st.text_input("Ingredientes disponíveis", placeholder="frango, batata, cebola")
        if st.form_submit_button("Executar gerenciar_lista_compras"):
            try:
                tool = criar_ferramenta_compras(conversa_id)
                resultado = json.loads(tool.invoke({"acao": "criar", "receita_id": receita_id, "ingredientes_disponiveis": itens_casa}))
                st.session_state["teste_compras_resultado"] = resultado
            except Exception as erro:
                st.session_state["teste_compras_resultado"] = {"erro": mensagem_erro(erro)}
    if "teste_compras_resultado" in st.session_state:
        st.json(st.session_state["teste_compras_resultado"])
        st.caption("A lista salva pode aparecer na barra lateral após atualizar a página.")

# A interface mantém os testes das ferramentas disponíveis mesmo se o modelo não iniciar.
agente = None
historico = []
try:
    agente = iniciar_agente(conversa_id)
    historico = carregar_historico(agente, conversa_id)
except Exception as erro:
    st.warning(mensagem_erro(erro) if not isinstance(erro, ValueError) else str(erro))
    st.info("O teste direto das ferramentas acima continua disponível. Confira o arquivo .env para usar a conversa com IA.")

if agente is not None and not historico:
    st.info("Experimente: 'Tenho frango, batata e cebola. O que posso cozinhar?' ou 'Quero fazer lasanha'.")

# Exibe as mensagens salvas com as observações das ferramentas usadas em cada resposta.
for mensagem in historico:
    with st.chat_message(mensagem["papel"]):
        st.markdown(mensagem["texto"])
        exibir_observacoes(mensagem.get("ferramentas", []))

pergunta = st.chat_input("Diga os ingredientes que tem ou procure uma receita", disabled=agente is None)
if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Pesquisando receitas e preparando a resposta..."):
            try:
                texto, observacoes = responder(agente, pergunta, conversa_id)
                st.markdown(texto)
                exibir_observacoes(observacoes)
            except Exception as erro:
                st.error(mensagem_erro(erro))
                st.caption("As ferramentas podem ser testadas separadamente na seção acima, sem consumir cota do modelo.")
