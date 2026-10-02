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

O retorno contém as métricas, os IDs avaliados e as limitações declaradas. A
implementação não fabrica resultados para execuções que ainda não ocorreram.

## Estado e limites conhecidos

O núcleo de avaliação já está disponível em `/evaluation` e o comparador
comportamental isolado está em `pipeline.behavioral_evaluation`. O bônus de
Eval está parcialmente implementado; Langfuse e equivalência B–F continuam
pendentes porque ainda não há traces reais nem execução comparável autorizada.

A primeira saída real Gemini foi persistida no `run_id=11` e exportada para
`results/run-11`. Ela não foi aprovada estaticamente: houve falha Ruff e o
reparo terminou com indisponibilidade do provedor. As tentativas seguintes
também receberam `503`; elas permanecem no denominador como falhas.

Consulta local após o `run_id=13`: 12 execuções terminais, uma aprovação
estática na primeira tentativa — proveniente do fluxo simulado —, zero após
reparo, quatro gerações simuladas, uma geração real e zero equivalências
comportamentais testadas. Há sete erros de geração, um de validação e um de
reparo; erros distintos da mesma execução são contados em seus estágios.

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
- A execução B–F permanece bloqueada por falta de rotinas legadas instaladas,
  fixtures de estado/entrada aprovadas e geração real disponível para comparar.
- Modelo, versão do prompt e metadados de uso permanecem nos relatórios de
  cada execução quando o provedor os disponibiliza.
