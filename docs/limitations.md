# Limitações conhecidas

- O parser é estrutural e não é uma AST completa de PL/pgSQL.
- A cobertura de extração deve ser interpretada conforme a tabela documentada para B–F; construções desconhecidas podem produzir status parcial.
- Sem `GEMINI_API_KEY`, a geração usa somente um stub explícito de desenvolvimento.
- Nenhum código gerado é executado pela API.
- `ast.parse` e linting demonstram validade estática, não equivalência comportamental.
- A recuperação de uma queda de processo entre o registro `pending` e a finalização ainda não foi implementada.
- O endpoint `/evaluation` e o comparador comportamental estão implementados, mas não existem ainda resultados de equivalência B–F.
- A execução B–F depende de rotinas legadas instaladas no banco isolado, cenários aprovados e uma saída real para comparação.
- O `gemini-3.8-flash` apresentou indisponibilidade recorrente. O padrão foi
  alterado para `gemini-3.5-flash-lite` depois de uma sondagem real e da
  verificação no catálogo oficial.
- O `run_id=18` do Anexo B passou em `ast.parse` e Ruff com geração real, mas
  ainda não foi executado nem comparado comportamentalmente com a função original.
- C e E tiveram saídas estaticamente aprovadas após reparo; D e F continuam
  falhando no Ruff nos artefatos mais recentes. A revisão semântica está em
  `results/semantic-review.md`.
- F ainda chama B legado por SQL na saída `run-26`; a dependência Python injetada
  foi aceita como direção no ADR-013, mas ainda não foi implementada no artefato.
