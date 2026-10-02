# Runbook de Operações

## Subir ambiente

```powershell
docker compose up -d postgres
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
langgraph dev --no-browser
```

O padrão é Gemini. Para geração real, configure `GEMINI_API_KEY` e
`GEMINI_MODEL`. Também são aceitos `OPENAI_API_KEY`/`OPENAI_MODEL` e
`OPENROUTER_API_KEY`/`OPENROUTER_MODEL`; a requisição pode selecionar o
provedor e o modelo sem alterar o grafo. Nunca imprima chaves nos logs.

Para a ferramenta interna de operação:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dashboard]"
$env:PIPELINE_API_URL = "http://127.0.0.1:8125"
.venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8501
```

`PIPELINE_API_URL` é opcional no ambiente local. Quando ausente, o dashboard
tenta as portas 8000 e 8125, nessa ordem, fazendo fallback somente em falha de
conexão.

## Verificar

```powershell
Invoke-RestMethod http://127.0.0.1:8125/health
Invoke-RestMethod http://127.0.0.1:8125/evaluation
```

## Diagnóstico

- PostgreSQL: `docker compose ps` e `docker compose logs postgres`.
- API: verificar logs do processo LangGraph e `/health`.
- Execução: consultar `run_id` e status em `modernization_history`.
- LLM: confirmar o modelo/chave do provedor escolhido sem imprimi-la; um erro
  de quota ou autenticação deve aparecer como falha controlada no relatório.
- Dashboard: conferir `PIPELINE_API_URL` quando uma URL explícita for necessária;
  a aba de auditoria precisa de uma `DATABASE_URL` válida para consultar o PostgreSQL.

## Incidentes

Não apagar ou resetar banco existente. Preserve `run_id`, relatório e logs,
classifique a falha e registre a ação. Recuperação automática de crash não está
implementada e não deve ser prometida.
