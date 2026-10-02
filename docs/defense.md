# Defesa técnica — estado atual

## Explicação em dois minutos

A API registra a execução antes do processamento e executa um grafo LangGraph com parsing, análise semântica, geração, validação e finalização. O parser preserva SQL e extrai uma IR estrutural para B–F. A geração usa Gemini API quando `GEMINI_API_KEY` existe; sem chave, usa um stub explicitamente simulado. O código não é executado pela API. Histórico, hashes e relatórios ficam em PostgreSQL JSONB.

## Cinco decisões principais

1. Monólito modular: reduz custo operacional e mantém fronteiras claras; evidência no grafo/API e ADRs.
2. Parsing híbrido: nenhum parser cobriu o corpo PL/pgSQL completo; a IR própria preserva limites.
3. SQL parametrizado e transações no PostgreSQL: reduz risco semântico de locking, tipos e efeitos.
4. Gemini API com SDK nativo, modelo/prompt configuráveis e TLS pelo armazenamento nativo: integração oficial sem credenciais em arquivos.
5. Reparo máximo de uma tentativa: impede ciclos e preserva tentativas anteriores; testes determinísticos cobrem o roteamento.

## Limitações a admitir

- `langgraph-api 0.10.3` está em EOL; `0.15.1` apresentou conflitos no conjunto verificado.
- A tentativa OpenAI terminou em `429`. O Gemini gerou código real com
  `gemini-3.8-flash` no `run_id=11`, mas o resultado falhou no Ruff e o reparo
  recebeu `503`. Após indisponibilidade recorrente, `gemini-3.5-flash-lite`
  produziu o `run_id=18`, aprovado em `ast.parse` e Ruff na primeira tentativa.
  Isso comprova integração e validade estática, não equivalência.
- Não há equivalência comportamental publicada para B–F.
- O parser não é AST completa de PL/pgSQL.
- D e F ainda têm falhas de validação estática nos artefatos mais recentes; E
  possui limitações semânticas não testadas.
- Evaluation reproduzível está disponível no endpoint, mas Langfuse e
  equivalência comportamental continuam bônus/pendências.

## Evolução para produção

1. Atualizar e validar uma combinação suportada do runtime LangGraph.
2. Corrigir as falhas estáticas D/F e implementar a dependência Python injetada
   de F conforme ADR-013.
3. Completar o harness comportamental isolado para B–F.
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
