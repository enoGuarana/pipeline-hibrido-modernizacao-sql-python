# ADR-009 — Integração OpenAI para geração

## Status

Aceita para a etapa de geração real; verificação real depende de `OPENAI_API_KEY` disponível.

## Contexto

O desafio exige uma pipeline híbrida e permite geração simulada somente durante construção/testes. A geração final precisa usar um provedor real, sem registrar credenciais.

## Alternativas

1. OpenAI Responses API por meio do SDK oficial.
2. Outro provedor com adaptador próprio.
3. Manter somente o cliente simulado.

## Decisão

Usar o SDK oficial OpenAI e a Responses API, com `OPENAI_MODEL` configurável, prompt versionado e `store=False`. O cliente fica isolado em `src/pipeline/llm/client.py`.

## Prós e contras

- Prós: integração oficial, resposta textual simples, modelo configurável e contexto rastreável.
- Contras: custo, dependência de rede/credencial, variabilidade do modelo e impossibilidade de declarar equivalência apenas pela resposta.

## Evidência e limites

O pacote `openai 2.54.0` foi instalado no Python 3.14.8. A integração foi verificada por importação e testes sem credencial; nenhuma chamada real foi executada porque nenhuma chave foi disponibilizada.

## Condição de revisão

Revisar após a primeira chamada real B, especialmente contrato da resposta, uso reportado e custo. Erros, timeout, resposta vazia e conteúdo fora do contrato devem finalizar a execução como falha.
