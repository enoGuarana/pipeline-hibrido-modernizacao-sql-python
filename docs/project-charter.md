# Termo de Abertura

## Propósito

Construir um pipeline auditável para analisar rotinas PL/pgSQL e produzir uma
tradução Python validável, preservando decisões, tentativas e limitações.

## Escopo

- API LangGraph com `/health`, `/modernize` e `/evaluation`.
- Parsing/análise estrutural dos anexos B–F.
- Geração Gemini configurável, validação estática e persistência.
- Avaliação comportamental isolada, iniciada por B/C.

Fora do escopo atual: execução automática do código gerado pela API, equivalência
geral D–F e observabilidade Langfuse.

## Critérios de sucesso

1. Execução reproduzível em Python 3.14, PostgreSQL e Compose.
2. Toda execução termina com relatório e status persistidos.
3. Nenhuma alegação de equivalência sem comparação executada.
4. Limitações e decisões rastreáveis em `docs/`.

## Situação

Projeto em desenvolvimento controlado. B/C têm três cenários comportamentais
equivalentes registrados; D–F permanecem pendentes nessa dimensão.
