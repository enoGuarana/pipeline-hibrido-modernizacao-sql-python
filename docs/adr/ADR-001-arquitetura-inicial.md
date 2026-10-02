# ADR-001 — Arquitetura inicial

- **Status:** substituída pelo ADR-006; mantida como histórico
- **Contexto:** o desafio exige que o backend local seja iniciado pelo LangGraph CLI, além de expor `/health` e `/modernize`.
- **Decisão proposta:** LangGraph CLI será o servidor oficial, com as rotas HTTP integradas ao mesmo runtime do grafo. O estado continuará tipado e o PostgreSQL será acessado por pool assíncrono.
- **Alternativas:** FastAPI como servidor principal; dois modos de execução, CLI e FastAPI.
- **Prós/contras:** atende diretamente ao requisito e mantém grafo/API no mesmo runtime; em contrapartida, depende da configuração vigente da CLI e pode exigir reorganização dos módulos.
- **Evidência:** o protótipo posterior configurou `http.app` para `pipeline.api:app`; o CLI carregou a aplicação e as rotas foram exercitadas localmente.
- **Condição de revisão:** revisar se a integração customizada deixar de ser suportada pela combinação de versões adotada.
