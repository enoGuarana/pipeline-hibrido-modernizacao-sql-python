# ADR-007 — Estratégia proposta de parsing PL/pgSQL

- **Status:** substituída como proposta de ferramenta; a IR/scanner própria foi aceita como implementação atual
- **Contexto:** SQLGlot 30.21.0 e pglast 8.4 reconheceram o invólucro `CREATE FUNCTION/PROCEDURE` dos anexos B–F, mas ambos falharam ao interpretar o corpo PL/pgSQL completo. `SELECT`, `UPDATE`, CTE recursiva e `FOR UPDATE` foram reconhecidos como SQL; `IF`, `RAISE`, cursores e loops não foram.
- **Alternativas:** usar somente SQLGlot; usar somente pglast; chamar uma LLM diretamente com o SQL; usar pglast para a gramática externa, preservar o corpo e aplicar scanner/IR própria, com SQLGlot apenas para fragmentos SQL isolados.
- **Decisão histórica:** a quarta alternativa orientou o protótipo, mas pglast/SQLGlot não foram adicionados como dependências obrigatórias. A implementação atual preserva o corpo e usa scanner consciente de comentários/strings para uma IR estrutural; construções desconhecidas são marcadas.
- **Prós/contras:** mantém fidelidade ao dialeto PostgreSQL e rastreabilidade da origem, mas exige um scanner próprio e não fornece AST procedural completa; a análise de fragmentos pode perder contexto se for separada incorretamente.
- **Evidência:** experimento documentado em `docs/technical-validation.md`; a implementação atual tem fixtures A–F, tags `$$`/`$BODY$`, rejeição de tags incompatíveis e testes contra falsos positivos em comentários/strings. O parser continua sem AST procedural completa.
- **Condição de revisão:** revisar se os testes revelarem falsos positivos relevantes ou se um segundo dialeto exigir outra estratégia. Não aceitar a implementação como AST completa.
