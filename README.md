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

## Desenho do grafo

```text
                 ┌─────────────────────┐
                 │  iniciar execução   │
                 │ persistir pending   │
                 └──────────┬──────────┘
                            ▼
                    ┌───────────────┐
                    │    parsing    │
                    └───────┬───────┘
                            │ sucesso
                            ▼
                    ┌───────────────┐
                    │ análise       │
                    │ semântica     │
                    └───────┬───────┘
                            │ sucesso
                            ▼
                    ┌───────────────┐
                    │ geração       │◄──────────────┐
                    │ provedor/stub │               │
                    └───────┬───────┘               │
                            ▼                        │
                    ┌───────────────┐                │
                    │ validação     │                │
                    │ AST + Ruff    │                │
                    └───┬───────┬───┘                │
                        │       │                    │
             aprovado ──┘       └── inválido ──► reparo
                        │                            │
                        │                    no máximo 1 tentativa
                        │                            │
                        └───────────────┬────────────┘
                                        ▼
                              ┌─────────────────┐
                              │ finalização     │
                              │ sucesso/falha   │
                              │ persistir JSONB │
                              └─────────────────┘

 Falhas em parsing, análise ou geração deixam os próximos nós como
 `stage_skipped` e seguem para a finalização. Portanto, o efeito é equivalente
 a uma saída controlada para finalização, mas o relatório preserva cada etapa
 ignorada para rastreabilidade. Falhas de validação podem entrar no reparo;
 após uma única tentativa, seguem para finalização.
```

O estado compartilhado é tipado em `pipeline.state`; contratos de entrada,
saída, IR, erros e relatórios ficam em `pipeline.contracts`. O grafo não executa
o código produzido e não transforma validação estática em equivalência.

## Executar localmente

Pré-requisitos: Python 3.14, Docker Desktop com Compose e uma chave do
provedor escolhido somente quando a geração real for necessária.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
langgraph dev --no-browser
```

Em outro terminal, para abrir o painel interno de operação:

```powershell
pip install -e ".[dashboard]"
streamlit run dashboard.py
```

O painel usa `PIPELINE_API_URL` quando ela é definida e `DATABASE_URL` para a
auditoria PostgreSQL. Sem URL explícita, tenta `http://localhost:8000` e, somente
em erro de conexão, `http://localhost:8125`. Ele não substitui a API: serve para
submissão manual, avaliação e revisão Human-in-the-loop.

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

### Escolher provedor por requisição

O padrão é Gemini. A requisição pode selecionar `gemini`, `openrouter` ou
`openai`, além de informar uma chave e um modelo específicos. A chave enviada
tem prioridade; sem ela, o sistema consulta a variável do provedor no ambiente.

```json
{
  "source_code": "CREATE FUNCTION ...",
  "schema": null,
  "provider": "openrouter",
  "api_key": "chave-apenas-para-esta-execucao",
  "model_name": "meta-llama/llama-3-8b-instruct"
}
```

As chaves são usadas somente durante a execução e não são persistidas em
`modernization_history`, relatórios ou metadados. O grafo continua com uma
única chamada sequencial ao provedor selecionado.

Variáveis de fallback:

| Provedor | Chave | Modelo padrão |
|---|---|---|
| `gemini` | `GEMINI_API_KEY` ou `GOOGLE_API_KEY` | `GEMINI_MODEL` ou `gemini-3.5-flash-lite` |
| `openrouter` | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL` ou `openai/gpt-4o-mini` |
| `openai` | `OPENAI_API_KEY` | `OPENAI_MODEL` ou `gpt-4o-mini` |

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

## Observabilidade Langfuse

O projeto possui integração opcional com o SDK oficial `langfuse` v4. Quando as
credenciais obrigatórias estão configuradas, cada chamada de `/modernize` cria
uma trace raiz e spans para `parsing`, `semantic_analysis`, `generation`,
`validation`, `repair` e `finalization`:

```powershell
pip install -e ".[dev,observability]"
$env:LANGFUSE_PUBLIC_KEY = "pk-lf-..."
$env:LANGFUSE_SECRET_KEY = "sk-lf-..."
$env:LANGFUSE_HOST = "https://cloud.langfuse.com"
$env:LANGFUSE_TRACING_ENVIRONMENT = "local"
```

Sem as credenciais, o adaptador executa em modo no-op. Assim, o pipeline local
continua funcional sem enviar dados acidentalmente. A integração não registra
chaves e envia apenas identificadores, status e metadados mínimos — não o SQL
completo.

### Captura de tela da evidência

A captura deve mostrar a trace de uma chamada `/modernize` no painel Langfuse,
com a árvore de spans acima e o status da geração/validação. Ela ainda não é
versionada neste checkout: não há projeto Langfuse nem credenciais disponíveis
para produzir uma captura real. Não foi incluída uma imagem simulada.

Para gerar a evidência após configurar o serviço:

1. Inicie a aplicação e execute uma chamada de `/modernize`.
2. Abra a trace retornada no painel Langfuse.
3. Salve a imagem como `docs/assets/langfuse-trace.png`.
4. Adicione ao README a imagem real salva em `docs/assets/langfuse-trace.png`.

Referências oficiais: [SDK Python Langfuse](https://langfuse.com/docs/observability/sdk/overview),
[tipos de observação](https://langfuse.com/docs/observability/features/observation-types)
e [self-host com Docker Compose](https://langfuse.com/self-hosting/deployment/docker-compose).

## Decisões e trade-offs

- **Monólito modular:** reduz operação e mantém fronteiras claras; ainda há um
  processo central.
- **LangGraph CLI:** atende ao servidor exigido e organiza o fluxo por nós; a
  combinação de versões do runtime tem limitações documentadas.
- **PostgreSQL:** preserva tipos, queries, locking e transações; exige banco
  disponível localmente.
- **Gemini com prompt versionado:** permite geração rastreável; a saída ainda
  pode conter erros semânticos.
- **Interface agnóstica de provedor:** mantém o SDK Gemini para o padrão e usa
  `openai` com `base_url` do OpenRouter para APIs compatíveis; aumenta opções,
  mas exige que o modelo escolhido aceite o formato de chat e o contrato de
  saída textual.
- **Parsing híbrido:** preserva SQL e marca construções desconhecidas; não é
  uma AST completa de PL/pgSQL. O invólucro aceita `$$` e tags nomeadas, como
  `$BODY$`, exigindo o mesmo delimitador na abertura e no fechamento.
- **Um único reparo:** limita custo e ciclos infinitos; uma saída inválida é
  preservada como falha.
- **Langfuse opcional:** adiciona traces por execução e nó quando configurado;
  não obriga credenciais nem infraestrutura de observabilidade no modo local.

Bibliotecas externas adicionadas nesta etapa:

- `langfuse>=4.7,<5`, como dependência opcional `observability`, para traces
  OpenTelemetry e inspeção de execuções. Ela foi escolhida por ter SDK Python
  oficial e integração baseada em observações; não é necessária para o caminho
  principal sem observabilidade.

Detalhes estão em [docs/architecture.md](docs/architecture.md) e nos
[ADRs](docs/adr/).

## Limitações e próximos passos

- Validade estática não prova equivalência.
- B/C têm três cenários equivalentes; D–F ainda não têm comparação executada.
- D/F possuem falhas de validação estática documentadas; E tem riscos semânticos
  ainda não testados.
- A dependência Python do Anexo F ainda está pendente. Langfuse está integrado
  opcionalmente, mas trace remoto/screenshot dependem de credenciais e host.
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
- [Estado da documentação](docs/documentation-status.md)
