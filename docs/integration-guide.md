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

O padrão é Gemini. Também são aceitos `openrouter` e `openai`:

```json
{
  "source_code": "CREATE FUNCTION ...",
  "provider": "openrouter",
  "api_key": "chave-da-execucao",
  "model_name": "meta-llama/llama-3-8b-instruct"
}
```

Se `api_key` não for enviada, use `GEMINI_API_KEY`/`GOOGLE_API_KEY`,
`OPENROUTER_API_KEY` ou `OPENAI_API_KEY`, conforme o provedor. Nunca registre
chaves em logs, JSON persistido ou controle de versão.

## Resultados

Use `run_id`, `status`, `generated_code` e `report`. Para avaliação exportada,
use `scripts/evaluate_results.py`; para comparação comportamental B/C, use
`scripts/run_behavioral_bc.py` em ambiente isolado.
