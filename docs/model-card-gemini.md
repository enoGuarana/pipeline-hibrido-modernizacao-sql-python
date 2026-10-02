# Model Card — Gemini

## Identificação

- Provedor: Google Gemini API via `google-genai`.
- Modelo configurável por `GEMINI_MODEL`.
- Modelo verificado nos artefatos atuais: `gemini-3.5-flash-lite`.
- Prompt versionado: `modernize_v4` nos artefatos C–F mais recentes.

## Uso pretendido

Gerar proposta de módulo Python a partir de SQL, IR, análise, riscos, contrato
e política de transação.

## Controles

`ast.parse`, Ruff, limite de um reparo, persistência de tentativas, hashes e
relatório por etapa. O código gerado não é executado pela API.

## Limitações

Validade estática não prova equivalência. O modelo pode alterar predicados,
NULL, precisão, locking ou exceções; D–F continuam com limitações documentadas.
Não há benchmark de qualidade ou garantia de estabilidade do modelo.

## Segurança

A chave vem de `GEMINI_API_KEY` e não deve ser registrada. Modelo, prompt e uso
disponível são armazenados quando o provedor informa esses dados.
