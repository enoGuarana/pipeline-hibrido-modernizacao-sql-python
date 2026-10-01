# Pipeline Híbrido de Modernização SQL → Python

Implementação incremental do desafio técnico. A fatia atual entrega servidor, rotas, persistência, parsing/análise estrutural B–F, integração OpenAI configurável e reparo limitado.

## Arquitetura mínima

```text
POST /modernize
       │
       ▼
LangGraph: parsing → análise semântica → geração → validação
       │
       ▼
PostgreSQL: modernization_history
```

O estado compartilhado é `PipelineState`, um `TypedDict`. Os nós estão registrados em `langgraph.json`; a geração sem credencial é um stub explícito e a geração real depende de `OPENAI_API_KEY`. Nenhuma saída afirma equivalência sem teste comportamental.

## Documentação de planejamento

- [Requisitos e critérios de aceite](docs/requirements.md)
- [Plano de implementação](docs/implementation-plan.md)
- [ADRs](docs/adr/ADR-001-arquitetura-inicial.md)
- [Instruções para agentes](AGENTS.md)

## Execução prevista

Requer Python 3.14, PostgreSQL e as dependências fixadas no `pyproject.toml`. O Compose usa a porta externa `55432`; a chave OpenAI é opcional para o modo simulado e necessária para geração real.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
langgraph dev --no-browser
```

Para geração real, configure `OPENAI_API_KEY` e opcionalmente `OPENAI_MODEL`. Nunca registre a chave em arquivos ou logs.

## Limitação importante

`ast.parse` ou lint isolado não demonstram equivalência. A comprovação exigirá testes comportamentais com entradas e estados de banco controlados, comparando procedure original e código gerado, inclusive erros, transações, NULLs e efeitos colaterais.

## Estado da primeira fatia

O fluxo Anexo B está executável pelo grafo e pela rota `/modernize`, com persistência de sucesso/falha. A geração atual é simulada e deliberadamente não é uma tradução equivalente. Os testes determinísticos estão em `tests/test_graph.py`; os resultados e limites estão em `docs/implementation-plan.md` e `docs/requirements.md`.
