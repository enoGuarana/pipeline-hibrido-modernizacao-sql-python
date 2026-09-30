# ADR-003 — Uso de LLM na geração

- **Status:** proposta
- **Decisão provisória:** se LLM for usada, receberá AST/estrutura semântica, riscos e schema, nunca apenas SQL bruto; a saída passará por `ast.parse`, lint e testes.
- **Alternativas:** regras determinísticas (reprodutíveis, cobertura inicial limitada); LLM direta (rápida, mas difícil de auditar e mais propensa a alucinação).
- **Trade-off:** contexto estruturado aumenta custo/latência, mas torna o prompt rastreável e a falha diagnosticável.
- **Limitação:** nenhum provedor, prompt ou chamada foi implementado nesta fatia.

