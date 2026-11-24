import re
import unicodedata

import requests

from config import URL_RECEITAS


# Estes dicionários traduzem termos frequentes sem depender de outra API.
NOMES = {
    "lasanha": "lasagne",
    "macarrao": "pasta",
    "espaguete": "spaghetti",
    "panqueca": "pancakes",
    "panquecas": "pancakes",
    "bolo": "cake",
    "sopa": "soup",
    "omelete": "omelette",
    "frango": "chicken",
    "arroz": "rice",
    "salada": "salad",
    "pizza": "pizza",
    "torta": "pie",
}

INGREDIENTES = {
    "frango": "chicken",
    "peito de frango": "chicken breast",
    "batata": "potato",
    "batatas": "potato",
    "batata doce": "sweet potato",
    "cebola": "onion",
    "cebolas": "onion",
    "tomate": "tomato",
    "tomates": "tomato",
    "ovo": "egg",
    "ovos": "egg",
    "leite": "milk",
    "queijo": "cheese",
    "manteiga": "butter",
    "alho": "garlic",
    "sal": "salt",
    "pimenta": "pepper",
    "azeite": "olive oil",
    "oleo": "oil",
    "arroz": "rice",
    "macarrao": "pasta",
    "farinha": "flour",
    "farinha de trigo": "flour",
    "acucar": "sugar",
    "cenoura": "carrot",
    "cenouras": "carrot",
    "carne": "beef",
    "carne moida": "minced beef",
    "peixe": "fish",
    "banana": "banana",
    "bananas": "banana",
    "morango": "strawberry",
    "morangos": "strawberry",
    "camarao": "prawns",
    "limao": "lemon",
    "brocolis": "broccoli",
    "cogumelo": "mushrooms",
    "milho": "sweetcorn",
    "feijao": "beans",
    "abobrinha": "courgette",
    "pimentao": "bell pepper",
    "abacate": "avocado",
    "mel": "honey",
    "iogurte": "yogurt",
    "chocolate": "chocolate",
}

EQUIVALENCIAS = {
    "potatoes": "potato",
    "onions": "onion",
    "tomatoes": "tomato",
    "eggs": "egg",
    "carrots": "carrot",
    "mushrooms": "mushroom",
    "mushroom": "mushroom",
    "flour": "flour",
    "plain flour": "flour",
    "all purpose flour": "flour",
    "self raising flour": "flour",
    "chicken breast": "chicken",
    "chicken breasts": "chicken",
    "chicken thighs": "chicken",
    "chicken": "chicken",
    "minced beef": "beef",
    "ground beef": "beef",
    "beef": "beef",
    "prawns": "prawn",
    "prawn": "prawn",
    "shrimp": "prawn",
    "courgette": "courgette",
    "zucchini": "courgette",
    "sweet potatoes": "sweet potato",
    "olive oil": "oil",
    "vegetable oil": "oil",
    "oil": "oil",
    "rice": "rice",
    "long grain rice": "rice",
    "basmati rice": "rice",
    "pasta": "pasta",
    "spaghetti": "pasta",
    "macaroni": "pasta",
}

TRADUCOES = {
    "chicken": "frango",
    "chicken breast": "peito de frango",
    "chicken thighs": "coxa de frango",
    "potato": "batata",
    "potatoes": "batatas",
    "onion": "cebola",
    "onions": "cebolas",
    "tomato": "tomate",
    "tomatoes": "tomates",
    "garlic": "alho",
    "egg": "ovo",
    "eggs": "ovos",
    "milk": "leite",
    "cheese": "queijo",
    "butter": "manteiga",
    "salt": "sal",
    "sugar": "açúcar",
    "pepper": "pimenta",
    "olive oil": "azeite",
    "flour": "farinha de trigo",
    "plain flour": "farinha de trigo",
    "carrot": "cenoura",
    "carrots": "cenouras",
    "rice": "arroz",
    "chocolate": "chocolate",
    "mushrooms": "cogumelos",
    "lemon": "limão",
    "honey": "mel",
    "yogurt": "iogurte",
    "pasta": "macarrão",
    "beef": "carne bovina",
    "minced beef": "carne moída",
    "prawns": "camarão",
    "banana": "banana",
    "strawberry": "morango",
    "sweet potato": "batata-doce",
    "fish": "peixe",
    "broccoli": "brócolis",
    "sweetcorn": "milho",
    "beans": "feijão",
    "courgette": "abobrinha",
    "bell pepper": "pimentão",
}


class ErroReceita(Exception):
    pass


# Remove acentos e diferenças de escrita para comparar ingredientes de forma consistente.
def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", texto).split())


def nome_ingles(texto):
    termo = normalizar(texto)
    return NOMES.get(termo, termo)


def ingrediente_ingles(texto):
    termo = normalizar(texto)
    return INGREDIENTES.get(termo, termo)


def chave_ingrediente(texto):
    termo = normalizar(ingrediente_ingles(texto))
    return EQUIVALENCIAS.get(termo, termo)


# Considera nomes equivalentes e variações simples, sem avaliar quantidade disponível.
def disponivel(nome, itens):
    chave = chave_ingrediente(nome)
    return any(
        chave == item or chave.startswith(item + " ") or item.startswith(chave + " ")
        for item in itens
    )


def interpretar_itens(texto):
    partes = re.split(r"[,;\n]|\s+e\s+", texto or "")
    return list(dict.fromkeys(chave_ingrediente(parte) for parte in partes if normalizar(parte)))


# Centraliza o acesso HTTP, o tempo limite e a validação da resposta da TheMealDB.
def _consultar(caminho, parametros):
    try:
        resposta = requests.get(f"{URL_RECEITAS}/{caminho}", params=parametros, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()
        if not isinstance(dados, dict) or "meals" not in dados:
            raise ValueError("Resposta inesperada do serviço de receitas.")
        refeicoes = dados["meals"]
        if refeicoes is None:
            return [], resposta.url
        if not isinstance(refeicoes, list) or any(not isinstance(item, dict) for item in refeicoes):
            raise ValueError("Resposta inesperada do serviço de receitas.")
        return refeicoes, resposta.url
    except (requests.RequestException, ValueError) as erro:
        raise ErroReceita("Não foi possível consultar a base de receitas.") from erro


def _resumo(refeicao):
    return {
        "id": str(refeicao.get("idMeal", "")),
        "nome_original": refeicao.get("strMeal", ""),
        "imagem": refeicao.get("strMealThumb", ""),
    }


def buscar_por_nome(consulta):
    termo = nome_ingles(consulta)
    if not termo or len(termo) > 90:
        raise ValueError("Informe o nome de um prato de até 90 caracteres.")
    refeicoes, fonte = _consultar("search.php", {"s": termo})
    return {"modo": "nome", "consulta": consulta, "resultados": [_resumo(r) for r in refeicoes[:8]], "fonte": fonte}


# Os ingredientes vêm de até 20 campos numerados fornecidos pela TheMealDB.
def detalhes_receita(id_receita):
    codigo = str(id_receita).strip()
    if not codigo.isdigit() or len(codigo) > 15:
        raise ValueError("Informe um identificador numérico de receita válido.")
    refeicoes, fonte = _consultar("lookup.php", {"i": codigo})
    if not refeicoes:
        return None
    refeicao = refeicoes[0]
    ingredientes = []
    for numero in range(1, 21):
        ingrediente = (refeicao.get(f"strIngredient{numero}") or "").strip()
        if ingrediente:
            medida = (refeicao.get(f"strMeasure{numero}") or "").strip()
            ingredientes.append({"nome": TRADUCOES.get(normalizar(ingrediente), ingrediente), "nome_original": ingrediente, "quantidade_original": medida})
    return {
        **_resumo(refeicao),
        "categoria": refeicao.get("strCategory", ""),
        "origem": refeicao.get("strArea", ""),
        "ingredientes": ingredientes,
        "preparo_original": refeicao.get("strInstructions", "") or "",
        "fonte": refeicao.get("strSource") or fonte,
        "consulta_api": fonte,
        "video": refeicao.get("strYoutube") or "",
    }


# A API gratuita aceita um ingrediente por busca; combinamos resultados e avaliamos os detalhes.
def buscar_por_ingredientes(consulta):
    ingredientes = interpretar_itens(consulta)
    if not ingredientes:
        raise ValueError("Informe pelo menos um ingrediente.")
    pesquisados = ingredientes[:3]
    encontrados = {}
    fontes = []
    for termo in pesquisados:
        refeicoes, fonte = _consultar("filter.php", {"i": termo.replace(" ", "_")})
        fontes.append(fonte)
        for refeicao in refeicoes:
            codigo = str(refeicao.get("idMeal", ""))
            if codigo and codigo not in encontrados:
                encontrados[codigo] = {"refeicao": refeicao, "frequencia": 0}
            if codigo:
                encontrados[codigo]["frequencia"] += 1
    # Primeiro seleciona pratos encontrados em mais pesquisas de ingredientes.
    candidatos = sorted(
        encontrados.values(),
        key=lambda item: (-item["frequencia"], item["refeicao"].get("strMeal", "")),
    )[:8]
    resultados = []
    for candidato in candidatos:
        detalhe = detalhes_receita(candidato["refeicao"]["idMeal"])
        if detalhe is None:
            continue
        aproveitados = [
            item["nome"]
            for item in detalhe["ingredientes"]
            if disponivel(item["nome_original"], ingredientes)
        ]
        resultados.append({
            **_resumo(candidato["refeicao"]),
            "ingredientes_aproveitados": aproveitados,
            "total_ingredientes": len(detalhe["ingredientes"]),
            "faltam_itens": len(detalhe["ingredientes"]) - len(aproveitados),
        })
    # Depois ordena pela quantidade de ingredientes aproveitados e pelos itens faltantes.
    resultados.sort(key=lambda item: (-len(item["ingredientes_aproveitados"]), item["faltam_itens"], item["nome_original"]))
    return {
        "modo": "ingredientes",
        "consulta": consulta,
        "ingredientes_considerados": pesquisados,
        "resultados": resultados[:6],
        "fonte": fontes,
        "observacao": "A busca consulta no máximo três ingredientes por vez e combina pesquisas individuais. A correspondência é aproximada; confirme itens e quantidades antes de cozinhar.",
    }
