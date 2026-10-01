# ADR-008 — Primeiro fluxo com geração simulada

## Status

Aceita somente para a etapa 5; não é decisão de geração final.

## Contexto

O primeiro fluxo precisa demonstrar roteamento, relatórios, validação e persistência sem depender de credenciais ou de um provedor externo de LLM.

## Alternativas

1. Chamar um provedor real já nesta etapa.
2. Deixar os nós sem implementação.
3. Usar um cliente simulado explícito e validar o resultado estático.

## Decisão proposta/aceita

Adotar a alternativa 3 para o Anexo B. O código gerado é um stub identificado como simulado, e o relatório marca `equivalence=not_tested`.

## Prós e contras

- Prós: fluxo reproduzível, sem segredo externo, permite testar falhas e persistência.
- Contras: não mede geração real, não prova tradução nem equivalência comportamental.

## Evidência e limites

Os testes determinísticos passaram em 3 casos; a CLI carregou a aplicação; uma chamada local persistiu `run_id=4` com status `success`. A evidência cobre apenas o stub e o Anexo B.

## Condição de revisão

Revisar ao integrar o provedor real ou quando a geração dos anexos C–F começar; o stub não pode ser apresentado como resultado de LLM.
