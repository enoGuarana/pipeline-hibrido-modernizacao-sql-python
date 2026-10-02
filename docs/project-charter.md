# Termo de Abertura

## Propósito

Construir um pipeline auditável para analisar rotinas PL/pgSQL e produzir uma
tradução Python validável, preservando decisões, tentativas e limitações.

## Escopo

- API LangGraph com `/health`, `/modernize` e `/evaluation`.
- Parsing/análise estrutural dos anexos B–F.
- Geração com Gemini como padrão e suporte a OpenAI/OpenRouter compatíveis,
  validação estática e persistência.
- Avaliação comportamental isolada, iniciada por B/C.
- Dashboard Streamlit interno para submissão, métricas e auditoria.
- Integração Langfuse opcional, condicionada a credenciais/host configurados.

Fora do escopo atual: execução automática do código gerado pela API, equivalência
geral D–F, recuperação automática de crash e operação de observabilidade em
produção.

## Critérios de sucesso

1. Execução reproduzível em Python 3.14, PostgreSQL e Compose.
2. Toda execução controlada termina com relatório e status persistidos quando o
   banco permanece disponível.
3. Nenhuma alegação de equivalência sem comparação executada.
4. Limitações e decisões rastreáveis em `docs/`.

## Situação

Projeto em desenvolvimento controlado. B/C têm três cenários comportamentais
equivalentes registrados; D–F permanecem pendentes nessa dimensão. O caminho de
geração é provider-agnostic, mas cada provedor externo ainda depende de chave,
modelo, quota e resposta compatíveis.
