# ADR-002 — Onde preservar a semântica SQL

- **Status:** proposta, não aceita; fronteiras concretas ainda pendentes
- **Contexto:** as procedures usam transações, `FOR UPDATE`, exceções, `JSONB`, cursores e CTE recursiva; a fronteira de tradução pode alterar comportamento.
- **Decisão proposta:** usar abordagem híbrida por construção: preservar SQL, operações relacionais, locks e transações no PostgreSQL quando isso reduzir risco semântico; usar Python para controle de fluxo, contratos e orquestração; decidir a fronteira por procedure.
- **Alternativas:** reescrever tudo em Python; delegar tudo ao banco.
- **Prós/contras:** tende a preservar semântica e permite modernização gradual; mantém acoplamento ao PostgreSQL, mistura linguagens e exige testes por procedure.
- **Evidência:** leitura das construções dos anexos B–F; nenhuma equivalência foi medida e não há aprovação explícita desta direção técnica.
- **Condição de revisão:** revisar a fronteira após protótipo comparável de pelo menos uma procedure simples e uma transacional, ou diante de divergência comportamental.
