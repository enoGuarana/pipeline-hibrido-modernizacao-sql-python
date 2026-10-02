# ADR-009 — Integração OpenAI para geração

## Status

Aceita com limitação explícita. A integração alcançou o provedor, mas ainda não
produziu uma geração real bem-sucedida.

## Contexto

O desafio exige uma pipeline híbrida e admite geração simulada somente durante
construção e testes. A geração final precisa usar um provedor real, sem registrar
credenciais e sem confundir validade estática com equivalência.

## Alternativas

1. OpenAI Responses API por meio do SDK oficial.
2. Outro provedor com adaptador próprio.
3. Manter somente o cliente simulado.

## Decisão

Usar o SDK oficial OpenAI e a Responses API, com `OPENAI_MODEL` configurável,
prompt versionado e `store=False`. O cliente permanece isolado em
`src/pipeline/llm/client.py`. Artefatos reais só podem ser exportados de uma
execução persistida com `generation_mode=openai`, código presente e status
`success` ou `partial`.

## Prós e contras

- Prós: integração oficial, modelo configurável, contexto rastreável e bundle
  revisável sem executar o código produzido.
- Contras: custo, dependência de rede/credencial, variabilidade do modelo e
  impossibilidade de declarar equivalência apenas pela resposta.

## Evidência e limites

O SDK `openai 2.54.0` está instalado no Python 3.14.8. Uma chamada real do
Anexo B alcançou a Responses API e terminou com `429 insufficient_quota`; o
`run_id=6` foi persistido como falha, sem código. Em 2026-10-02, a nova
execução não foi iniciada porque `OPENAI_API_KEY` estava vazia no `.env` e no
processo. Isso confirma o tratamento da falha, não geração real bem-sucedida.

O exportador de resultados foi verificado contra o histórico: recusou o
`run_id=6`, não criou artefato e não executou código gerado. Os testes cobrem
exportação elegível e rejeição de geração simulada.

## Condição de revisão

Revisar após a primeira geração real bem-sucedida do Anexo B. Registrar modelo,
versão do prompt, uso realmente retornado, código, validação e limitações. Erros,
timeout, resposta vazia ou conteúdo fora do contrato devem continuar encerrando
a execução como falha.
