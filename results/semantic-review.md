# Revisão semântica dos artefatos reais B–F

Esta revisão inspeciona código e relatórios gerados pelo Gemini. Nenhum artefato
foi executado. Validade estática não foi convertida em equivalência.

## Categorias

| Anexo | Comportamento plausível | Divergência ou limitação observada |
|---|---|---|
| B | `run-18` preserva `COALESCE`, `Decimal` e SQL parametrizado; `ast.parse` e Ruff passaram | Sem comparação com a função original em banco |
| C | `run-23` preserva validação de dias, `UPDATE`, `rowcount` e auditoria JSONB; passou após reparo | `OUT`/`ROW_COUNT` e auditoria não foram comparados em execução |
| D | `run-24` preserva `FOR UPDATE`, débito/crédito, inserts e tratamento explícito de erros no texto gerado | Falhou Ruff; quantização e auditoria/rollback exigem decisão e teste de transação; a saída não foi aprovada |
| E | `run-21` preserva a ordem geral do lote, busca de taxa, cálculo por tipo, tarifa e logs | Falhou Ruff em nova rodada; conversão de `NULL` de taxa para zero altera `CONTINUE`; cursor foi materializado com `fetchall`; precisão e repetição não foram testadas |
| F | `run-26` preserva CTE recursiva, retorno tabular, NOTICE/WARNING e fallback em parte | Falhou Ruff; chama B legado por SQL, omite o filtro de contas do cliente no movimento e não constitui tradução independente |

## Evidência de validação

- C: `run-19` e `run-23` terminaram com aprovação estática após reparo.
- E: `run-21` terminou com aprovação estática após reparo, mas a revisão acima
  mantém limitações semânticas não testadas.
- D e F: `run-24` e `run-26` terminaram com falha Ruff após uma tentativa de
  reparo; os códigos e relatórios foram preservados.
- Os bundles são exportados com SQL, Python, relatório, modelo e prompt. Os
  hashes de B foram verificados; a política de `LF` está em `.gitattributes`.

## Critério de avanço

Não reivindicar equivalência até instalar schema e rotinas de referência em
banco isolado, definir entradas/estado inicial e comparar retorno, alterações,
erros, locking, arredondamento, auditoria e fallback.
