# Requisitos e critérios de aceite

## Fontes e limites

- Fonte consolidada: `DESAFIO_CONTEXTO.md`, baseada em `Desafio_Tecnico_Inovacao_v2_candidatos 4.pdf`.
- O contexto confirma que suas propostas arquiteturais não são decisões já aprovadas.
- A coluna de evidência registra apenas fatos observados; uma proposta não é aceite.

## Status das decisões

- **Proposta:** direção sugerida pelo contexto ou por um ADR, ainda sem aprovação e evidência suficiente.
- **Aceita:** decisão explicitamente adotada para a etapa, com a evidência disponível e seus limites registrados.
- **Substituída:** decisão anteriormente aceita que deixou de orientar o trabalho; o documento substituto e o motivo devem ser indicados.

O ADR-009 (OpenAI) foi substituído pelo ADR-012 (Gemini) para novas gerações;
sua evidência histórica foi preservada. As propostas do `DESAFIO_CONTEXTO.md`
não são aceites por sua simples presença no documento.

## Obrigatórios

| ID | Requisito | Implementação prevista | Evidência de aceite |
|---|---|---|---|
| O1 | Backend iniciado pelo LangGraph CLI | Configuração CLI validada e rotas personalizadas integradas ao servidor LangGraph | CLI 0.4.32 carregou `pipeline.api:app` com PostgreSQL do projeto em `localhost:55432`; aceite limitado ao ambiente de desenvolvimento local |
| O2 | `POST /modernize` recebe SQL/schema e retorna Python/relatório | Contratos de entrada/saída e integração com o grafo | `run_id=18`: HTTP 200, Python real e relatório persistido; schema continua opcional e não foi fornecido nesse caso |
| O3 | `GET /health` retorna status | Rota funcional no servidor alvo | `GET http://127.0.0.1:8125/health` respondeu 200 e `{"status":"ok"}`; evidência somente local |
| O4 | LangGraph com quatro nós e estado tipado | Parsing, análise semântica, geração e validação | Grafo tipado executado no `run_id=18`, seguido de finalização; diagrama em `docs/architecture.md` |
| O5 | Parsing estruturado | AST, tokens classificados ou IR equivalente; parser justificado | IR estrutural e testes B–F; limite de não ser AST completa documentado |
| O6 | Análise semântica e riscos | Extrair parâmetros, variáveis, cursores, transações, exceções, CTEs, chamadas e riscos (`RAISE`, `FOR UPDATE`, `JSONB`, recursão) | Testes B–F e tabela de cobertura; inferências separadas de fatos |
| O7 | Geração equivalente e decisão SQL/Python | Contexto de geração derivado das etapas anteriores; fronteira documentada | Código/relatório real B em `results/run-18`; validade estática aprovada, equivalência ainda não testada |
| O8 | Validação estática | `ast.parse` e linting do Python produzido | `run_id=18` passou nas duas verificações na primeira tentativa; `run_id=17` preserva falha Ruff real |
| O9 | PostgreSQL e `modernization_history` | Script/migração e repositório de persistência | Banco iniciado, schema inspecionado e integração funcional |
| O10 | Persistir toda execução | Criar registro antes do processamento e atualizar sucesso/falha/parcial | `run_id=18` persistiu sucesso e `run_id=17` persistiu falha controlada com JSONB; desfecho parcial ainda requer evidência específica |
| O11 | Modularização e evolução | Separar API, grafo, nós, persistência e integrações | Inspeção estrutural e testes das fronteiras |
| O12 | Procedures B–F e resultados reais | Fixtures do schema A e rotinas B–F; artefatos associados às entradas | Fixtures A–F e artefatos reais `run-18` e `run-19–26`; D–F têm falhas/limitações documentadas e ainda não demonstram equivalência |
| O13 | Docker Compose e README completo | Compose para servidor/PostgreSQL; fluxo, testes, diagrama, decisões, trade-offs e limitações | Reprodução em checkout limpo |

## Bônus

| ID | Bônus | Implementação prevista | Evidência de aceite |
|---|---|---|---|
| B1 | Observabilidade Langfuse ou LangSmith | Traces por execução, spans por nó e custos/latências quando houver LLM | Captura ou consulta reproduzível mostrando uma execução e seus spans |
| B2 | QA estático e pytest | Linter, type checks se adotados e testes automatizados | Comandos, versões, saída e cobertura publicados; sem declarar passagem antecipada |
| B3 | Métrica de evaluation | Métrica definida, limitações explicitadas e resultado para B–F | Endpoint `/evaluation` e `scripts/evaluate_results.py`, com denominador, IDs e limitações; equivalência comportamental permanece zero |

## Recomendações não obrigatórias

Estas são recomendações de engenharia, não requisitos aceitos automaticamente:

- manter queries/transações no PostgreSQL quando isso reduzir risco semântico;
- usar contexto estruturado no prompt caso uma LLM seja adotada;
- evitar N+1 ao traduzir cursores;
- adicionar filas, cache, paralelização e novos dialetos somente após medir a necessidade;
- adicionar observabilidade e avaliação depois que o caminho determinístico mínimo estiver verificável.

## Recomendações do contexto, não requisitos adicionais

- Monólito modular, regras determinísticas e LLM substituível são propostas; não estão aceitos por este documento.
- Não executar código gerado no servidor; qualquer comparação deve ocorrer em ambiente de teste isolado.
- Considerar uma única tentativa de reparo somente após o fluxo básico ser verificável.
- Não adicionar frontend, microserviços, filas, Kubernetes ou IaC sem necessidade demonstrada.

## Inconsistências do enunciado a confirmar

- Os pesos obrigatórios listados somam 95%, embora o texto diga 100%.
- A entrega menciona repositório público, enquanto as instruções gerais permitem privado com acesso ou ZIP.
- A numeração dos bônus é repetida.

Nenhuma dessas inconsistências foi corrigida silenciosamente; devem ser confirmadas com o avaliador se afetarem a entrega.

## Estado atual observado

Há contratos tipados, uma definição de grafo, rotas, pool PostgreSQL e DDL no repositório. Python 3.14.8, a instalação editável e o LangGraph CLI foram verificados; o CLI carregou o grafo e a aplicação customizada usando o PostgreSQL do projeto em `localhost:55432`. `/health` respondeu 200. Uma chamada real a `/modernize` criou e finalizou uma linha `pending` com `run_id=1`; os nós ainda levantam `NotImplementedError`, a rota retorna `501` e não há execução dos casos B–F. O1, O3 e a fatia `pending` de O10 têm evidência local limitada; O2 e O4–O9, O11–O13 permanecem não aceitos.

## Atualização após a etapa 5

A descrição acima é o baseline anterior à implementação do fluxo. A evidência mais recente é:

- O1: CLI LangGraph carregou `pipeline.api:app` em `127.0.0.1:8123`; aceite limitado ao ambiente local e à versão instalada.
- O2: `/modernize` recebeu `source_code`, devolveu `run_id`, status, código e relatório; a saída é simulada.
- O3: `/health` respondeu 200 com status `ok`.
- O4: o grafo executou parsing, análise semântica, geração e validação, mais finalização; `PipelineState` é tipado.
- O8: `ast.parse` e Ruff passaram para o código produzido no caso verificado.
- O9/O10: `run_id=4` foi persistido no PostgreSQL isolado como `success`, com código gerado simulado e cinco relatórios no JSONB.

O2, O4, O8, O9 e O10 permanecem aceitos apenas para esta fatia e com os limites acima. O5–O7, O11–O13 continuam pendentes para cobertura completa, integração real e os anexos B–F.

## Atualização após parsing/análise dos anexos

Os fixtures B–F foram criados em `fixtures/`, preservando uma versão do SQL de cada rotina. O parser estrutural reconhece invólucro, parâmetros, variáveis, operações, tabelas e construções de risco. A análise classifica fatos, riscos, inferências e construções não suportadas. A cobertura automatizada passou para os cinco fixtures e inclui proteção contra falsos positivos em comentários e strings.

Isso fornece evidência parcial para O5 e O6. Ainda não é evidência de geração equivalente, execução real B–F ou equivalência comportamental.

## Atualização de geração, reparo e rastreabilidade

O cliente Gemini foi integrado por uma fronteira pequena, com prompt versionado e modelo configurável por ambiente. A decisão OpenAI anterior foi substituída sem apagar sua evidência histórica. O reparo limitado tem uma única tentativa e preserva os relatórios anteriores. Os relatórios incluem hashes SHA-256 da entrada, schema e código gerado quando disponíveis.

O `run_id=18` fornece evidência real para O2, O7 e O8 no Anexo B: a chamada
`POST /modernize`, servida pelo LangGraph CLI, usou `gemini-3.5-flash-lite` e
`modernize_v3`, persistiu código/relatório e passou em `ast.parse` e Ruff na
primeira tentativa. A evidência está em `results/run-18` e não autoriza alegar
equivalência. O12 agora tem execução real B–F, mas permanece parcial quanto a
aceite estático/semântico e equivalência.

O schema A foi extraído fielmente para `fixtures/A.sql`. As rodadas reais
`run_id=19–26` cobriram C–F com schema no contexto e estão preservadas em
`results/`; a revisão em `results/semantic-review.md` separa comportamento
plausível, divergência observada e comportamento ainda não testado. O12 tem
evidência de execução dos cinco casos, mas permanece parcial quanto a aceite
semântico e equivalência.

## Pendências objetivas após as decisões validadas

- **Geração real B:** concluída estaticamente no `run_id=18`; falta executar e
  revisar C–F.
- **Equivalência:** instalar schema/rotinas originais no banco de avaliação, executar cenários B–F e comparar retorno, efeitos, exceções e transações.
- **Evaluation/observabilidade:** bônus planejados; ainda não reivindicados por falta de traces e resultados reais.
- **Runtime:** a CLI atual funciona, mas `langgraph-api 0.10.3` está em EOL; a tentativa de atualização para `0.15.1` foi revertida por conflitos documentados no ADR-010.

A tentativa OpenAI histórica retornou `429 insufficient_quota`, mas foi
substituída pela integração Gemini. A geração real do Anexo B está comprovada;
equivalência comportamental e os artefatos C–F permanecem abertos.
