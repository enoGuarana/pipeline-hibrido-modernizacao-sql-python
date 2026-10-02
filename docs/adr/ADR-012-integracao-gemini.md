# ADR-012 — Integração Gemini via SDK nativo

## Status

Aceita em 2026-10-02; substitui o ADR-009 para novas gerações.

## Contexto

O usuário decidiu usar uma chave criada no Google AI Studio. O desafio exige
LLM real e substituível, mas não obriga um provedor específico. A máquina de
desenvolvimento utiliza uma autoridade certificadora presente no armazenamento
nativo do Windows e ausente no bundle OpenSSL padrão do Python.

## Alternativas

1. SDK nativo `google-genai`.
2. Endpoint Gemini compatível com o SDK OpenAI.
3. Manter OpenAI e exigir outra credencial.
4. Desabilitar a verificação TLS para contornar o certificado local.

## Decisão

Usar `google-genai 2.27.0`, `GEMINI_API_KEY` e modelo configurável por
`GEMINI_MODEL`. Fixar `gemini-3.8-flash` como padrão operacional após
`gemini-2.5-pro` e `gemini-2.5-flash` serem recusados para novos usuários e
`gemini-3.1-pro-preview` apresentar quota gratuita igual a zero. O identificador
foi recomendado pela resposta do próprio endpoint. Usar
`truststore 0.10.4` com HTTPX
para consultar o armazenamento nativo de certificados, sem desabilitar TLS.

A interface interna `generate(prompt) -> LLMResult` permanece estável. O grafo
não conhece detalhes do SDK. Metadados disponíveis — provedor, versão do modelo,
identificador da resposta, versão do prompt e uso — são preservados no relatório.

## Prós e contras

- Prós: SDK oficial e nativo; modelo efetivamente disponível para a chave;
  verificação TLS preservada; impacto localizado ao cliente.
- Contras: nova dependência e contrato de resposta; custo e quotas do projeto;
  comportamento do modelo continua não determinístico.

## Evidência e limites

`google-genai 2.27.0` importou no Python 3.14.8 e `pip check` ficou limpo. A
consulta `models.list` falhou inicialmente por certificado e passou com
`truststore`. A primeira chamada, persistida como `run_id=7`, mostrou que
`gemini-2.5-pro` aparece na lista mas retorna `404` para novos usuários. O
provedor recomendou `gemini-3.1-pro-preview`; a escolha de preview foi aceita
explicitamente, mas o `run_id=8` retornou `429` com quota gratuita igual a
zero. O `run_id=9` mostrou que `gemini-2.5-flash` também foi retirado para
novos usuários e recomendou `gemini-3.8-flash`. Nenhuma equivalência foi
reivindicada.

Com `gemini-3.8-flash`, o `run_id=11` produziu 990 caracteres de código e
reportou 2.384 tokens totais. A saída passou por parsing de Python, mas falhou
no Ruff por usar `Optional[int]`; a única tentativa de reparo terminou em
`503 UNAVAILABLE`. O código e o relatório foram preservados em
`results/run-11`. Os `run_id=10`, `12` e `13` registraram indisponibilidade
temporária do modelo antes da geração. O prompt `modernize_v2` explicita
Python 3.14 e Ruff, mas ainda não obteve resposta por causa desses `503`.

## Condição de revisão

Revisar após a primeira geração real do Anexo B ou se o modelo for descontinuado,
ficar indisponível ao projeto ou apresentar custo/qualidade inadequados. Toda
troca de modelo deve ser registrada; aliases `latest` e previews não devem
substituir silenciosamente o identificador fixado.
