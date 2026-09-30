# Matriz de requisitos

Fonte: `Desafio_Tecnico_Inovacao_v2_candidatos 4.pdf`.

| ID | Requisito | Tipo | Implementação nesta fatia | Evidência/pendência |
|---|---|---|---|---|
| R1 | Servidor local com LangGraph CLI | Obrigatório | Parcial: `langgraph.json` e app FastAPI | CLI/dependências precisam ser instaladas e executadas |
| R2 | `POST /modernize` com código e relatório | Obrigatório | Rota criada, responde `501 pending` | Pipeline e persistência por execução pendentes |
| R3 | `GET /health` com status | Obrigatório | Implementado com `SELECT 1` no pool | Requer PostgreSQL disponível |
| R4 | Quatro nós: parsing, semântica, geração, validação | Obrigatório | Contratos tipados e grafo linear criados | Corpos funcionais pendentes |
| R5 | Estado tipado | Obrigatório | `PipelineState(TypedDict)` | Campos precisarão ser refinados com a implementação |
| R6 | PostgreSQL e `modernization_history` | Obrigatório | Pool assíncrono e DDL idempotente | Migrações/uso em cada execução pendentes |
| R7 | Modularização API/grafo/nós/persistência | Obrigatório | Estrutura inicial separada | Integrações externas ainda não existem |
| R8 | Escalabilidade futura | Obrigatório | Pool configurável e grafo desacoplado | Filas, cache e paralelização pendentes |
| R9 | README, execução, diagrama, decisões e limitações | Obrigatório | Este documento + ADRs; README pendente | Consolidar após próxima fatia |
| R10 | Procedures B–F como casos de teste | Obrigatório | Apenas identificadas na análise do desafio | Fixtures, resultados e testes pendentes |
| B1 | Langfuse/LangSmith com traces/spans | Bônus | Não implementado | Requer integração e evidência visual |
| B2 | QA: checks estáticos e pytest | Bônus | Configuração inicial | Testes e execução pendentes |
| B3 | Métrica automática de evaluation | Bônus | Não implementado | Definir métrica, persistência e endpoint/notebook |

## Escopo explicitamente não comprovado

Não há equivalência comportamental nesta etapa. O endpoint não chama o grafo nem produz Python; portanto não se pode afirmar tradução, validação, persistência da execução ou cobertura dos anexos B–F.

