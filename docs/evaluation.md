# Avaliação reproduzível

## O que é medido

O endpoint `GET /evaluation` calcula métricas sobre registros terminais de
`modernization_history`. Entram no denominador `success`, `failure` e `partial`;
registros `pending` ficam fora porque ainda não representam uma execução
concluída.

As métricas são:

- `total_runs`: total honesto de execuções terminais;
- aprovação estática na primeira tentativa;
- aprovação estática após o reparo;
- falhas agrupadas por etapa;
- gerações simuladas e reais;
- equivalência comportamental somente quando o relatório a marca como `tested`.

Uma aprovação estática exige `ast_parse=passed` e `lint=passed` no relatório de
validação. Isso não prova equivalência comportamental.

## Como reproduzir

Com o servidor e o PostgreSQL isolado em execução:

```powershell
Invoke-RestMethod http://127.0.0.1:8125/evaluation
```

Para avaliar os artefatos versionados sem servidor ou banco:

```powershell
.venv\Scripts\python.exe scripts\evaluate_results.py --results-dir results
```

O script informa o denominador e os IDs incluídos. Ele não fabrica resultados
para execuções ausentes e não exclui falhas para melhorar a taxa.

## Estado evidenciado neste checkout

- O conjunto exportado contém `run-11` e `run-17` a `run-26`; a avaliação por
  arquivos usa 11 execuções completas.
- A consulta histórica local após `run_id=26` registrou 25 execuções terminais,
  2 aprovações na primeira tentativa, 3 após reparo, 4 gerações simuladas e 11
  gerações reais com código. Esses números são um snapshot do banco local, não
  uma promessa para outro ambiente.
- O harness `scripts/run_behavioral_bc.py` executou três cenários em schema
  temporário: saldo de B, inativação de C e parâmetro inválido de C. O relatório
  `results/behavioral-bc.json`, datado de 2026-10-02, registra 3/3 equivalentes.
- D–F possuem artefatos reais e revisão semântica em `results/`, mas não há
  comparação comportamental publicada para eles.
- A tentativa histórica com OpenAI terminou em `429 insufficient_quota`; ela
  comprova apenas o caminho controlado de falha, não uma geração aprovada.
- As execuções simuladas verificam fluxo e persistência, não qualidade de
  tradução.

## Comparação comportamental

O comparador em `pipeline.behavioral_evaluation` compara retorno, estado das
tabelas e erro observado. IDs, timestamps e outros valores só são normalizados
quando o cenário declara o caminho explicitamente. O caso inválido de C compara
a categoria semântica `invalid_parameter`; não afirma identidade entre classes
de exceção do PostgreSQL e do Python.

O harness não executa código gerado dentro da API e não cria observações
fictícias. Para ampliar a evidência a D–F, é necessário instalar as rotinas
originais no banco isolado, definir cenários de entrada/estado inicial e
comparar retorno, efeitos e falhas.

## Observabilidade

O adaptador opcional `pipeline.observability` integra observações Langfuse aos
nós/API quando `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY` estão disponíveis.
Sem essas credenciais, a aplicação opera sem observabilidade remota e não há
trace ou screenshot para reivindicar. A integração deve ser instalada com o
extra `observability` e verificada em uma conta/host controlado.

## Limites de interpretação

Modelo, versão do prompt e uso de tokens só são relatados quando o provedor
fornece esses metadados. Validação estática, taxa de sucesso e ausência de erro
não autorizam alegação de preservação de semântica SQL.
