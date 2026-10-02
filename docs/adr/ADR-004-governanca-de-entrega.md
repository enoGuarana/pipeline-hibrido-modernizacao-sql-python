# ADR-004 — Governança da entrega por etapas

- **Status:** aceito para governança da entrega
- **Contexto:** o repositório começou como um esqueleto; `DESAFIO_CONTEXTO.md` confirma que propostas arquiteturais não são decisões implementadas automaticamente. O baseline abaixo é histórico e não descreve o fluxo atual.
- **Alternativas:** implementar tudo de uma vez; congelar a entrega até o contexto aparecer; entregar fatias com evidência e status explícitos.
- **Decisão proposta:** trabalhar em etapas verificáveis, mantendo requisitos, plano e ADRs como documentação de controle. Esta decisão é aceita apenas para o processo, não aprova escolhas técnicas ainda propostas.
- **Prós:** reduz afirmações sem evidência, torna bloqueios visíveis e preserva trabalho existente. **Contras:** demora a produzir uma demo ponta a ponta e exige manutenção documental.
- **Evidência:** leitura de `DESAFIO_CONTEXTO.md`, histórico de commits e documentação atualizada por etapas; o fluxo ponta a ponta, testes e evidências são mantidos separados dos requisitos.
- **Condição de revisão:** revisar se o avaliador resolver as inconsistências do enunciado de modo diferente ou se a entrega passar a exigir um processo de release distinto.
