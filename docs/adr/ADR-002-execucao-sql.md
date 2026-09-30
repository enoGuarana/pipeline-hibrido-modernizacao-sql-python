# ADR-002 — Onde preservar a semântica SQL

- **Status:** proposta
- **Decisão provisória:** preservar queries e transações no PostgreSQL quando isso reduzir risco semântico; usar Python para orquestração e regras que precisem sair do banco.
- **Alternativas:** reescrever tudo em Python (mais portável, maior risco em transações, NULL, tipos e locking); delegar tudo ao banco (maior fidelidade, menor modernização).
- **Trade-off:** abordagem híbrida exige testes por procedure e contratos de transação, mas limita divergências em `FOR UPDATE`, `EXCEPTION`, CTEs e tipos numéricos.
- **Limitação:** nenhuma equivalência foi medida; decisão só poderá ser confirmada após testes comportamentais contra o banco legado.

