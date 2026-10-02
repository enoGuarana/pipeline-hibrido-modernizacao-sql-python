# ADR-007 — Estratégia proposta de parsing PL/pgSQL

- **Status:** proposta, não aceita como implementação final
- **Contexto:** SQLGlot 30.21.0 e pglast 8.4 reconheceram o invólucro `CREATE FUNCTION/PROCEDURE` dos anexos B–F, mas ambos falharam ao interpretar o corpo PL/pgSQL completo. `SELECT`, `UPDATE`, CTE recursiva e `FOR UPDATE` foram reconhecidos como SQL; `IF`, `RAISE`, cursores e loops não foram.
- **Alternativas:** usar somente SQLGlot; usar somente pglast; chamar uma LLM diretamente com o SQL; usar pglast para a gramática externa, preservar o corpo e aplicar scanner/IR própria, com SQLGlot apenas para fragmentos SQL isolados.
- **Decisão proposta:** adotar a quarta alternativa para o protótipo: pglast no invólucro, texto procedural preservado, scanner delimitado para construções conhecidas e SQLGlot opcional para fragmentos SQL. Construções desconhecidas serão marcadas como desconhecidas.
- **Prós/contras:** mantém fidelidade ao dialeto PostgreSQL e rastreabilidade da origem, mas exige um scanner próprio e não fornece AST procedural completa; a análise de fragmentos pode perder contexto se for separada incorretamente.
- **Evidência:** experimento documentado em `docs/technical-validation.md`, com resultados individuais para B–F e construções representativas. Os testes foram executados em Python 3.13-32 auxiliar; a compatibilidade dos parsers com Python 3.14 ainda precisa ser verificada.
- **Condição de revisão:** revisar após executar a estratégia contra fixtures preservadas de B–F e comparar falsos positivos/negativos em comentários, strings, cursores, exceções e CTEs. Não aceitar a decisão como AST completa sem essa evidência.
