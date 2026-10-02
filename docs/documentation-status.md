# Estado da documentação

Atualizado em 2026-10-02 após inspeção do código, testes locais, artefatos
`results/` e configuração do ambiente. Este índice evita que snapshots antigos
sejam confundidos com o comportamento atual.

## Fontes de verdade

| Assunto | Documento/código de referência |
|---|---|
| Requisitos e aceite | [`requirements.md`](requirements.md) |
| Plano e etapa atual | [`implementation-plan.md`](implementation-plan.md) |
| Arquitetura e contratos | [`architecture.md`](architecture.md), `src/pipeline/contracts.py`, `src/pipeline/state.py` |
| Provedores LLM | [`ADR-016`](adr/ADR-016-selecao-de-provedor-llm.md), [`integration-guide.md`](integration-guide.md) |
| Persistência/operação | [`runbook.md`](runbook.md), `src/pipeline/db.py`, `infra/` |
| Evaluation | [`evaluation.md`](evaluation.md), `scripts/evaluate_results.py` |
| Equivalência | [`ADR-014`](adr/ADR-014-evidencia-comportamental-b-c.md), `results/behavioral-bc.json` |
| Observabilidade | [`ADR-015`](adr/ADR-015-observabilidade-langfuse.md), `src/pipeline/observability.py` |
| Defesa | [`defense.md`](defense.md) |

## Estado resumido

- Fluxo API/Grafo/persistência: implementado e testado localmente.
- Parsing e análise: implementados para fixtures A–F, com limites explícitos.
- Geração: Gemini padrão; OpenAI/OpenRouter compatíveis; stub sem credencial.
- Validação: `ast.parse`, Ruff e no máximo um reparo.
- Evaluation: endpoint, script e dashboard implementados; denominador inclui
  falhas e exclui apenas `pending`.
- Equivalência: aceita somente os três cenários B/C registrados; D–F pendentes.
- Langfuse: adaptador opcional implementado; trace real do `run_id=30`
  confirmado via API v2 e captura versionada em `assets/langfuse-trace.png`.
  Custos, retenção e alertas permanecem fora da evidência disponível.

## Como interpretar snapshots antigos

`technical-validation.md`, ADRs históricos e algumas seções de `requirements.md`
preservam evidências de etapas anteriores, como o antigo `/modernize` 501, o
stub inicial e a tentativa OpenAI com `429`. Esses fatos continuam úteis como
histórico, mas não descrevem o estado atual. O status atual está nas seções
explicitamente marcadas como baseline/estado atual e nos documentos da tabela
acima.
