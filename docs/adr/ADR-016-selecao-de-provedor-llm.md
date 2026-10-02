# ADR-016 — Seleção de provedor LLM por requisição

## Status

Aceita para a camada de geração; equivalência do código continua independente
do provedor.

## Contexto

O pipeline usava Gemini diretamente no nó de geração. O cliente precisa poder
selecionar Gemini, OpenAI ou um endpoint compatível, como OpenRouter, sem criar
novos nós no LangGraph.

## Alternativas

1. Criar um nó por provedor.
2. Usar uma fábrica simples dentro do cliente LLM.
3. Adicionar um sistema de plugins e registro dinâmico.

## Decisão

Manter um único nó sequencial. `ModernizeRequest` recebe `provider`, `api_key` e
`model_name`; esses valores seguem no `PipelineState`. O cliente Gemini continua
com `google-genai`; `openai` e `openrouter` usam `AsyncOpenAI`, sendo que
OpenRouter altera apenas `base_url` para `https://openrouter.ai/api/v1`.

A prioridade de configuração é: valor enviado na requisição, variável de
ambiente do provedor e modelo padrão. A chave nunca entra no relatório.

## Prós e contras

- Prós: grafo inalterado, chamada única e interface de saída uniforme.
- Contras: provedores compatíveis podem divergir em modelos, limites,
  ferramentas e formato de resposta; a validação estática não resolve essa
  diferença semântica.

## Evidência e revisão

Testes cobrem defaults Gemini, override de requisição e cliente OpenRouter
compatível com OpenAI usando cliente falso. A integração real de cada conta e
modelo depende de credenciais e não foi reivindicada. Revisar se um provedor
exigir streaming, multimodalidade, ferramentas ou contrato diferente de texto.
