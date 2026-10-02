# Model cards — provedores de LLM

Este arquivo mantém o nome histórico do modelo Gemini, mas documenta a fronteira
atual de provedores. A seleção ocorre por execução; não existe alegação de que
modelos diferentes produzem saídas equivalentes.

## Gemini (padrão)

- Cliente: SDK `google-genai`.
- Configuração: `GEMINI_API_KEY`, `GEMINI_MODEL` ou os campos correspondentes da
  requisição.
- Prompt versionado: `modernize_v4` nos artefatos C–F mais recentes.
- Evidência: geração real de B em `results/run-18`, com aprovação em AST e Ruff.
- Limite: quota, disponibilidade do catálogo e comportamento do modelo variam;
  a saída não é executada pela API.

## OpenAI-compatible

- Cliente: SDK oficial `openai`.
- OpenAI: `OPENAI_API_KEY` e `OPENAI_MODEL`.
- OpenRouter: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` e base URL
  `https://openrouter.ai/api/v1`.
- A interface normaliza o texto retornado para `generated_code` e registra
  somente metadados seguros.
- Evidência local: testes determinísticos validam roteamento e tratamento de
  resposta; a tentativa histórica OpenAI terminou em `429 insufficient_quota`.
- Limite: não há neste checkout uma chamada remota OpenRouter aprovada; não
  inventar modelo, custo ou tokens quando o provedor não os fornecer.

## Controles comuns

- Chaves podem ser fornecidas pela requisição ou pelo ambiente, mas não são
  persistidas no histórico nem incluídas no prompt de auditoria.
- Timeout, resposta vazia, erro de autenticação e resposta fora do contrato
  encerram a execução como falha controlada.
- Uma saída sintaticamente válida ainda precisa de revisão semântica; AST/Ruff
  não comprovam equivalência.
