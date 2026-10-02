# ADR-011 — Harness de avaliação comportamental

## Status

Proposto e parcialmente implementado; a execução B–F permanece pendente.

## Contexto

Validação estática não demonstra preservação de comportamento. A comparação
precisa observar retorno, alterações persistidas e erros, sem esconder
divergências por normalização implícita. O repositório ainda não contém
rotinas legadas instaladas nem geração real suficiente para executar B–F.

## Alternativas

1. Declarar equivalência com base em `ast.parse`, lint ou geração simulada.
2. Criar um comparador determinístico de observações e executar cenários apenas
   quando o banco, entradas e ambas as implementações estiverem disponíveis.
3. Executar código gerado diretamente no processo da API.

## Decisão proposta

Adotar a alternativa 2. `pipeline.behavioral_evaluation` compara retorno,
estado de tabelas e erro. Valores voláteis só são normalizados por caminhos
explicitamente declarados pelo cenário. O comparador não executa código e não
marca observações ausentes como equivalentes.

## Prós e contras

- Prós: diferenças não declaradas permanecem visíveis; o comparador é
  determinístico e testável sem chamadas externas; separa avaliação da API.
- Contras: ainda exige um executor isolado, fixtures de estado e uma saída real
  de cada lado; normalização incorreta declarada pelo cenário pode ocultar uma
  diferença, por isso deve ser revisada junto com o caso.

## Evidência e condição de revisão

Os testes determinísticos cobrem igualdade com `Decimal`, campos voláteis
declarados e divergência de saldo não declarada. Não há evidência de
equivalência B–F neste momento. Revisar após executar pelo menos um cenário
com a rotina legada e a implementação Python em banco isolado, comparando
retorno, estado, exceções e efeitos transacionais.
