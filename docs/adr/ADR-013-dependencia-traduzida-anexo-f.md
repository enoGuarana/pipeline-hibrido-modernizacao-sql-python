# ADR-013 — Dependência Python traduzida para o Anexo F

## Status

Aceita como direção para a próxima implementação; os artefatos atuais de F
não atendem a esta decisão.

## Contexto

O Anexo F chama `fn_saldo_cliente` (Anexo B). A saída real `run-26` chamou a
função PL/pgSQL diretamente por SQL, o que preserva uma dependência do legado e
não demonstra a fronteira SQL/Python proposta para a modernização.

## Alternativas

1. Receber uma função Python `saldo_cliente` como dependência injetada.
2. Importar o módulo Python gerado para B a partir de um pacote de artefatos.
3. Duplicar a implementação de B dentro do módulo gerado para F.
4. Continuar chamando a rotina original no PostgreSQL.

## Decisão proposta/aceita

Usar uma dependência Python injetada para F, com contrato tipado para entrada,
retorno `Decimal` e conexão. O chamador compõe B e F e continua responsável
pela conexão e pela transação. A decisão é aceita para a próxima geração; o
`run-26` permanece como evidência de uma saída que não a cumpriu.

## Prós e contras

- Prós: evita chamada oculta ao legado, facilita testes, explicita a fronteira
  entre módulos e permite trocar a implementação de B.
- Contras: altera o contrato interno de F, exige composição no chamador e
  requer um pacote ou registro de módulos gerados.

## Evidência e limites

Os `run_id=19–26` comprovam geração real e validação parcial, mas não execução
comportamental. O `run-26` chama `fn_saldo_cliente` diretamente e, portanto,
não é evidência de equivalência nem de cumprimento desta decisão.

## Condição de revisão

Revisar após um caso de teste em que B e F Python sejam compostos e comparados
com a referência PostgreSQL no mesmo estado inicial. Se a injeção impedir a
reprodução de transações ou observabilidade, reavaliar a alternativa de pacote
de módulos.
