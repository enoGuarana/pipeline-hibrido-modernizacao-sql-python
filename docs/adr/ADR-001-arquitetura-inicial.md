# ADR-001 — Arquitetura inicial

- **Status:** aceito para a primeira fatia
- **Decisão:** FastAPI expõe o servidor; LangGraph modela quatro nós com `PipelineState`; PostgreSQL é acessado por pool assíncrono; a camada de API não conhece detalhes do grafo.
- **Alternativas:** Flask (menos alinhado ao contrato assíncrono e OpenAPI); orquestração imperativa (mais simples, mas não atende o requisito do grafo); SQLAlchemy (mais abstração, ainda não necessária para a inicialização).
- **Trade-off:** mais componentes e configuração agora, em troca de fronteiras claras para trocar parser, LLM e estratégia de persistência.
- **Limitação:** os nós são somente contratos e levantam `NotImplementedError`; o endpoint `/modernize` retorna `501` deliberadamente.

