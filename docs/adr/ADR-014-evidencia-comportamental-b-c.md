# ADR-014 — Evidência comportamental inicial B/C

## Status

Aceita para os cenários registrados; não generalizada para D–F.

## Contexto

Validação estática não demonstra que o SQL original e o Python gerado retornam
os mesmos valores ou produzem os mesmos efeitos. Os artefatos reais de B e C,
as rotinas originais e um PostgreSQL isolado ficaram disponíveis para uma
comparação controlada.

## Alternativas

1. Declarar equivalência de B–F a partir de `ast.parse` e Ruff.
2. Executar referência e tradução em schema temporário, com estado inicial
   reproduzível, comparando retorno, tabelas e erro.
3. Executar os módulos gerados no processo da API.

## Decisão

Adotar a alternativa 2. `scripts/run_behavioral_bc.py` instala as funções
originais B/C em um schema temporário, sem alterar o banco persistente, executa
os artefatos `results/run-18` e `results/run-23` e remove o schema ao final.

## Prós e contras

- Prós: comparação reproduzível, isolamento explícito e efeitos observáveis.
- Contras: a cobertura depende dos cenários escolhidos; a categoria de erro do
  caso inválido é uma normalização semântica, não identidade de exceção.

## Evidência e condição de revisão

`results/behavioral-bc.json` registra três casos executados em 2026-10-02:
saldo de B, inativação de C com 30 dias e parâmetro inválido de C. Os três
foram equivalentes, incluindo estado das tabelas e auditoria. Isso não aceita
D–F nem prova equivalência para entradas não cobertas.

Revisar após executar D–F com fixtures de estado aprovadas e comparar também
locks, rollback, precisão, múltiplas linhas e dependências entre rotinas.
