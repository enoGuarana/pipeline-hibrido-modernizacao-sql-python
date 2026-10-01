# Limitações conhecidas

- O parser é estrutural e não é uma AST completa de PL/pgSQL.
- A cobertura de extração deve ser interpretada conforme a tabela documentada para B–F; construções desconhecidas podem produzir status parcial.
- Sem `OPENAI_API_KEY`, a geração usa somente um stub explícito de desenvolvimento.
- Nenhum código gerado é executado pela API.
- `ast.parse` e linting demonstram validade estática, não equivalência comportamental.
- A recuperação de uma queda de processo entre o registro `pending` e a finalização ainda não foi implementada.
- O endpoint `/evaluation` e o comparador comportamental estão implementados, mas não existem ainda resultados de equivalência B–F.
- A execução B–F depende de rotinas legadas instaladas no banco isolado, cenários aprovados e uma saída real para comparação.
