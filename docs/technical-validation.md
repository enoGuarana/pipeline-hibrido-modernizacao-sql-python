# Validação técnica da stack e do parsing

Data da execução: 2026-10-01.

## Escopo e limites

Esta validação cobre a inicialização da stack e uma comparação curta entre dois parsers adequados ao dialeto PostgreSQL. Os experimentos de parser foram executados em um ambiente auxiliar Python 3.13 de 32 bits porque o interpretador Python 3.14 do ambiente não estava acessível durante esta rodada. Portanto, os resultados de parsing não comprovam compatibilidade de instalação com Python 3.14.

Não foi instalado nem usado um parser como dependência do projeto nesta etapa. A escolha abaixo é uma proposta sujeita a ADR e a nova verificação no runtime alvo.

## Stack executável — baseline histórico

| Item | Comando/versão | Resultado | Limitação |
|---|---|---|---|
| Python alvo | `py -3.14` / Python 3.14.8, registrado na validação anterior | Dependências do projeto instalaram e o grafo compilou | Revalidação posterior foi bloqueada por acesso ao executável |
| LangGraph CLI | `langgraph dev --no-browser --host 127.0.0.1 --port 8125` / CLI 0.4.32 | Carregou `modernization` e `pipeline.api:app` | Servidor de desenvolvimento; não é evidência de produção |
| Rotas customizadas | `GET /health`; `POST /modernize` | No baseline, `/health` respondeu 200 e `/modernize` respondeu 501 conforme contrato pendente | Esse resultado é histórico; a implementação atual tem fluxo completo |
| PostgreSQL | `postgres:16-alpine`, publicado em `localhost:55432` | Healthcheck saudável; `modernization_history` criada e inspecionada | Porta 5432 já era usada por uma instalação local |

Comandos reproduzíveis da verificação de integração:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
langgraph dev --no-browser --host 127.0.0.1 --port 8125
```

Os comandos HTTP usados no baseline foram `GET http://127.0.0.1:8125/health` e um `POST` para `/modernize` com `{"source_code":"SELECT 1;"}`. A chamada criou `run_id=1` com status `pending`.

## Verificações posteriores da implementação

As verificações abaixo não substituem os experimentos históricos dos parsers;
elas registram o estado executável posterior:

| Verificação | Comando/versão | Resultado observado | Limite |
|---|---|---|---|
| Runtime | Python 3.14.8 | instalação editável e testes executados | não é garantia de compatibilidade futura |
| Dependências | `pip check` | sem conflitos no ambiente verificado | ambiente local |
| Qualidade | `pytest -q`; Ruff em `src`, `tests` e `dashboard.py` | 32 testes passaram; Ruff passou nesse escopo | dois avisos de depreciação não foram eliminados |
| Provedores | testes unitários com clientes simulados | Gemini, OpenAI e OpenRouter roteados sem chamadas externas | não comprova quota, modelo ou resposta real de cada provedor |
| LangGraph | `langgraph dev --no-browser --host 127.0.0.1 --port 8125` | CLI carregou `pipeline.api:app` | servidor de desenvolvimento |
| Dashboard | `python -m streamlit run dashboard.py --server.headless true --server.port 8501` | health interno do Streamlit respondeu 200 | não comprova API/DB ativos simultaneamente |

Os 32 testes incluem a fronteira HTTP da API, fallback local do dashboard,
resolução de `GOOGLE_API_KEY` e dollar quoting nomeado. Os testes HTTP usam
pool/grafo controlados e não substituem uma execução real com PostgreSQL e LLM.
O comando Ruff incluindo `scripts/` encontrou `I001` no arquivo não versionado
`scripts/build_report_pdf.py`; ele não foi alterado por pertencer a outro
trabalho presente no diretório.

O resultado real Gemini do Anexo B e os artefatos C–F estão descritos em
`docs/evaluation.md` e `docs/requirements.md`. As chamadas OpenAI/OpenRouter
dos testes locais são mocks determinísticos; não devem ser apresentadas como
geração remota executada.

## Instalação auxiliar dos parsers

```powershell
$parserDeps = "C:\Users\Enomoto\parser-validation-deps"
py -3.13-32 -m pip install --target $parserDeps sqlglot pglast
```

Resultado observado:

- `sqlglot 30.21.0` instalado;
- `pglast 8.4` instalado;
- ambos instalaram nesse ambiente auxiliar Python 3.13-32;
- nenhuma conclusão de compatibilidade com Python 3.14 é feita a partir disso.

## Experimento A — invólucro CREATE FUNCTION/PROCEDURE

Fonte: blocos SQL B–F de `DESAFIO_CONTEXTO.md`, extraídos sem reconstrução manual. Para cada anexo foi executado:

```python
sqlglot.parse_one(sql, read="postgres")
pglast.parse_sql(sql)
```

| Anexo | SQLGlot no invólucro | pglast no invólucro | Corpo entre `$$` |
|---|---|---|---|
| B | OK, `Create` | OK, tupla de `RawStmt` | ambos falharam |
| C | OK, `Create` | OK, tupla de `RawStmt` | ambos falharam |
| D | OK, `Create` | OK, tupla de `RawStmt` | ambos falharam |
| E | OK, `Create` | OK, tupla de `RawStmt` | ambos falharam |
| F | OK, `Create` | OK, tupla de `RawStmt` | ambos falharam |

O sucesso do invólucro não significa que o corpo PL/pgSQL foi convertido em AST. No SQLGlot houve avisos de fallback para comandos não suportados no corpo; no pglast o invólucro é reconhecido, mas o conteúdo procedural interno não é uma AST procedural completa.

## Experimento B — construções representativas

| Construção | SQLGlot | pglast | Interpretação |
|---|---|---|---|
| `SELECT` com `COALESCE` | OK, `Select` | OK | SQL embutido pode ser analisado |
| `UPDATE` | OK, `Update` | OK | SQL embutido pode ser analisado |
| CTE recursiva | OK, `Select` | OK | Estrutura SQL reconhecida |
| `IF ... THEN ... RAISE` | Falha | Falha | Controle procedural não coberto |
| `OPEN/FETCH/LOOP` | Falha | Falha | Cursor e loop exigem análise própria |
| `RAISE NOTICE` | Falha | Falha | Comando procedural exige análise própria |
| `SELECT ... FOR UPDATE` | OK | OK | Locking SQL reconhecido, sem inferir semântica transacional |

## Comparação e proposta de estratégia

SQLGlot oferece AST SQL, dialeto PostgreSQL e análise de fragmentos SQL, mas é leniente e não é um parser completo de PL/pgSQL. pglast usa a gramática PostgreSQL e reconhece melhor o `CREATE FUNCTION/PROCEDURE`, mas a própria documentação ressalta que a extensão procedural não é exposta como AST procedural completa.

Proposta para a próxima etapa, ainda não aceita como decisão final:

1. usar pglast para o invólucro PostgreSQL e metadados da rotina;
2. preservar o texto `prosrc` do corpo como origem rastreável;
3. usar um scanner delimitado e consciente de comentários/strings para identificar construções PL/pgSQL e produzir uma IR própria mínima;
4. usar SQLGlot apenas nos fragmentos SQL que forem isolados com segurança;
5. marcar construções não reconhecidas, em vez de alegar AST completa.

Essa estratégia é compatível com B–F e foi implementada como IR/scanner
estrutural do projeto. Ela ainda não demonstra extração semântica completa nem
equivalência comportamental para D–F.

## Fontes oficiais consultadas

- [SQLGlot API](https://sqlglot.com/sqlglot.html): `parse_one`, dialeto PostgreSQL, AST e limitações de parser/transpiler.
- [pglast API](https://pglast.readthedocs.io/en/latest/api.html): `parse_sql` e limitação de AST para a extensão procedural.
- [LangGraph CLI schema](https://github.com/langchain-ai/langgraph/blob/main/libs/cli/langgraph_cli/schemas.py): `http.app` e configuração de `langgraph.json`.

## Critério de conclusão

A inicialização do CLI, a aplicação customizada, as rotas e o PostgreSQL foram
demonstrados localmente. A cobertura real dos cinco invólucros foi medida e o
bloqueio de uma AST procedural completa foi identificado precisamente. A etapa
de validação técnica está concluída com a limitação de que os experimentos de
SQLGlot/pglast são históricos e a implementação atual usa uma IR própria; não
se deve apresentar nenhuma delas como AST completa.
