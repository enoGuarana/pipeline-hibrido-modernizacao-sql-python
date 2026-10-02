# Limitações conhecidas

- O parser é estrutural e não é uma AST completa de PL/pgSQL. Ele reconhece
  `$$` e dollar quoting nomeado, mas não cobre toda a gramática procedural.
- A cobertura de extração deve ser interpretada conforme a tabela documentada para B–F; construções desconhecidas podem produzir status parcial.
- Sem a credencial do provedor selecionado, a geração usa somente um stub
  explícito de desenvolvimento; o padrão é Gemini, mas OpenAI/OpenRouter também
  são suportados.
- Nenhum código gerado é executado pela API.
- `ast.parse` e linting demonstram validade estática, não equivalência comportamental.
- A recuperação de uma queda de processo entre o registro `pending` e a finalização ainda não foi implementada.
- O endpoint `/evaluation` e o comparador comportamental estão implementados; há resultados equivalentes para os três cenários B/C registrados, mas D–F continuam sem execução comportamental.
- `scripts/evaluate_results.py` reproduz as métricas sobre artefatos exportados; ele não executa código gerado e não substitui o comparativo no PostgreSQL.
- O adaptador Langfuse está integrado de forma opcional e o trace real do
  `run_id=30` está versionado; não há evidência de custos, retenção, alertas ou
  comportamento sob carga.
- A execução comportamental D–F depende de rotinas legadas instaladas no banco
  isolado, cenários aprovados e uma saída real para comparação; B/C já têm três
  cenários registrados.
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
