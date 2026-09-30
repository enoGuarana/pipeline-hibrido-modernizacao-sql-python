# Pipeline Híbrido de Modernização SQL → Python

Implementação incremental do desafio técnico. Esta primeira fatia entrega a inicialização do servidor, as rotas contratuais e a conexão/configuração inicial do PostgreSQL.

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

O estado compartilhado é `PipelineState`, um `TypedDict`. Os nós já estão registrados em `langgraph.json`, mas seus corpos ainda são contratos que levantam `NotImplementedError`. Até a implementação das etapas, `/modernize` responde `501` e não afirma equivalência.

## Executar

Requer Python 3.14, Docker e dependências do `pyproject.toml`:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/modernization"
uvicorn pipeline.api:app --app-dir src --reload
```

Verificações manuais:

```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/modernize -H "Content-Type: application/json" -d '{"source_code":"SELECT 1;"}'
```

O LangGraph CLI poderá carregar o grafo com `langgraph dev` após a instalação das dependências. Isso não transforma os nós pendentes em uma pipeline funcional.

## Escopo e próximos passos

Veja a [matriz de requisitos](requirements-matrix.md) e os [ADRs](docs/adr/ADR-001-arquitetura-inicial.md). Ainda faltam parser/AST, análise de riscos, geração, validação, persistência de cada desfecho, testes dos anexos B–F, observabilidade e evaluation.

## Limitação importante

`ast.parse` ou lint isolado não demonstram equivalência. A comprovação exigirá testes comportamentais com entradas e estados de banco controlados, comparando procedure original e código gerado, inclusive erros, transações, NULLs e efeitos colaterais.

