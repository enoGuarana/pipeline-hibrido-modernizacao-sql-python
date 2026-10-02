# Defesa técnica — estado atual

## Explicação em dois minutos

A aplicação recebe SQL legado, cria um `run_id` e persiste o estado `pending` antes de iniciar um grafo LangGraph. O fluxo percorre parsing estrutural, análise semântica, geração, validação e finalização. A análise preserva fatos, riscos e construções desconhecidas; a geração usa um adaptador selecionável para Gemini, OpenRouter ou OpenAI, com stub explícito quando não há credencial. `ast.parse` e Ruff verificam a saída, e há no máximo uma tentativa de reparo. O código gerado não é executado pela API. Relatórios, hashes e tentativas ficam em PostgreSQL JSONB.

A distinção essencial para a defesa é: validade estática não é equivalência. Há evidência comportamental para B e C em três cenários no relatório `results/behavioral-bc.json`; D–F têm artefatos e revisão semântica, mas continuam sem equivalência publicada.

## Cinco decisões principais

1. **Monólito modular:** mantém API, grafo, parsing, análise, geração, validação e persistência separáveis sem criar distribuição prematura.
2. **Parsing híbrido:** nenhum parser candidato cobriu o corpo PL/pgSQL completo; a IR própria preserva o SQL original e marca limites.
3. **SQL parametrizado e transações no PostgreSQL:** reduz o risco de alterar tipos, locking, exceções e efeitos transacionais durante a tradução.
4. **Provedor LLM por execução:** o mesmo grafo roteia Gemini, OpenRouter ou OpenAI; a chave pode vir da requisição ou do ambiente e não entra no histórico.
5. **Reparo limitado a uma tentativa:** impede ciclos ilimitados e preserva o código/relatório da tentativa anterior para auditoria.

As decisões, alternativas, evidências e condições de revisão estão nos ADRs, especialmente [ADR-012](adr/ADR-012-integracao-gemini.md), [ADR-014](adr/ADR-014-evidencia-comportamental-b-c.md), [ADR-015](adr/ADR-015-observabilidade-langfuse.md) e [ADR-016](adr/ADR-016-selecao-de-provedor-llm.md).

## Limitações a admitir

- A combinação `langgraph-api 0.10.3` permanece uma restrição de compatibilidade registrada no ADR-010; `pip check` está limpo no ambiente verificado, mas a atualização para uma combinação suportada ainda precisa ser validada.
- Os artefatos B–F foram gerados e revisados, mas somente B/C possuem comparação comportamental registrada. D–F continuam pendentes nessa dimensão.
- O parser não é uma AST completa de PL/pgSQL; construções desconhecidas podem levar a status parcial.
- D e F têm falhas de validação estática nos artefatos mais recentes; E tem riscos semânticos não testados. Nenhuma correção de negócio foi aplicada silenciosamente.
- A integração Langfuse é opcional e o dashboard é uma ferramenta interna. Sem credenciais/configuração remota, não há trace ou screenshot remoto reivindicado.
- Evaluation calcula métricas verificáveis, mas equivalência comportamental só é contada quando há relatório explícito de execução comparável.

## Evolução para produção

1. Validar uma combinação atualizada e suportada do runtime LangGraph.
2. Corrigir ou regenerar D/F somente com decisão explícita e revisão semântica; implementar a dependência Python de F conforme o ADR-013.
3. Expandir o harness comportamental para D–F com banco isolado, cenários aprovados e normalização explícita de valores variáveis.
4. Obter traces Langfuse reais, proteger o dashboard e definir retenção/alertas.
5. Implementar recuperação de crash, rotação de segredos, limites de concorrência e testes de carga antes de produção.

## Perguntas prováveis

1. **Lint prova equivalência?** Não. Prova apenas validade sintática e as regras estáticas adotadas.
2. **O stub é LLM?** Não. É um modo simulado identificado nos relatórios.
3. **O parser cobre todo PL/pgSQL?** Não. Ele extrai a estrutura suportada e registra construções desconhecidas.
4. **Por que não reescrever tudo em Python?** Para preservar queries, tipos, locking, exceções e transações do PostgreSQL quando isso for necessário.
5. **Por que uma tentativa de reparo?** Para limitar custo e ciclos, sem apagar evidência da saída anterior.
6. **Como trocar o provedor?** Informando `provider` e opcionalmente `model_name`/`api_key`; a topologia do grafo permanece igual.
7. **Onde ficam os segredos?** No ambiente ou apenas em memória durante a requisição; não são persistidos nem incluídos nos logs.
8. **O código gerado é executado na API?** Não. A execução comportamental usa harness isolado e controlado.
9. **O que acontece se o banco cair?** A API declara a falha e não afirma que a finalização foi persistida; não há recuperação de crash alegada.
10. **O que falta para equivalência completa?** Executar original e Python em estado inicial igual para D–F, comparar retorno, efeitos e erros e registrar divergências sem corrigi-las silenciosamente.
