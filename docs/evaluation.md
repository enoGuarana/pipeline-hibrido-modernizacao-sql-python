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

- A execução real com OpenAI registrada até esta etapa terminou com erro de
  quota (`429`); ela não é contada como geração real bem-sucedida.
- As execuções simuladas servem para verificar o fluxo e a persistência, não
  para reivindicar qualidade de tradução.
- Ainda não há harness de equivalência comportamental B–F em banco isolado;
  `behavioral_equivalence_tested` permanece zero até que esses cenários sejam
  realmente executados.
- Modelo, versão do prompt e metadados de uso permanecem nos relatórios de
  cada execução quando o provedor os disponibiliza.
