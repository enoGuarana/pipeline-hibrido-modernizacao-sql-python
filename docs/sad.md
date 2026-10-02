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
| `pipeline.llm` | Prompt versionado e provedor |
| `pipeline.db` | Pool e histórico JSONB |
| `pipeline.behavioral_evaluation` | Comparação de observações isoladas |

O código gerado não é executado pela API. Detalhes e decisões estão em
`docs/architecture.md` e `docs/adr/`.

## Riscos atuais

Parser não é AST completa de PL/pgSQL; D/F ainda falham validação estática; a
equivalência B–F não está completa; Langfuse não está integrado.
