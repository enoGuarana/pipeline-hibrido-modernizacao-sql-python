# Defesa técnica — estado atual

## Explicação em dois minutos

A API registra a execução antes do processamento e executa um grafo LangGraph com parsing, análise semântica, geração, validação e finalização. O parser preserva SQL e extrai uma IR estrutural para B–F. A geração usa OpenAI Responses API quando `OPENAI_API_KEY` existe; sem chave, usa um stub explicitamente simulado. O código não é executado pela API. Histórico, hashes e relatórios ficam em PostgreSQL JSONB.

## Cinco decisões principais

1. Monólito modular: reduz custo operacional e mantém fronteiras claras; evidência no grafo/API e ADRs.
2. Parsing híbrido: nenhum parser cobriu o corpo PL/pgSQL completo; a IR própria preserva limites.
3. SQL parametrizado e transações no PostgreSQL: reduz risco semântico de locking, tipos e efeitos.
4. OpenAI Responses API com modelo/prompt configuráveis: integração oficial, sem credenciais em arquivos; chamada real ainda depende de chave.
5. Reparo máximo de uma tentativa: impede ciclos e preserva tentativas anteriores; testes determinísticos cobrem o roteamento.

## Limitações a admitir

- `langgraph-api 0.10.3` está em EOL; `0.15.1` apresentou conflitos no conjunto verificado.
- A geração real OpenAI não foi executada sem `OPENAI_API_KEY`.
- Não há equivalência comportamental publicada para B–F.
- O parser não é AST completa de PL/pgSQL.
- Evaluation e observabilidade externa ainda são bônus futuros.

## Evolução para produção

1. Atualizar e validar uma combinação suportada do runtime LangGraph.
2. Executar geração real e registrar uso/custos disponíveis.
3. Criar harness comportamental isolado para B–F.
4. Implementar evaluation e observabilidade com evidência real.
5. Tratar recuperação de crashes e operação segura de credenciais.

## Perguntas prováveis

1. **Lint prova equivalência?** Não; prova apenas validade estática.
2. **O stub é LLM?** Não; é marcado como simulado.
3. **O parser cobre todo PL/pgSQL?** Não; classifica construções e preserva desconhecidas.
4. **Por que não reescrever tudo em Python?** Para preservar tipos, locking e semântica do PostgreSQL.
5. **Por que uma tentativa de reparo?** Para limitar custo e ciclos.
6. **Onde ficam os segredos?** Apenas no ambiente; não são persistidos.
7. **O código gerado é executado na API?** Não.
8. **Como uma execução é rastreada?** `run_id`, hashes, prompt, modelo, tentativas e relatórios.
9. **O que acontece se o banco cair?** A API declara indisponibilidade; não alega persistência confirmada.
10. **O que ainda falta para equivalência?** Executar rotina original e Python em banco isolado, com mesmo estado e comparação de efeitos.
