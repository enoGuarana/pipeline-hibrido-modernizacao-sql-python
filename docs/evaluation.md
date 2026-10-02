# Avaliação reproduzível

## Escopo implementado

O endpoint `GET /evaluation` calcula métricas a partir das linhas terminais de
`modernization_history`. A seleção inclui `success`, `failure` e `partial`,
portanto falhas e gerações simuladas permanecem no denominador. Linhas
`pending` não são avaliações concluídas e ficam fora do denominador.

As métricas atuais são:

- `total_runs`: número de execuções terminais avaliadas;
- `first_attempt_static_approval`: validação estática aprovada na primeira tentativa;
- `after_repair_static_approval`: validação estática aprovada após reparo;
- `failures_by_stage`: erros agrupados pelo estágio informado no relatório;
- `behavioral_equivalence_tested`: somente relatórios explicitamente marcados como `tested`;
- contagens de gerações simuladas e reais.

Uma aprovação estática exige `ast_parse=passed` e `lint=passed` no relatório do
estágio de validação. Isso não demonstra equivalência comportamental.

## Reprodução

Com o servidor e o PostgreSQL isolado em execução:

```powershell
Invoke-RestMethod http://127.0.0.1:8125/evaluation
```

Também é possível reproduzir a avaliação diretamente sobre os artefatos
versionados, sem servidor ou banco:

```powershell
.venv\Scripts\python.exe scripts\evaluate_results.py --results-dir results
```

O script inclui somente diretórios `run-*` completos, informa o denominador e
lista os IDs avaliados. Na rodada registrada, o conjunto exportado contém os
runs 11 e 17–26; o endpoint continua sendo a fonte das métricas de todo o
histórico persistido.

O retorno contém as métricas, os IDs avaliados e as limitações declaradas. A
implementação não fabrica resultados para execuções que ainda não ocorreram.

## Estado e limites conhecidos

O núcleo de avaliação já está disponível em `/evaluation` e o comparador
comportamental isolado está em `pipeline.behavioral_evaluation`. O bônus de
Eval está parcialmente implementado; Langfuse e equivalência B–F continuam
pendentes porque ainda não há traces reais nem execução comparável autorizada.

A primeira saída real Gemini foi persistida no `run_id=11` e exportada para
`results/run-11`. Ela não foi aprovada estaticamente: houve falha Ruff e o
reparo terminou com indisponibilidade do provedor. O `run_id=17`, já com
`gemini-3.5-flash-lite`, gerou e reparou código, mas o resultado final ainda
falhou no Ruff por ordenação de imports; ele está em `results/run-17`.

O `run_id=18` usou `gemini-3.5-flash-lite` e `modernize_v3`. Foi aprovado em
`ast.parse` e Ruff na primeira tentativa e está preservado em `results/run-18`.
O provedor informou 596 tokens de prompt, 149 tokens de saída e 745 totais.
O código não foi executado e `equivalence` continua `not_tested`.

Consulta local após o `run_id=18`: 17 execuções terminais, duas aprovações
estáticas na primeira tentativa — uma simulada e uma real —, zero após reparo,
quatro gerações simuladas, três gerações reais com código e zero equivalências
comportamentais testadas. Há dez erros de geração, dois de validação e um de
reparo; erros distintos da mesma execução são contados em seus estágios.

Após as rodadas reais C–F (`run_id=19–26`), a consulta local passou a registrar
25 execuções terminais, 2 aprovações na primeira tentativa, 3 aprovações após
reparo, 4 gerações simuladas, 11 gerações reais com código e zero equivalências.
Os erros agrupados foram: 10 de geração, 7 de validação e 1 de reparo. D–F
possuem artefatos reais, mas a aprovação estática ou a revisão semântica não
autoriza alegar equivalência.

O núcleo do comparador comportamental foi implementado em
`pipeline.behavioral_evaluation`. Ele compara retorno, estado das tabelas e
erro observado. IDs, timestamps ou outros valores só são normalizados quando
o cenário os declara por caminho explícito; diferenças não declaradas continuam
causando reprovação. O comparador não executa código gerado e não cria
observações fictícias.

- A tentativa histórica com OpenAI registrada terminou com erro de
  quota (`429`); ela não é contada como geração real bem-sucedida.
- As execuções simuladas servem para verificar o fluxo e a persistência, não
  para reivindicar qualidade de tradução.
- Ainda não há harness de equivalência comportamental B–F em banco isolado;
  `behavioral_equivalence_tested` permanece zero até que esses cenários sejam
  realmente executados.
- A execução comportamental B–F permanece bloqueada por falta de rotinas
  legadas instaladas e fixtures de estado/entrada aprovadas. A disponibilidade
  de geração real foi demonstrada para B, mas C–F ainda não foram gerados.
- Modelo, versão do prompt e metadados de uso permanecem nos relatórios de
  cada execução quando o provedor os disponibiliza.
