# ADR-015 — Observabilidade opcional com Langfuse

## Status

Aceita como integração opcional; evidência visual real ainda pendente.

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
`LANGFUSE_HOST` e aceita Cloud ou self-host.

## Prós e contras

- Prós: integração oficial, spans por nó, baixo acoplamento e operação local
  sem credenciais.
- Contras: exige serviço e credenciais para evidência visual; o SDK adiciona
  dependências e custos de armazenamento; a captura ainda não foi produzida.

## Evidência e revisão

O SDK `langfuse 4.16.0` foi instalado no Python 3.14.8; importação, caminho
no-op, `pytest` e Ruff foram verificados. Não há trace remoto nem screenshot
real neste ambiente. Revisar após uma execução com credenciais, verificando no
painel a trace raiz e todos os spans esperados.
