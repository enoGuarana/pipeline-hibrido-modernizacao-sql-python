# SAD — Documento de Arquitetura de Software

## Visão

Monólito modular: API → persistência de `pending` → LangGraph → finalização.

```text
Cliente HTTP → pipeline.api → LangGraph
                         parsing → análise → geração → validação
                              └── PostgreSQL: modernization_history
```

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `pipeline.api` | HTTP, ciclo da execução e resposta |
| `pipeline.graph` | Nós, estado e roteamento |
| `pipeline.parsing` | IR estrutural e construções desconhecidas |
| `pipeline.contracts` | Entrada, resposta, IR, erros e relatórios |
| `pipeline.llm` | Prompt versionado e adaptador selecionável para Gemini, OpenAI e OpenRouter |
| `pipeline.db` | Pool e histórico JSONB |
| `pipeline.behavioral_evaluation` | Comparação de observações isoladas |
| `pipeline.observability` | Integração opcional com Langfuse, sem bloquear a execução sem credenciais |
| `dashboard.py` | Operação humana: submissão, métricas e auditoria do histórico |

O código gerado não é executado pela API. Detalhes e decisões estão em
`docs/architecture.md` e `docs/adr/`.

## Riscos atuais

Parser não é AST completa de PL/pgSQL; D/F ainda falham validação estática; a
equivalência comportamental está demonstrada somente em três cenários de B/C.
Langfuse está integrado como opção, mas não há trace remoto versionado neste
ambiente. O dashboard depende da API e/ou do PostgreSQL estarem disponíveis.
