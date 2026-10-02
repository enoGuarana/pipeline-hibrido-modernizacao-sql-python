# ADR-001 — Arquitetura inicial

- **Status:** proposta, não aceita
- **Contexto:** o desafio exige que o backend local seja iniciado pelo LangGraph CLI, além de expor `/health` e `/modernize`.
- **Decisão proposta:** LangGraph CLI será o servidor oficial, com as rotas HTTP integradas ao mesmo runtime do grafo. O estado continuará tipado e o PostgreSQL será acessado por pool assíncrono.
- **Alternativas:** FastAPI como servidor principal; dois modos de execução, CLI e FastAPI.
- **Prós/contras:** atende diretamente ao requisito e mantém grafo/API no mesmo runtime; em contrapartida, depende da configuração vigente da CLI e pode exigir reorganização dos módulos.
- **Evidência:** Python 3.14.8 e LangGraph CLI 0.4.32 iniciaram o grafo `modernization`; `/ok` respondeu 200. O mesmo runtime respondeu 404 para `/health`, e não há aprovação explícita desta direção técnica.
- **Condição de revisão:** revisar a proposta porque a configuração atual não monta as rotas FastAPI no runtime do CLI; aceitar, substituir ou dividir a arquitetura somente após um protótipo integrado e reproduzível.
