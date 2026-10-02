# Guia de Integração

## Cliente HTTP

Envie JSON para `POST /modernize`:

```powershell
$body = @{source_code = (Get-Content fixtures/B.sql -Raw); schema = $null} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8125/modernize -ContentType 'application/json' -Body $body
```

## Dados

O campo `schema` é contexto opcional; não cria nem altera automaticamente um
banco. A persistência usa `DATABASE_URL` e `modernization_history`.

## LLM

Defina `GEMINI_API_KEY` e opcionalmente `GEMINI_MODEL`. Nunca envie a chave no
JSON, não a registre em logs e não a versione.

## Resultados

Use `run_id`, `status`, `generated_code` e `report`. Para avaliação exportada,
use `scripts/evaluate_results.py`; para comparação comportamental B/C, use
`scripts/run_behavioral_bc.py` em ambiente isolado.
