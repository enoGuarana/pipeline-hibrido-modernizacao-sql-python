# PRD — Documento de Requisitos do Produto

## Entrega principal

Pipeline HTTP para modernização assistida de PL/pgSQL com rastreabilidade.

## Requisitos

| ID | Requisito | Estado |
|---|---|---|
| PRD-01 | Receber `source_code`, `schema` e configuração opcional de provedor | Implementado |
| PRD-02 | Executar parsing, análise, geração e validação | Implementado no fluxo documentado |
| PRD-03 | Persistir execução antes e depois do processamento | Implementado |
| PRD-04 | Retornar código e relatório por etapa | Implementado |
| PRD-05 | Limitar reparo a uma tentativa | Implementado |
| PRD-06 | Avaliar resultados exportados | Implementado |
| PRD-07 | Demonstrar equivalência B–F | Parcial: B/C executados; D–F pendentes |
| PRD-08 | Apoiar operação humana por dashboard e observabilidade opcional | Parcial: dashboard implementado; trace remoto pendente |

## Restrições

- Python 3.14 e dependências reproduzíveis.
- Segredos somente no ambiente.
- Falhas devem ser observáveis e persistidas quando o banco estiver disponível.
- Nenhum resultado simulado pode ser apresentado como geração real.

Consultar `docs/requirements.md` para a matriz oficial de aceite.
