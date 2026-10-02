# Plano de implementação

## Princípios

- Entregar uma fatia verificável por vez.
- Manter requisitos, decisões e evidências separados.
- Não declarar equivalência sem comparação comportamental contra uma referência executável.
- Confirmar APIs e configuração na documentação oficial vigente antes de codificar integrações sujeitas a mudança.
- Registrar em cada decisão se ela é proposta, aceita ou substituída; aceitação deve indicar evidência e limites.

## Sequência

| Etapa | Entrega | Dependências | Critério de saída | Riscos principais |
|---|---|---|---|---|
| 0. Contexto e baseline | `AGENTS.md`, matriz, plano e ADRs coerentes | PDF e `DESAFIO_CONTEXTO.md` | Escopo, fontes, status e lacunas revisados | Contexto local pode divergir do PDF |
| 1. Fundação executável | Ambiente Python 3.14, CLI LangGraph, PostgreSQL e API | Decisão de versões; Docker disponível | `/health` e inicialização comprovados em ambiente limpo | Compatibilidade de versões, conexão e ciclo de vida |
| 2. Parsing | Representação estruturada de PL/pgSQL | Parser escolhido e fixtures B–F | Saída determinística e erros classificados | Cobertura insuficiente de PL/pgSQL |
| 3. Análise semântica | Riscos, parâmetros, variáveis, cursores, transações, exceções, CTEs e chamadas | Parsing | Relatório reproduzível por fixture | Perda de semântica em construções complexas |
| 4. Geração | Estratégia determinística/LLM documentada e código Python | Análise, schema opcional, ADR de geração | Saída versionada e auditável | Alucinação, tipos, transações e efeitos colaterais |
| 5. Validação | `ast.parse`, lint e validações de contrato | Geração | Falha explícita quando validação não passa | Validação estática não prova comportamento |
| 6. Persistência e API completa | Persistir sucesso e falha; resposta do `/modernize` | Fundação, grafo e schema | Uma execução persistida por chamada | Estado parcial, retries e idempotência |
| 7. Equivalência comportamental | Banco/fixtures de referência e comparação B–F | Geração, validação e PostgreSQL | Casos comparáveis, divergências classificadas | Procedures têm efeitos e erros difíceis de comparar |
| 8. Bônus | Observabilidade, QA ampliado e evaluation | Caminho obrigatório estável | Evidência reproduzível de cada bônus adotado | Custo, credenciais e métricas pouco representativas |

## Dependências de decisão

1. Tratar `DESAFIO_CONTEXTO.md` como contexto consolidado e resolver com o avaliador suas inconsistências documentadas.
2. Fixar versões compatíveis de Python, LangGraph CLI, FastAPI, psycopg e parser após consulta às documentações oficiais e uma instalação limpa.
3. Decidir a fronteira SQL/Python e o uso de LLM em ADR antes da geração.
4. Definir o oráculo comportamental antes de alegar equivalência.

## Evidência da etapa 1 até o momento

- Python 3.14.8 e instalação editável do projeto foram verificadas no `.venv`.
- LangGraph CLI 0.4.32 iniciou o grafo `modernization` a partir de `langgraph.json`; `/ok` respondeu 200.
- `http.app` foi configurado para `pipeline.api:app`, e o CLI confirmou `Loaded custom app from pipeline.api:app`.
- O PostgreSQL do projeto foi iniciado em `localhost:55432` porque `localhost:5432` já era usado por uma instalação local; a tabela `modernization_history` foi criada e inspecionada.
- Com `DATABASE_URL=postgresql://postgres:postgres@localhost:55432/modernization`, `/health` respondeu 200 e `/modernize` respondeu 501 com o contrato pendente esperado.
- A chamada de `/modernize` criou `run_id=1` e persistiu `status=pending`, `source_code` e relatório JSONB; nenhum desfecho de sucesso, falha ou parcial foi executado.

A etapa de persistência pendente está funcional apenas no ambiente local verificado; O2 permanece pendente porque a pipeline ainda não produz Python, e O10 só tem evidência para o desfecho `pending`.

## Evidência da validação técnica da etapa 2

`docs/technical-validation.md` registra a comparação reproduzível de SQLGlot 30.21.0 e pglast 8.4 nos anexos B–F. Ambos reconhecem o invólucro das rotinas, mas nenhum interpreta o corpo PL/pgSQL completo. A estratégia proposta é pglast + preservação do corpo + scanner/IR própria, com SQLGlot restrito a fragmentos SQL. A compatibilidade desses parsers com Python 3.14 ainda precisa ser verificada no runtime alvo.

## Evidência da definição arquitetural da etapa 3

`docs/architecture.md` e `src/pipeline/contracts.py` definem o fluxo, responsabilidades, IR, relatórios por etapa, erros, estados, transações, tentativas e limites de abstração. Os exemplos de contrato são ilustrativos e não são resultados de execução. Ainda não há tradução completa nem testes automatizados.

## Status das decisões técnicas

- **Propostas, não aceitas:**
  - iniciar o servidor oficial pelo LangGraph CLI, com as rotas no mesmo runtime do grafo; execução ainda não comprovada;
  - usar estratégia híbrida, preservando SQL quando isso proteger semântica e usando Python para controle/orquestração; fronteiras concretas ainda pendentes;
  - validar estaticamente B–F e começar a validação comportamental por B e D; nenhum resultado comportamental foi produzido.
- **Aceitas para esta etapa documental:** consultar o contexto antes de editar, trabalhar em fatias verificáveis, preservar alterações existentes e não declarar evidência ausente.
- **Substituídas:** nenhuma registrada até o momento.

## Três incertezas técnicas prioritárias

### U1 — Compatibilidade do runtime e do LangGraph CLI

O projeto declara Python 3.14 e usa `langgraph.json`, mas a configuração efetiva da CLI, o formato do entrypoint e a compatibilidade entre versões ainda não foram executados neste ambiente. A referência oficial atual do [LangGraph CLI](https://github.com/langchain-ai/langgraph/blob/main/libs/cli/README.md) descreve `langgraph dev`, `langgraph.json` e versões `python_version` 3.11–3.13; isso não confirma compatibilidade com o `requires-python >=3.14` deste repositório. O contexto exige LangGraph CLI; uma API FastAPI isolada não satisfaz O1.

**Ameaça:** bloqueia inicialização e invalida os critérios de aceite do servidor/grafo.

### U2 — Estratégia que preserva semântica das procedures

Ainda não está decidido se cada construção será mantida como SQL executado no PostgreSQL, reescrita em Python ou encaminhada a uma LLM com regras. `FOR UPDATE`, transações, exceções, `JSONB`, cursores e CTE recursiva tornam a escolha sensível ao comportamento.

**Ameaça:** código sintaticamente válido pode produzir efeitos, erros ou saldos diferentes.

### U3 — Oráculo para equivalência comportamental

Não existe ainda um harness que execute a procedure original e o Python gerado no mesmo estado controlado, compare retorno, exceções e efeitos no banco e trate diferenças de relógio/ordenação.

**Ameaça:** sem esse oráculo, só é possível aceitar parsing/estática, não equivalência.

## Critério para avançar

Avançar para implementação somente quando a etapa corrente tiver: (a) decisão documentada ou explicitamente marcada como proposta; (b) comando reproduzível; (c) evidência armazenada; e (d) limitações conhecidas registradas. A etapa de equivalência só avança após existir um caso controlado que compare procedure original e saída Python.

## Atualização da etapa 5 — primeiro fluxo completo

Estado: concluída para o caso Anexo B, com geração simulada.

- `src/pipeline/graph.py` implementa parsing estrutural, análise semântica limitada ao Anexo B, geração simulada, `ast.parse`, Ruff e finalização.
- `src/pipeline/api.py` registra uma execução como `pending`, executa o grafo e finaliza o registro em sucesso ou falha controlada.
- `tests/test_graph.py` cobre sucesso, sintaxe inválida e falha de parsing antes da geração.
- Evidência observada: `3 passed`; Ruff passou; a CLI LangGraph carregou `pipeline.api:app`; `/health` respondeu `{"status":"ok"}`; `/modernize` respondeu sucesso com cinco relatórios; o registro `run_id=4` foi persistido como `success`, com código e cinco etapas no JSONB.

Limites: o gerador é um stub explícito, não chama LLM, não executa o código produzido e não demonstra equivalência. O suporte de parsing/análise ainda não cobre C–F.

## Atualização da etapa 6 — parsing e análise B–F

Estado: parsing estrutural e análise semântica inicial concluídos; tradução completa ainda pendente.

| Anexo | Rotina reconhecida | Extrações/riscos verificados |
|---|---|---|
| B | `fn_saldo_cliente` | parâmetros, variável, `SELECT`, tabelas, agregação e retorno |
| C | `sp_atualizar_status_contas_inativas` | `IN/OUT`, `UPDATE`, `NOT EXISTS`, `ROW_COUNT`, `JSONB` e `RAISE` |
| D | `sp_transferir_entre_contas` | parâmetros, variáveis, `SELECT`, `UPDATE`, `FOR UPDATE`, exceção e auditoria |
| E | `sp_processar_lote_taxas` | cursor, loop, `FETCH`, `CASE`, `UPDATE`, inserções, `JSONB` e risco de N+1 |
| F | `sp_relatorio_mensal_cliente` | retorno tabular, CTE recursiva, chamada de B, `RAISE`, agregações e fallback |

Evidência: `9 passed` em `pytest tests -q`; Ruff passou. O parser preserva o corpo original, ignora comentários e strings na classificação e declara explicitamente que não produz AST completa de PL/pgSQL. Construções não suportadas são reportadas e podem levar o fluxo a `partial`.

## Atualização das etapas 7–8 — geração OpenAI e reparo limitado

- O SDK oficial `openai 2.54.0` foi instalado no Python 3.14.8.
- A integração usa a Responses API, `OPENAI_API_KEY`, `OPENAI_MODEL`, prompt `modernize_v1` e `store=False`; credenciais não são lidas para relatórios.
- Sem chave, o sistema permanece explicitamente no modo simulado para desenvolvimento. Nenhuma chamada real foi reivindicada.
- Com chave, timeout, erro de autenticação, resposta vazia ou resposta fora do contrato finalizam a execução como falha.
- A validação admite no máximo uma tentativa de reparo; `11 passed` cobre o roteamento e a preservação da tentativa anterior.
- Cada execução registra hashes SHA-256 do SQL, schema e código gerado, além de tentativa, modelo e versão do prompt quando disponíveis.

Referência consultada: [SDKs oficiais OpenAI](https://developers.openai.com/api/docs/libraries) e [migração para Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses). A verificação real da geração ainda depende de `OPENAI_API_KEY`.

## Atualização da compatibilidade do runtime

A tentativa de usar `langgraph-api 0.15.1` foi registrada no ADR-010 e revertida porque introduziu conflitos de dependências verificáveis. O ambiente atual foi restaurado para `langgraph-cli 0.4.32`, `langgraph-api 0.10.3` e `langgraph 1.2.12`; `pip check` ficou limpo e a limitação de EOL permanece explícita. A atualização para uma combinação suportada continua pendente de uma versão compatível publicada pela CLI.

## Evidência da primeira chamada OpenAI

Uma chamada real do Anexo B alcançou a Responses API, mas terminou controladamente com `429 insufficient_quota`. O histórico recebeu `run_id=6` como `failure`, sem código gerado. Isso confirma o caminho de autenticação, requisição e persistência da falha, mas não confirma geração real, validação do código ou equivalência.

## Substituição do provedor por Gemini

- O usuário aprovou o SDK nativo `google-genai`. `gemini-2.5-pro` foi recusado
  para novos usuários no `run_id=7`; o usuário então aprovou
  `gemini-3.1-pro-preview` com a limitação de preview explícita.
- O modelo sucessor foi recomendado pela própria resposta do provedor.
- `gemini-3.1-pro-preview` retornou quota gratuita igual a zero no `run_id=8`;
  `gemini-2.5-flash` foi então recusado para novos usuários no `run_id=9`.
- A resposta do provedor recomendou `gemini-3.8-flash`, adotado como padrão
  operacional fixo para a próxima verificação.
- O `run_id=11` obteve geração real com `gemini-3.8-flash`, prompt
  `modernize_v1` e uso reportado, mas falhou no Ruff; o reparo recebeu `503`.
- O artefato de falha foi preservado em `results/run-11` para auditoria.
- `modernize_v2` passou a exigir Python 3.14 e Ruff, sem correção manual da
  saída anterior. As tentativas `12` e `13` receberam `503` antes da geração.
- O `run_id=14` confirmou nova indisponibilidade do `gemini-3.8-flash`. Valores
  temporários de modelo nos processos dos `run_id=15` e `16` foram sobrescritos
  pelo `.env` carregado pelo LangGraph CLI; os logs mostraram que essas chamadas
  ainda atingiram `gemini-3.8-flash`.
- O catálogo da API e a documentação oficial confirmaram
  `gemini-3.5-flash-lite`. Uma sondagem mínima passou e o modelo foi adotado
  explicitamente no `.env` local e como padrão versionado.
- O `run_id=17`, com `modernize_v2`, gerou e reparou código real, mas terminou
  em Ruff `I001`; a saída foi preservada em `results/run-17` sem correção manual.
- O prompt `modernize_v3` tornou explícitas a ordem Ruff/isort dos imports e a
  fidelidade ao contrato de retorno. O `run_id=18` passou em `ast.parse` e Ruff
  na primeira tentativa, foi persistido como `success` e exportado para
  `results/run-18`. Essa conclusão fecha geração real e validação estática de B,
  mas não equivalência nem os resultados C–F.
- A verificação dos bundles detectou tradução automática de `LF` para `CRLF`
  no Windows. O exportador passou a gravar texto com `newline=""`; um teste
  compara os bytes exportados e os hashes registrados. Os bundles 17 e 18 foram
  reexportados do PostgreSQL, sem alteração manual do código gerado. O
  `.gitattributes` fixa `LF` em `results/**` para preservar os hashes após
  checkout em Windows.
- `truststore` foi adotado para preservar a verificação TLS usando o armazenamento nativo do Windows; `verify=False` foi rejeitado.
- O ADR-012 substitui o ADR-009 para novas gerações sem apagar a tentativa OpenAI anterior.
- A interface interna do grafo permanece estável e os metadados disponíveis do Gemini continuam rastreáveis.

## Revisão da etapa 9 — execução real C–F

O schema A foi extraído para `fixtures/A.sql` com comparação textual ao bloco
de `DESAFIO_CONTEXTO.md`. Os `run_id=19–22` executaram C–F com
`modernize_v3`; C e E passaram estaticamente após reparo, enquanto D e F
falharam. Os `run_id=23–26` repetiram C–F com `modernize_v4`; C passou após
reparo e D, E e F falharam por Ruff. Todos os artefatos foram exportados.

A revisão crítica encontrou divergências semânticas nos códigos gerados,
incluindo arredondamento/NULL em E, dependência legada e filtro de contas em F,
e comportamento de auditoria/rollback em D. Elas estão classificadas em
`results/semantic-review.md`; não foram corrigidas silenciosamente.
