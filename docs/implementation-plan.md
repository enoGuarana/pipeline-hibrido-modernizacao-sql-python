# Plano de implementação e estado atual

> Atualizado em 2026-10-02. Esta página é o plano operacional vigente; números
> e resultados históricos detalhados continuam nos artefatos de `results/` e em
> `docs/evaluation.md`.

## Princípios

- Entregar uma fatia verificável por vez.
- Separar requisito, decisão, evidência e limitação.
- Não declarar equivalência sem comparação comportamental contra uma referência executável.
- Consultar documentação oficial para integrações sujeitas a mudança.
- Preservar alterações existentes e não corrigir comportamento do legado silenciosamente.

## Estado por etapa

| Etapa | Estado | Evidência principal | Pendente/limite |
|---|---|---|---|
| 1. Regras e plano | Concluída | `AGENTS.md`, matriz, ADRs e este plano | Revisar quando o escopo mudar |
| 2. Viabilidade | Concluída com limites | `docs/technical-validation.md`, `pip check`, CLI e testes locais | Compatibilidade futura do runtime LangGraph |
| 3. Arquitetura e contratos | Concluída | `docs/architecture.md`, `contracts.py`, `state.py` | IR não é AST completa de PL/pgSQL |
| 4. Infraestrutura/persistência | Concluída | Docker Compose, DDL, `/health`, histórico JSONB | Recuperação automática de crash não implementada |
| 5. Primeiro fluxo | Concluída | quatro nós, finalização, reparo limitado e testes | Stub só é modo simulado |
| 6. Parsing/análise B–F | Concluída parcialmente | fixtures A–F, tags `$$`/`$BODY$`, testes e revisão de cobertura | Construções desconhecidas e limites documentados |
| 7. Geração real/provedores | Concluída parcialmente | Gemini real; adaptador Gemini/OpenAI/OpenRouter; ADR-016 | chamadas externas dependem de credenciais/quota |
| 8. Validação/reparo | Concluída | AST, Ruff, no máximo um reparo, preservação de tentativas | Não executa código gerado |
| 9. Revisão semântica C–F | Parcial | artefatos e `results/semantic-review.md`; B/C comportamental | D–F sem equivalência comportamental |
| 10. Evaluation/documentação | Concluída parcialmente | `/evaluation`, script, dashboard, README e trace Langfuse real do `run_id=30` | Métrica comportamental só B/C; custos/retenção/alertas não demonstrados |
| 11. Revisão arquitetural | Concluída | ADRs, limitações e defesa atualizados | Nova revisão deve ser sem alterações antes de corrigir |
| 12. Defesa/prontidão | Parcial | `docs/defense.md` e requisitos atualizados | Resolver pendências D–F e operação de produção |

## Dependências e sequência de execução

1. Subir PostgreSQL isolado e validar `DATABASE_URL`.
2. Instalar dependências base e extras somente quando necessários (`dashboard`,
   `observability`).
3. Iniciar o runtime pelo LangGraph CLI e confirmar `/health`.
4. Executar `/modernize` com `provider` explícito ou configuração do ambiente.
5. Conferir o histórico JSONB, os relatórios e os artefatos exportados.
6. Rodar testes, Ruff e `pip check` antes de aceitar a mudança.
7. Para equivalência, executar o harness em banco isolado com estado inicial
   controlado; não inferir equivalência a partir de AST/lint.

## Decisões vigentes

- O grafo continua um monólito modular; não há tecnologia adicional sem requisito.
- O provedor é selecionado no início da execução e não altera a topologia do grafo.
- A chave pode vir da requisição ou do ambiente, mas não é persistida.
- O reparo é limitado a uma tentativa.
- Langfuse e Streamlit são camadas opcionais de operação/auditoria.
- A saída deve preservar consultas, transações, locking, exceções e tipos do
  legado quando aplicáveis; achados de possível bug ficam separados da tradução.

Detalhes e condições de revisão estão em `docs/adr/`.

## Riscos de entrega ainda abertos

1. **Semântica D–F:** locking, rollback/auditoria, arredondamento/N+1 e
   dependência recursiva precisam de cenários comparáveis.
2. **Runtime:** a combinação atual do pacote `langgraph-api` tem limitação de
   suporte registrada no ADR-010.
3. **Provedores externos:** quota, modelo, timeout e formato de resposta variam;
   testes locais usam mocks e não substituem verificação real.
4. **Operação:** não há recuperação de crash entre `pending` e finalização,
   nem promessa de execução segura de código gerado.

## Critério para avançar

Uma etapa só deve ser marcada como concluída quando houver decisão registrada,
comando reproduzível, evidência armazenada e limitações explícitas. A etapa de
equivalência para D–F avança apenas após comparação em banco isolado; qualquer
divergência deve ser registrada antes de uma eventual correção de negócio.
