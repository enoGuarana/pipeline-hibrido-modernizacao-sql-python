# ADR-004 — Governança da entrega por etapas

- **Status:** aceito para o planejamento documental
- **Contexto:** o repositório tem um esqueleto inicial; `DESAFIO_CONTEXTO.md` foi fornecido durante a revisão e confirma que propostas arquiteturais não são decisões implementadas. Os nós do grafo ainda não executam a pipeline.
- **Alternativas:** implementar tudo de uma vez; congelar a entrega até o contexto aparecer; entregar fatias com evidência e status explícitos.
- **Decisão proposta:** trabalhar em etapas verificáveis, mantendo requisitos, plano e ADRs como documentação de controle. Esta decisão é aceita apenas para o processo, não aprova escolhas técnicas ainda propostas.
- **Prós:** reduz afirmações sem evidência, torna bloqueios visíveis e preserva trabalho existente. **Contras:** demora a produzir uma demo ponta a ponta e exige manutenção documental.
- **Evidência:** leitura de `DESAFIO_CONTEXTO.md`, nós com `NotImplementedError` e rota `/modernize` com `501`; isso não comprova execução do servidor ou do CLI.
- **Condição de revisão:** revisar quando o comando LangGraph CLI e a primeira execução ponta a ponta forem comprovados, ou se o avaliador resolver as inconsistências do enunciado de modo diferente.
