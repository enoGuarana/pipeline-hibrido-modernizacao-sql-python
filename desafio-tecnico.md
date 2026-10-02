# Desafio Técnico
Construção de um Pipeline Híbrido de Modernização SQL -> Python

## Objetivo
Avaliar habilidades técnicas em desenvolvimento de software, integração de sistemas aplicada a um cenário real de modernização de sistemas legados. O candidato deverá projetar e implementar um pipeline híbrido (LLM + Rules) e apresentar a solução de forma clara, fundamentada e reprodutível.

## Instruções Gerais
1. O candidato terá até 2 dias corridos (take-home) a partir do recebimento do desafio para concluir a entrega.
2. É permitido pesquisar e utilizar bibliotecas externas, desde que sejam justificadas no README.
3. É permitido o uso de assistentes de IA (Copilot, Claude, ChatGPT, Cursor etc.), desde que o candidato saiba defender cada decisão técnica na entrevista de revisão.
4. O resultado final deve ser entregue como repositório Git (público, privado com acesso concedido, ou em arquivo .zip).
5. Inclua um arquivo README.md contendo:
   - Descrição da pipeline desenvolvida e do fluxo de modernização proposto.
   - Passos para executar e testar a aplicação localmente (incluindo Docker Compose, se aplicável).
   - Explicação das decisões técnicas tomadas, com trade-offs considerados.
   - Limitações conhecidas e o que seria feito com mais tempo.

## Descrição do Desafio

### Cenário
A solução de modernização da empresa é composta por pipelines de modernização de sistemas legados. As pipelines híbridas etapas baseadas em chamadas a LLM e etapas determinísticas. Um dos volumes mais frequentes da área de inovação é a migração de lógica de negócio implementada em stored procedures de bancos legados — escritas em PL/pgSQL, T-SQL ou PL/SQL — para serviços modernos em Python. Você foi solicitado a criar uma nova pipeline, responsável pela modernização de stored procedures PL/pgSQL para Python 3.14.

O pipeline recebe o código de uma stored procedure (e, opcionalmente, o schema das tabelas referenciadas) e produz, ao final do fluxo, um módulo Python 3.14 equivalente, junto com um relatório das decisões e validações realizadas. O foco está na qualidade do desenho da pipeline e nas decisões de tradução, não na cobertura sintática total da linguagem.

Os anexos deste documento (A a F) fornecem o material de entrada: o schema do banco legado e cinco stored procedures de complexidade crescente. O candidato deve usá-las como casos de teste da pipeline.

### A Pipeline Híbrida
A pipeline deve implementar uma pipeline com pelo menos quatro etapas, orquestradas como nós de um grafo:

1. **Parsing** — Receber o código SQL e produzir uma representação estruturada (AST, árvore de tokens classificados ou estrutura intermediária equivalente). É aceitável e recomendado o uso de bibliotecas de parsing SQL (sqlglot, pglast, sqlparse), desde que a escolha seja justificada.
2. **Análise semântica** — Identificar construções relevantes (parâmetros IN/OUT, variáveis, cursores, transações, exceções, CTEs, chamadas a outras funções) e marcar pontos de risco para a tradução (ex.: cursores que podem virar gargalo, RAISE, FOR UPDATE, JSONB, recursão).
3. **Geração** — Produzir código Python 3.14 equivalente. O uso de LLM nesta etapa é permitido e bem-vindo, desde que o prompt e o contexto sejam construídos a partir das saídas das etapas anteriores (não basta enviar a procedure bruta direto para o modelo). A escolha entre delegar a query original ao SGBD via texto SQL ou reescrever a lógica em Python puro é uma decisão arquitetural que o candidato deve justificar.
4. **Validação** — Verificar a saída gerada. Como mínimo, executar verificações estáticas (parsing do Python gerado com ast.parse, linting). Como evolução desejada, executar testes ou comparar o comportamento contra a procedure original em um banco de teste.

## Requisitos Técnicos Obrigatórios

### 1. Backend do Pipeline Híbrido
- O híbrido deve ser exposto como um endpoint de um servidor local com langgraph cli com, no mínimo, os seguintes endpoints:
  - `POST /modernize` — Recebe uma stored procedure SQL e retorna o código Python 3.14 equivalente, junto com o relatório das etapas (parsing, análise, geração, validação).
  - `GET /health` — Retorna o status do pipeline (ex.: `{"status": "ok"}`).
- Utilize boas práticas de organização e modularização (separação clara entre camada de API, orquestração do grafo, nós da pipeline, persistência e integrações externas).

### 2. Orquestração com LangGraph
- A pipeline deve ser orquestrada com LangGraph. Cada etapa (parsing, análise semântica, geração, validação) deve ser modelada como um nó do grafo, com estado tipado.
- Documente o desenho do grafo no README (diagrama textual ou imagem).

### 3. Banco de Dados
- Configure um banco de dados PostgreSQL para persistência de informações do pipeline.
- Crie uma tabela `modernization_history` com, no mínimo, os campos:
  - `id` — identificador único.
  - `source_code` — stored procedure SQL enviada.
  - `generated_code` — código Python 3.14 produzido.
  - `report` — relatório estruturado das etapas (JSONB).
  - `status` — desfecho da execução (sucesso, falha, parcial).
  - `created_at` — timestamp da execução.
- Toda execução da pipeline deve ser persistida nessa tabela, independentemente do desfecho.

### 4. Escalabilidade e Boas Práticas
- Use uma arquitetura que suporte crescimento futuro (volume de requisições, novos dialetos SQL, novos modelos de LLM).

## Requisitos Bônus
Os bônus não são obrigatórios, implemente pelo menos um se desejar diferenciar a entrega.

**Bônus 1 — Observabilidade de execução da pipeline híbrida**
- Integre Langfuse (ou langsmith, prioritariamente langfuse) ao servidor langgraph para rastrear cada execução da pipeline (traces por execução, spans por nó do grafo, custo e latência das chamadas de LLM, se aplicável).
- Pode ser usado o Langfuse self-hosted via Docker. Documente a escolha.
- Apresente no README com a captura de tela com os tracings de execução dentro do langfuse ou langsmith evidenciando que o serviço de observabilidade está integrado ao pipeline.

**Bônus 3 — QA**
- Projeto passando em checks de qualidade estática (o padrão de verificações pode ser definido pelo candidato).
- Adicionar cobertura de testes com pytest.

**Bônus 3 — Métrica de Evaluation do Pipeline**
- Defina e implemente pelo menos uma métrica de avaliação automática da qualidade da migração — por exemplo: taxa de código Python gerado que passa em ast.parse, percentual de execuções concluídas sem erro, similaridade estrutural entre AST de origem e destino, equivalência comportamental (mesmo input -> mesmo output) contra um banco de teste, ou avaliação por LLM-as-judge contra critérios objetivos.
- Registre os resultados dessa métrica no Langfuse (scores) ou em uma tabela própria, e exponha um endpoint ou notebook que demonstre a métrica calculada sobre o conjunto de procedures dos Anexos B a F.
- Justifique a escolha da métrica: o que ela captura, o que ela deixa de fora, e como ela seria evoluída em produção.

## Entrega
10. Um repositório Git público contendo:
  - Código completo da pipeline, organizado em módulos claros.
  - Scripts de banco de dados (criação da tabela modernization_history e migrações, se houver).
  - docker-compose.yml ou equivalente para subir servidor local + PostgreSQL (e Langfuse, se aplicável).
  - Resultados da execução do pipeline sobre as procedures dos Anexos B a F (código Python gerado e relatórios).
  - Arquivo README.md com explicações detalhadas e diagrama do grafo LangGraph.
11. Instruções claras de como rodar a aplicação localmente, incluindo variáveis de ambiente necessárias (chaves de LLM, conexão com Postgres, credenciais Langfuse).

## Critérios de Avaliação

| Critério | Peso | Descrição |
| --- | --- | --- |
| Funcionamento Geral | 30% | Pipeline executa de ponta a ponta e atende aos requisitos básicos. |
| Código e Estrutura | 20% | Qualidade do código, modularização, testes e aderência a boas práticas Python. |
| Arquitetura do Pipeline | 15% | Modelagem do grafo LangGraph, separação de nós, estado e fluxo de decisão. |
| Banco de Dados | 10% | Modelagem, inicialização, integração e manipulação correta do PostgreSQL. |
| Escalabilidade | 10% | Propostas para crescimento futuro: cache, filas, paralelização. |
| Documentação | 10% | Clareza e completude do README e das decisões técnicas. |
| Bônus | +15% | Observabilidade com Langfuse (ou langsmith) e métrica de evaluation do pipeline. |

Observação: a soma dos critérios obrigatórios é 100%. Os bônus podem somar até +15 pontos percentuais adicionais à nota final.

## Etapa Pós-Entrega
Após o envio, será agendada uma sessão de revisão técnica de aproximadamente 45 minutos com o time de inovação. Nessa sessão, o candidato apresentará a solução, conduzirá um walk-through pelo código e responderá a perguntas sobre decisões arquiteturais, trade-offs e como evoluiria a solução em produção.

## Anexos — Material de Entrada para a Pipeline
Esta seção contém o material que a pipeline deve ser capaz de processar. O Anexo A descreve o schema do banco legado fictício; os Anexos B a F apresentam cinco stored procedures de complexidade crescente que servem como casos de teste obrigatórios da pipeline.

**Mapa de complexidade dos anexos**

| Anexo | Procedure | Complexidade | Construções principais |
| --- | --- | --- | --- |
| B | fn_saldo_cliente | Baixa | Função escalar, agregação, WHERE simples. |
| C | sp_atualizar_status_contas_inativas | Baixa-Média | Procedure, parâmetros IN/OUT, UPDATE em massa, GET DIAGNOSTICS. |
| D | sp_transferir_entre_contas | Média | Transação explícita, validação, EXCEPTION, RAISE, múltiplos UPDATE/INSERT. |
| E | sp_processar_lote_taxas | Alta | Cursor explícito, LOOP, CASE, JSONB, múltiplas tabelas, log de auditoria. |
| F | sp_relatorio_mensal_cliente | Muito Alta | CTE recursiva, função aninhada, RETURN QUERY (SETOF), RAISE NOTICE, EXCEPTION em camadas. |

(Os anexos de código original estão disponíveis no arquivo DESAFIO_CONTEXTO.md)
