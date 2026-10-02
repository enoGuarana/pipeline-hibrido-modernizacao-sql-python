# Pipeline Híbrido de Modernização SQL → Python

Pipeline auditável para analisar rotinas PL/pgSQL, gerar uma proposta Python e
validá-la sem esconder falhas ou afirmar equivalência sem evidência.

> Estado atual: B/C possuem três cenários comportamentais equivalentes
> registrados. D–F ainda precisam de validação comportamental.

## Fluxo

```text
POST /modernize → pending → parsing → análise → geração → validação
                         └──────── PostgreSQL: modernization_history
```

O pipeline preserva o SQL original, produz uma representação intermediária,
identifica riscos, usa contexto estruturado no modelo e valida a saída com
`ast.parse` e Ruff. O código gerado não é executado pela API.

## Executar localmente

Pré-requisitos: Python 3.14, Docker Desktop com Compose e uma chave Gemini
somente quando a geração real for necessária.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
langgraph dev --no-browser
```

Verifique a API:

```powershell
Invoke-RestMethod http://127.0.0.1:8125/health
Invoke-RestMethod http://127.0.0.1:8125/evaluation
```

Para geração real, configure a chave apenas no ambiente:

```powershell
$env:GEMINI_API_KEY = "sua-chave-local"
$env:GEMINI_MODEL = "gemini-3.5-flash-lite"
```

Nunca versione a chave nem a envie no corpo da requisição.

## Usar a API

```powershell
$body = @{source_code = (Get-Content fixtures/B.sql -Raw); schema = $null} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8125/modernize -ContentType "application/json" -Body $body
```

A resposta contém `run_id`, `status`, código quando disponível e relatório por
etapa. Os status possíveis são `success`, `failure`, `partial` e `pending`.

## Testar e avaliar

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check src tests scripts
.venv\Scripts\python.exe scripts/evaluate_results.py --results-dir results
```

Comparação comportamental isolada de B/C:

```powershell
.venv\Scripts\python.exe scripts/run_behavioral_bc.py --database-url "postgresql://postgres:postgres@localhost:55432/modernization"
```

O harness usa schema temporário, compara a rotina original com o Python gerado
e remove o schema ao terminar. A evidência está em
`results/behavioral-bc.json`.

## Decisões e trade-offs

- **Monólito modular:** reduz operação e mantém fronteiras claras; ainda há um
  processo central.
- **LangGraph CLI:** atende ao servidor exigido e organiza o fluxo por nós; a
  combinação de versões do runtime tem limitações documentadas.
- **PostgreSQL:** preserva tipos, queries, locking e transações; exige banco
  disponível localmente.
- **Gemini com prompt versionado:** permite geração rastreável; a saída ainda
  pode conter erros semânticos.
- **Parsing híbrido:** preserva SQL e marca construções desconhecidas; não é
  uma AST completa de PL/pgSQL.
- **Um único reparo:** limita custo e ciclos infinitos; uma saída inválida é
  preservada como falha.

Detalhes estão em [docs/architecture.md](docs/architecture.md) e nos
[ADRs](docs/adr/).

## Limitações e próximos passos

- Validade estática não prova equivalência.
- B/C têm três cenários equivalentes; D–F ainda não têm comparação executada.
- D/F possuem falhas de validação estática documentadas; E tem riscos semânticos
  ainda não testados.
- A dependência Python do Anexo F e a integração Langfuse estão pendentes.
- Recuperação automática de crashes não está implementada.

Com mais tempo: corrigir D/F, implementar F por injeção de dependência, criar
cenários comportamentais D–F, integrar Langfuse com traces reais e reproduzir a
entrega em ambiente limpo.

## Documentação

- [Índice de documentos](docs/README.md)
- [Requisitos e aceite](docs/requirements.md)
- [Plano de implementação](docs/implementation-plan.md)
- [Avaliação](docs/evaluation.md)
- [Runbook](docs/runbook.md)
- [Guia de integração](docs/integration-guide.md)
