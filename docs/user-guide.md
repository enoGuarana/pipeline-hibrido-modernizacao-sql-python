# Guia de Usuário

## Pré-requisitos

Python 3.14, Docker e PostgreSQL isolado. Para geração real, uma chave do
provedor escolhido no ambiente; sem ela, use o modo simulado explicitamente
identificado. Gemini é o padrão; OpenAI e OpenRouter também são aceitos.

## Uso básico

1. Suba PostgreSQL e servidor conforme o README.
2. Envie `source_code` e, se necessário, `schema`, `provider` e `model_name`
   para `/modernize`. `api_key` pode ser informada apenas para a execução.
3. Guarde o `run_id`, código e relatório.
4. Revise parsing, riscos, validação e limitações antes de usar qualquer saída.

Para operação Human-in-the-loop, instale o extra `dashboard` e execute
`streamlit run dashboard.py`. A tela possui submissão, métricas e auditoria;
ela não substitui a revisão técnica do SQL/Python.

## Interpretação

`success` significa que as validações da etapa passaram. Não significa que o
código preserva comportamento. `failure` exige análise do relatório; `partial`
indica cobertura incompleta.
