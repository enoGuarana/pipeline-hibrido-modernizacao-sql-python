# Guia de Usuário

## Pré-requisitos

Python 3.14, Docker e PostgreSQL isolado. Para geração real, uma chave Gemini
no ambiente; sem ela, use o modo simulado explicitamente identificado.

## Uso básico

1. Suba PostgreSQL e servidor conforme o README.
2. Envie `source_code` e, se necessário, `schema` para `/modernize`.
3. Guarde o `run_id`, código e relatório.
4. Revise parsing, riscos, validação e limitações antes de usar qualquer saída.

## Interpretação

`success` significa que as validações da etapa passaram. Não significa que o
código preserva comportamento. `failure` exige análise do relatório; `partial`
indica cobertura incompleta.
