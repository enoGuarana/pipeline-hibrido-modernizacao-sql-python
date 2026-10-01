# ADR-010 — Compatibilidade do runtime LangGraph

## Status

Aceita provisoriamente para reprodutibilidade local; bloqueador conhecido para atualização do runtime.

## Contexto

O projeto precisa Python 3.14 e LangGraph CLI. A CLI publicada disponível é `0.4.32`; ela instalou `langgraph-api 0.10.3`, que emitiu alerta de EOL. A versão publicada `langgraph-api 0.15.1` foi testada no ambiente, mas introduziu conflitos verificáveis entre Starlette/OpenTelemetry e o conjunto da aplicação.

## Alternativas

1. Usar `langgraph-api 0.15.1` imediatamente.
2. Manter o conjunto funcional, fixando CLI, API e grafo.
3. Trocar LangGraph CLI por outro servidor.

## Decisão

Fixar temporariamente `langgraph-cli 0.4.32`, `langgraph-api 0.10.3` e `langgraph 1.2.12`, preservando o caminho exigido e a reprodução que passou. A alternativa 1 não foi aceita porque `pip check` detectou conflitos; a alternativa 3 viola o escopo do desafio.

## Prós e contras

- Prós: instalação reproduzível, CLI comprovadamente funcional, sem conflito no ambiente (`pip check` limpo).
- Contras: `langgraph-api 0.10.3` está em EOL e não deve ser tratado como solução de produção.

## Evidência e condição de revisão

Python 3.14.8, CLI e API carregaram a aplicação; a tentativa com API 0.15.1 foi revertida após conflitos objetivos. Revisar quando a CLI publicar uma combinação compatível e suportada; repetir instalação limpa, `pip check`, inicialização e chamadas HTTP antes de aceitar a atualização.
