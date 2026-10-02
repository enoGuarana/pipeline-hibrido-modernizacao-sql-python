# Runbook de Operações

## Subir ambiente

```powershell
docker compose up -d postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
langgraph dev --no-browser
```

## Verificar

```powershell
Invoke-RestMethod http://127.0.0.1:8125/health
Invoke-RestMethod http://127.0.0.1:8125/evaluation
```

## Diagnóstico

- PostgreSQL: `docker compose ps` e `docker compose logs postgres`.
- API: verificar logs do processo LangGraph e `/health`.
- Execução: consultar `run_id` e status em `modernization_history`.
- LLM: confirmar `GEMINI_MODEL` e presença da chave sem imprimi-la.

## Incidentes

Não apagar ou resetar banco existente. Preserve `run_id`, relatório e logs,
classifique a falha e registre a ação. Recuperação automática de crash não está
implementada e não deve ser prometida.
