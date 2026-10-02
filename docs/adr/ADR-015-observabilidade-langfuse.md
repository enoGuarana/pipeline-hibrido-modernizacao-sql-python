# ADR-015 — Observabilidade opcional com Langfuse

## Status

Aceita como integração opcional, com trace remoto e evidência visual reais.

## Contexto

O desafio pede traces por execução e por nó. O projeto precisa continuar
executável sem credenciais de observabilidade e não pode registrar o SQL ou
segredos inadvertidamente.

## Alternativas

1. Langfuse opcional via SDK Python.
2. LangSmith via integração do ecossistema LangGraph.
3. Implementar telemetria própria no PostgreSQL.

## Decisão

Usar `langfuse>=4.7,<5` como extra `observability`. A API cria uma trace raiz;
os nós do grafo criam spans. Sem `LANGFUSE_PUBLIC_KEY` e
`LANGFUSE_SECRET_KEY`, o adaptador é no-op. A configuração de host usa
`LANGFUSE_BASE_URL` e deve corresponder à região Cloud ou ao endereço self-host.

## Prós e contras

- Prós: integração oficial, spans por nó, baixo acoplamento e operação local
  sem credenciais.
- Contras: exige serviço e credenciais para evidência visual; o SDK adiciona
  dependências e custos de armazenamento; região, retenção e alertas exigem
  configuração operacional. No `langgraph dev`, o flush síncrono do SDK exige
  `--allow-blocking` ou desacoplamento do envio para não bloquear o event loop.

## Evidência e revisão

O SDK `langfuse 4.16.0` foi instalado no Python 3.14.8; importação, caminho
no-op, `pytest` e Ruff foram verificados. Em 2026-10-02, a execução real
`run_id=30` usou Gemini, terminou com `success` após um reparo e produziu a
trace `efd25f5ff4c957fe922b49900c94d963` no Langfuse US. A API v2 confirmou 13
observações: `modernize`, `parsing`, `semantic_analysis`, `generation`,
`validation`, `repair` e `finalization`. A captura real está em
`docs/assets/langfuse-trace.png`.

A aceitação comprova ingestão, hierarquia, duração e status dos spans. Não
comprova retenção, alertas, atribuição completa de custos nem equivalência do
código gerado. Revisar se o SDK, a região, o modo de exportação ou os requisitos
operacionais mudarem.
