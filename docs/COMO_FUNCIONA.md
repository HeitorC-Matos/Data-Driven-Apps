# Como funciona o Receitas & Compras IA

Este documento explica a aplicação em linguagem simples, desde a pergunta do usuário até a lista de compras.

## 1. Visão geral

O usuário conversa com uma interface criada em Streamlit. O agente é organizado pelo LangChain e utiliza o Google Gemini para escolher qual ferramenta chamar. Ele não precisa guardar receitas completas no projeto: as informações vêm de consultas à API TheMealDB.

Há duas ferramentas principais:

1. `buscar_receitas`: encontra pratos por nome ou ingrediente e obtém os detalhes de uma receita.
2. `gerenciar_lista_compras`: cria ou modifica uma lista de compras no SQLite, tomando como referência os ingredientes da receita encontrada.

## 2. A sequência de uma conversa

Imagine que o usuário escreva: "Tenho frango, batata e cebola. O que posso cozinhar?"

O fluxo previsto é:

1. O agente identifica a intenção de procurar receitas por ingredientes.
2. Chama `buscar_receitas` com o modo `ingredientes`.
3. A ferramenta traduz ingredientes comuns, consulta a TheMealDB e combina os resultados.
4. O agente recebe as opções encontradas e apresenta nomes, identificadores e dados da fonte.
5. O usuário escolhe um prato, por exemplo: "Quero a primeira opção".
6. O agente usa a memória da conversa para recuperar a referência e consulta o detalhamento pelo identificador.
7. Se o usuário pedir uma lista, o agente chama `gerenciar_lista_compras` com a receita e os ingredientes que a pessoa informou possuir.
8. A ferramenta recupera os ingredientes da receita, compara os nomes normalizados e grava os itens faltantes no banco local.
9. A lista aparece na barra lateral e pode ser editada pelo usuário.

Não há um roteiro fixo para todas as mensagens: a escolha da ferramenta é feita dinamicamente pelo agente. As chamadas e os resultados podem ser consultados em "Ferramentas utilizadas e resultados", inclusive após recarregar o histórico da conversa.

## 3. O que significa ReAct

ReAct é um padrão de execução de agentes que combina escolha de ações e observação dos resultados. No projeto, o modelo decide quando consultar a base de receitas ou o banco de compras. Após receber os dados, pode consultar outra ferramenta ou apresentar a resposta final.

O programa exibe as ferramentas chamadas e as respostas recebidas, mas não expõe o raciocínio interno privado do modelo.

## 4. Como é feita a pesquisa por ingredientes

A TheMealDB gratuita filtra por um ingrediente por consulta. Se a pessoa informar "frango, batata e cebola", o programa consulta separadamente os termos traduzidos para o inglês, reúne candidatos e examina os detalhes de até oito receitas promissoras. Em seguida, prioriza receitas que aproveitam mais ingredientes informados.

Isso não significa que a receita possa ser feita exclusivamente com esses ingredientes. O sistema mostra quantos itens ainda poderão ser necessários.

A correspondência é aproximada porque nomes de ingredientes nem sempre são idênticos. Exemplo: "frango" pode representar várias partes do frango. As quantidades não são comparadas, pois a pessoa normalmente informa apenas o nome dos ingredientes disponíveis.

## 5. Como a lista de compras é construída

A ferramenta recebe o identificador da receita e os ingredientes que o usuário já possui. Os dados completos vêm da mesma API. Se a receita pedir frango, batata, cebola e sal, e o usuário informar frango, batata e cebola, a lista incluirá somente sal.

O banco guarda as informações em duas tabelas: `listas` e `itens`. A primeira identifica a receita da conversa; a segunda guarda os ingredientes, suas quantidades originais e se já foram comprados.

A lista é associada a cada conversa e salva em `dados/compras.sqlite`. É possível consultá-la depois de fechar e reabrir o programa, desde que a conversa seja retomada pelo mesmo identificador.

## 6. Como a memória funciona

A memória conversacional é armazenada em `dados/conversas.sqlite` pelo LangGraph. Cada conversa recebe um identificador próprio e o histórico é recuperado quando a página é aberta novamente com o mesmo endereço.

Assim, frases como "mostre o preparo dessa" podem ser interpretadas com base nas mensagens anteriores. A memória não substitui a consulta à fonte: para obter ingredientes e instruções, a ferramenta usa o identificador real da receita.

## 7. Organização do código

- `app.py`: tela e interação com o usuário.
- `agente.py`: regras de comportamento do agente, chamada ao LLM e leitura do histórico.
- `ferramentas.py`: registro das duas ferramentas no LangChain.
- `receitas.py`: consulta, conversão e comparação de dados da TheMealDB.
- `compras.py`: armazenamento e edição de listas no SQLite.
- `memoria.py`: configuração da memória conversacional.
- `config.py`: variáveis de ambiente e caminhos do projeto.
- `tests/`: verificações automatizadas.

Os módulos foram separados para facilitar a leitura e permitir testar os serviços sem depender do Gemini. A interface também inclui uma seção que aciona diretamente as duas ferramentas para verificar pesquisa e listas sem usar cota de IA. Esse teste direto não substitui o teste do agente ReAct.

## 8. Limites do sistema

O Gemini pode atingir a cota gratuita da conta ou ficar temporariamente sobrecarregado. Quando isso ocorrer, as duas ferramentas podem ser testadas diretamente na interface, sem executar o modelo, mas a conversa com ReAct depende do Gemini. A API de receitas também pode estar indisponível, e algumas receitas não têm tradução ou fonte original separada do endpoint da API.

A aplicação não sabe quanto de cada ingrediente existe na casa do usuário. Por isso, mesmo quando um item é considerado disponível, a quantidade deve ser conferida. O projeto não calcula preços, não faz compras e não substitui cuidados de segurança alimentar.

## 9. Por que essa solução é diferente de uma pesquisa convencional

Na pesquisa convencional, a pessoa alterna entre sites de receitas e uma lista manual. Com o agente, a pesquisa, o detalhamento, a comparação de ingredientes e a manutenção da lista são coordenados por uma conversa. É um benefício funcional, mas precisa ser validado em uso real para afirmar qualquer redução específica de tempo.
