# Contratos de API e Dados

## `POST /modernize`

Entrada mínima:

```json
{"source_code": "CREATE FUNCTION ...", "schema": null}
```

Resposta resumida:

```json
{"run_id": 18, "status": "success", "generated_code": "...", "report": {"stages": [], "errors": []}}
```

`status` pode ser `success`, `failure`, `partial` ou `pending`. O contrato
tipado está em `src/pipeline/contracts.py`; o estado está em
`src/pipeline/state.py`.

## Outras rotas

- `GET /health`: disponibilidade da API.
- `GET /evaluation`: métricas do histórico terminal.

## Persistência

`modernization_history` guarda origem, código gerado, relatório JSONB, status e
timestamp. Credenciais nunca fazem parte do contrato ou relatório.

## Erros

Erros têm `code`, `message`, `stage`, `recoverable` e `details` opcionais.
Falha estática não é equivalência comportamental.
