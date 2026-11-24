# 🍲 Receitas & Compras IA

**Receitas & Compras IA** é um assistente que ajuda a encontrar receitas, aproveitar ingredientes disponíveis em casa e organizar uma lista de compras. A aplicação funciona em português, oferece uma interface web simples e guarda o histórico de cada conversa.

O projeto foi desenvolvido em **Python**, com **LangChain**, **LangGraph**, **Google Gemini**, **TheMealDB**, **SQLite** e **Streamlit**.

## 1. Problema e proposta

Escolher o que cozinhar exige procurar receitas, conferir ingredientes, comparar com o que já existe em casa e anotar o que falta comprar. O Receitas & Compras IA reúne essas etapas em um único lugar.

**Público-alvo:** pessoas que cozinham no dia a dia, estudantes, iniciantes na cozinha e qualquer pessoa que queira organizar a preparação de refeições e as compras de ingredientes.

**Objetivo:** permitir que o usuário faça perguntas em linguagem natural, consulte receitas de uma fonte externa e mantenha uma lista de compras vinculada à conversa.

## 2. Funcionalidades

- **Buscar receitas pelo nome:** encontrar pratos como lasanha, panquecas ou massas.
- **Buscar pelo que há em casa:** informar ingredientes e receber sugestões relacionadas.
- **Ver os detalhes:** consultar ingredientes, quantidades e instruções de preparo.
- **Montar listas de compras:** comparar os ingredientes da receita com os itens disponíveis.
- **Editar a lista:** adicionar, marcar, desmarcar e remover produtos.
- **Continuar a conversa:** fazer perguntas como “E os ingredientes dessa receita?” ou “O que falta comprar?”.
- **Retomar o histórico:** preservar as mensagens e as listas em bancos SQLite locais.
- **Usar as ferramentas diretamente:** consultar receitas e criar listas pela interface, mesmo sem realizar chamadas ao Gemini.

### Exemplo de utilização

```text
Usuário: Tenho frango, batata e cebola. O que posso cozinhar?
Agente: Pesquisa receitas com esses ingredientes e apresenta opções encontradas.

Usuário: Mostre a primeira receita.
Agente: Consulta os detalhes e apresenta ingredientes e preparo.

Usuário: Crie a lista de compras. Já tenho frango e batata.
Agente: Compara os ingredientes e salva os itens restantes na lista.

Usuário: O que falta comprar?
Agente: Consulta a lista da mesma conversa.
```

O exemplo ilustra o fluxo da aplicação; os resultados dependem das receitas disponíveis na TheMealDB e das respostas do modelo.

## 3. Arquitetura e as duas ferramentas

O agente utiliza o padrão **ReAct**: recebe o pedido, seleciona uma ferramenta, observa o resultado e decide se precisa executar outra ação antes de responder.

```text
                     Usuário / Streamlit
                            |
                  Agente LangChain / ReAct
                            |
                       Google Gemini
                            |
            +---------------+----------------+
            |                                |
     buscar_receitas               gerenciar_lista_compras
            |                                |
        TheMealDB                     SQLite + TheMealDB
            |                                |
            +---------------+----------------+
                            |
                    Resposta ao usuário

           Memória: LangGraph + SQLite, por conversa
```

| Ferramenta | O que realiza | Integração |
| --- | --- | --- |
| `buscar_receitas` | Pesquisa por nome ou ingredientes e consulta os detalhes de uma receita pelo identificador. | API pública TheMealDB |
| `gerenciar_lista_compras` | Cria, consulta, adiciona, marca, desmarca e remove itens da lista vinculada à conversa. | Banco SQLite local; consulta à TheMealDB ao criar a lista |

As ferramentas são registradas no LangChain com descrições e argumentos próprios. O agente pode acionar uma ou ambas, conforme a pergunta. A interface exibe os nomes das ferramentas utilizadas e os respectivos resultados, sem mostrar o raciocínio interno privado do modelo.

**Limite da busca por ingredientes:** a modalidade gratuita da TheMealDB filtra um ingrediente por consulta. O programa faz pesquisas individuais e combina os candidatos para apresentar opções relacionadas. A comparação é aproximada e não é uma busca exaustiva no catálogo.

### Memória conversacional

O LangGraph utiliza um *checkpointer* SQLite para salvar mensagens em `dados/conversas.sqlite`. Cada conversa possui um `thread_id` próprio. As listas ficam em `dados/compras.sqlite`, associadas ao mesmo identificador. Reabrir o endereço da conversa permite recuperar seu histórico; começar uma nova conversa cria outro identificador.

## 4. Tecnologias

| Tecnologia | Finalidade |
| --- | --- |
| Python | Lógica da aplicação |
| LangChain | Agente e ferramentas |
| LangGraph | Ciclo do agente e memória persistente |
| Google Gemini | Modelo de linguagem |
| TheMealDB | Dados de receitas |
| SQLite | Conversas e listas de compras |
| Streamlit | Interface web |
| Requests | Consultas HTTP |
| pytest | Testes automatizados |

O projeto utiliza **somente Gemini como modelo de linguagem**. Não é necessário instalar modelos locais.

## 5. Instalação no Windows

### Requisitos

- Python 3.11 ou superior.
- Acesso à internet para consultar receitas.
- Chave da API Gemini e um projeto Google **autorizado a utilizar o modelo selecionado** para conversar com a IA.

Extraia o projeto, abra a pasta `receitas-compras-ia` no Explorador de Arquivos e digite `powershell` na barra de endereço para abrir o terminal nessa pasta.

Confira a versão do Python:

```powershell
py --version
```

Crie o ambiente virtual e instale as dependências:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Não é necessário ativar o ambiente virtual: os comandos chamam seu executável Python diretamente.

### Configurar o Gemini

Crie uma chave em [Google AI Studio — API Keys](https://aistudio.google.com/apikey). Depois execute:

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha o arquivo `.env`:

```dotenv
GOOGLE_API_KEY=SUA_CHAVE_DO_GEMINI
GEMINI_MODEL=gemini-3.8-flash
```

Escolha um modelo disponível para seu projeto no Google AI Studio. O exemplo acima corresponde ao nome configurado nesta versão; o acesso depende das permissões e dos limites do projeto associado à chave. **A modalidade gratuita não está disponível para todos os projetos**, e o uso com faturamento habilitado pode gerar cobranças.

**Cada pessoa que instalar a aplicação, inclusive quem avaliar ou executar o projeto a partir do GitHub, deverá configurar sua própria chave no arquivo `.env`.** A chave deve pertencer a um projeto Google com acesso autorizado ao modelo selecionado. Não é preciso alterar o código Python para trocar a chave.

Guarde a chave em segredo. O arquivo `.env` e os bancos locais são ignorados pelo Git. O repositório contém somente `.env.example`, que é um exemplo de configuração sem credenciais.

### Iniciar a aplicação

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra [http://localhost:8501](http://localhost:8501). Para encerrar a aplicação, pressione `Ctrl + C` no PowerShell. Reinicie o Streamlit se alterar o `.env`.

## 6. Como utilizar

**Conversar com o agente:** digite uma receita ou ingredientes no campo principal. Continue na mesma conversa para que o agente possa utilizar o contexto anterior. Ao receber uma resposta, abra **“Ferramentas utilizadas e resultados”** para consultar as ações realizadas.

**Editar a lista:** use a barra lateral para marcar ou remover itens e adicionar ingredientes. A lista pertence à conversa atual.

**Usar as ferramentas sem consultar o modelo:** abra a seção **“Testar as duas ferramentas sem gastar cota de IA”**, pesquise uma receita pelo nome e copie seu ID. Em seguida, consulte os detalhes e gere uma lista com o ID e os ingredientes disponíveis. Essas ações usam a TheMealDB e o SQLite diretamente, sem fazer requisições ao Gemini.

## 7. Como testar sem consumir cotas do Gemini

É possível verificar as ferramentas, a lógica de compras, a persistência e o ciclo de chamadas do agente **sem possuir uma chave Gemini e sem enviar perguntas ao modelo real**. Há duas maneiras complementares:

### Método A — Testes automatizados com respostas simuladas

1. Abra o PowerShell na pasta que contém `requirements.txt`.
2. Instale as dependências conforme a seção de instalação.
3. Execute:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
```

Esse comando executa os testes locais sem fazer chamadas à API Gemini. Os testes simulam os retornos da TheMealDB quando necessário e verificam pesquisas, tratamento de erros, cálculo de itens faltantes, gravação e recuperação da lista.

Para conferir especificamente o ciclo de ferramentas do LangChain, execute:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs tests/test_ciclo_agente.py
```

O teste `test_ciclo_agente.py` utiliza `FakeMessagesListChatModel`: é um modelo **falso de teste**, não outro provedor de IA. Ele fornece mensagens pré-definidas que solicitam o uso de `buscar_receitas` e `gerenciar_lista_compras`; o LangChain executa as ferramentas e registra as observações. O teste também confere continuidade e separação de conversas. **Nenhuma requisição é enviada ao Gemini.**

### Método B — Testar as duas ferramentas pela interface

1. Inicie o Streamlit:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

2. Abra [http://localhost:8501](http://localhost:8501).
3. Expanda **“Testar as duas ferramentas sem gastar cota de IA”**.
4. Selecione **`nome`**, digite `Arrabiata` e clique em **“Executar buscar_receitas”**.
5. Copie o **ID** de uma das receitas retornadas. Selecione **`detalhe`**, preencha esse ID e consulte os ingredientes e o preparo.
6. No formulário de compras, cole o mesmo ID, informe os ingredientes que já possui (ou deixe em branco) e clique em **“Executar gerenciar_lista_compras”**.
7. Confira a lista na barra lateral; atualize a página se necessário. Marque, desmarque ou adicione um item e veja se a alteração é mantida.

Essa opção usa a **API TheMealDB pela internet e o banco SQLite local**, mas **não chama o Gemini nem consome seus créditos ou sua cota**. Ela funciona mesmo quando a conversa com IA está desabilitada por falta de chave.

**Diferença entre os métodos:** o método A usa respostas simuladas e consegue testar o encadeamento de ferramentas; o método B consulta receitas reais, mas aciona as ferramentas diretamente, sem passar pelas decisões do modelo. Portanto, ambos comprovam partes do funcionamento, mas não substituem uma conversa real com Gemini para verificar suas decisões em produção.

---

## 8. Testes automatizados e resultados

O projeto utiliza `pytest` para conferir as funções de consulta de receitas, o tratamento de dados e erros, o gerenciamento de listas, a persistência e o comportamento do agente com respostas simuladas.

No PowerShell, dentro da pasta do projeto, execute:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
```

**Resultado registrado em execução no Windows em 23/11/2026: 31 testes aprovados, sem falhas nos testes executados.**

Os cenários efetivamente exercitados pelos testes automatizados incluem:

| Caso de uso verificado | Comportamento observado nos testes |
| --- | --- |
| Buscar receita por nome | Retorno de receitas e identificadores a partir de respostas de API simuladas |
| Buscar por ingredientes | Combinação de resultados e correspondência aproximada com os itens informados |
| Consultar detalhes | Extração dos ingredientes, das medidas e do modo de preparo |
| Resposta inválida da API | Tratamento do erro sem criar uma receita fictícia |
| Criar lista de compras | Registro de itens ausentes a partir dos ingredientes da receita |
| Atualizar a lista | Adição, marcação, desmarcação e exclusão de itens |
| Persistir dados | Recuperação de listas após novos acessos ao SQLite |
| Separar conversas | Isolamento de listas e histórico por identificador da sessão |
| Ciclo com ferramentas | Encadeamento de chamadas às duas ferramentas usando um modelo de teste simulado |

Esses testes utilizam dados e respostas simuladas quando necessário e **não consomem créditos do Gemini**. A execução direta das ferramentas pela interface consulta a TheMealDB e trabalha com o banco SQLite, também sem consumir cota do modelo.

## 9. Tratamento de erros e limitações

A aplicação trata ausência de resultados, respostas inesperadas e problemas de conexão com a base de receitas. Também identifica erros retornados pelo provedor do modelo, como falta de cota (`429`), indisponibilidade (`503`) e modelo não encontrado (`404`).

O uso da conversa com IA exige que a chave e o projeto do Google tenham permissão para o modelo configurado. Uma restrição de permissão (`403`) é definida pelo provedor e não é resolvida apenas instalando novamente as dependências.

Outras limitações importantes:

- Algumas receitas da TheMealDB são originalmente escritas em inglês. O Gemini pode apresentar o preparo em português.
- A disponibilidade de ingredientes em casa não garante que existam quantidades suficientes.
- Medidas e porções seguem os dados retornados pela fonte.
- A pesquisa por vários ingredientes é aproximada.
- Uma lista nova substitui a lista anterior da mesma conversa.
- A aplicação não verifica alergias, não calcula preços e não realiza compras online.
- Os dados e o histórico ficam armazenados localmente; não há login nem sincronização entre dispositivos.

## 10. Comparação com o procedimento manual

**Sem o agente**, o usuário precisa procurar receitas, abrir os resultados, conferir ingredientes, compará-los com os itens que tem em casa e anotar a lista manualmente.

**Com o agente**, a mesma interface reúne consulta à fonte, explicação do preparo, comparação de ingredientes e gerenciamento da lista, além de preservar o contexto das mensagens. Essa integração reduz a necessidade de alternar entre páginas e anotações, embora o resultado dependa da qualidade das informações recuperadas e da disponibilidade dos serviços.

## 11. Estrutura do projeto

```text
receitas-compras-ia/
├── app.py
├── agente.py
├── ferramentas.py
├── receitas.py
├── compras.py
├── memoria.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── dados/
│   └── .gitkeep
├── tests/
│   └── arquivos de teste pytest
├── docs/
│   └── COMO_FUNCIONA.md
└── README.md
```

Os arquivos são organizados por responsabilidade. O funcionamento de cada módulo é o seguinte:

| Arquivo | Responsabilidade no código |
| --- | --- |
| `app.py` | Monta a interface Streamlit, mostra o histórico e a lista lateral, recebe perguntas e disponibiliza o teste direto das ferramentas. |
| `agente.py` | Define as instruções do assistente, cria o modelo Gemini e o agente com `create_agent`, executa cada pergunta e registra as ferramentas chamadas. Também traduz erros do provedor para mensagens simples. |
| `ferramentas.py` | Declara as duas ferramentas com `@tool`, define seus parâmetros e entrega resultados estruturados ao agente. |
| `receitas.py` | Consulta os endpoints da TheMealDB, normaliza nomes de ingredientes, reúne sugestões e extrai os detalhes das receitas encontradas. |
| `compras.py` | Compara os ingredientes necessários com os disponíveis e grava, consulta e modifica itens em `dados/compras.sqlite`. |
| `memoria.py` | Configura o `SqliteSaver`, responsável por manter o histórico do LangGraph em `dados/conversas.sqlite`. |
| `config.py` | Carrega as opções do `.env`, define os caminhos locais e valida a presença da chave para usar a conversa com IA. |
| `tests/` | Reúne testes unitários, testes de ferramentas e o teste do agente com respostas simuladas. |

### Como uma pergunta percorre o código

1. O Streamlit (`app.py`) recebe a mensagem e recupera o identificador da conversa.
2. O agente (`agente.py`) envia a mensagem e seu histórico ao modelo Gemini.
3. O modelo escolhe se precisa usar `buscar_receitas` ou `gerenciar_lista_compras`, registradas em `ferramentas.py`.
4. A ferramenta executa a consulta na TheMealDB (`receitas.py`) ou a operação sobre a lista SQLite (`compras.py`) e devolve um resultado estruturado.
5. O LangChain entrega esse resultado ao modelo, que pode solicitar outra ferramenta ou elaborar a resposta.
6. O histórico é mantido pelo LangGraph (`memoria.py`); a interface exibe a resposta e as ferramentas utilizadas. A lista permanece vinculada à mesma conversa.

As funções foram separadas para facilitar a leitura e os testes. Há comentários breves apenas nos trechos técnicos mais importantes.

## 12. Publicação no GitHub

Crie um repositório vazio e execute os comandos dentro da pasta do projeto:

```powershell
git init
git branch -M main
git add .
git commit -m "Versao inicial do Receitas e Compras IA"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

Substitua o endereço de exemplo pelo endereço do seu repositório. Antes de publicar, confira `git status` e verifique que arquivos `.env`, `.venv`, caches e bancos SQLite não estão sendo incluídos.

## 13. Fontes e créditos

- [TheMealDB — API](https://www.themealdb.com/api.php) e [guia de utilização](https://www.themealdb.com/docs_api_guide.php): dados e parâmetros das consultas de receitas.
- [TheMealDB — Condições de uso](https://www.themealdb.com/terms_of_use.php): condições aplicáveis ao conteúdo das receitas.
- [LangChain — Agentes](https://docs.langchain.com/oss/python/langchain/agents) e [ferramentas](https://docs.langchain.com/oss/python/langchain/tools): organização do agente ReAct.
- [LangChain — Memória](https://docs.langchain.com/oss/python/langchain/short-term-memory): histórico e persistência.
- [Streamlit](https://docs.streamlit.io/): interface web.
- [Google AI Studio](https://aistudio.google.com/): acesso e configuração da API Gemini.
- **ChatGPT (OpenAI):** utilizado como ferramenta de apoio para planejamento, elaboração, revisão do código, testes e documentação. As informações técnicas devem ser conferidas nas fontes indicadas.

As receitas são provenientes da TheMealDB. O uso ou a redistribuição de conteúdo e imagens deve respeitar as condições do serviço.
