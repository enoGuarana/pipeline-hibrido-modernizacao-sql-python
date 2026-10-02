# Escalabilidade e operação

## Estado atual

A implementação é um monólito modular adequado ao escopo atual. O pool
assíncrono limita conexões ao PostgreSQL, mas não há ainda benchmark,
controle de fila ou processamento distribuído. Portanto, não há alegação de
capacidade de produção.

## Riscos identificados

| Risco | Evidência atual | Mitigação nesta etapa | Critério para revisão |
|---|---|---|---|
| N+1 em rotinas com cursor/loop | O parser marca `cursor`, `loop` e o risco semântico associado | Preservar a ordem e investigar cada consulta antes de agrupar | Teste comportamental que compare retorno, contagens e efeitos |
| Concorrência no pool | Pool configurável por `DB_POOL_MIN_SIZE` e `DB_POOL_MAX_SIZE` | Limites explícitos no ambiente; sem ajuste baseado em benchmark | Medir latência, filas e conexões sob carga controlada |
| Contexto grande enviado ao LLM | SQL original, IR, análise e schema podem crescer | Não truncar silenciosamente; registrar hashes e limites | Medir tamanho de prompt, custo e taxa de falha por anexo |
| Reparo repetido | O grafo permite no máximo uma tentativa | `generation_attempts < 2` no roteamento | Revisar apenas com taxa de correção e custo observados |
| Falha entre `pending` e finalização | Processo pode cair antes do update final | Lacuna documentada; não prometer recuperação | Implementar reconciliador e testar interrupção controlada |

## Regras de evolução

- Não substituir cursores por operações em lote automaticamente: a ordem,
  locking, exceções e efeitos podem mudar.
- Não adicionar filas, cache ou workers antes de medir o gargalo e definir a
  garantia de consistência necessária.
- Aumentar o pool somente junto com capacidade comprovada do PostgreSQL e
  cenários de carga reproduzíveis.
- O código gerado continua fora do processo da API; execução de avaliação deve
  ocorrer em ambiente isolado e explicitamente autorizado.

## Evidência disponível e limites

Há detecção estrutural de riscos N+1 nos anexos, testes unitários do fluxo e
persistência funcional local. Não há benchmark nem teste de carga executado;
qualquer número de throughput, latência ou custo seria especulativo.
