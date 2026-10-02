# ADR-003 — Uso de LLM na geração

- **Status:** aceita como estratégia de contexto; provedor substituído/concretizado pelos ADR-012 e ADR-016
- **Contexto:** a geração pode usar LLM, mas o desafio exige rastreabilidade do contexto e validação da saída.
- **Decisão:** o cliente recebe SQL original, IR, análise, riscos, schema opcional e contrato Python; a saída passa por validação estática e só recebe alegação comportamental quando houver harness executado.
- **Alternativas:** regras determinísticas; LLM direta sem estrutura intermediária.
- **Prós/contras:** contexto estruturado melhora auditabilidade, mas aumenta custo/latência; regras são reprodutíveis, porém têm cobertura inicial limitada.
- **Evidência:** Gemini real foi preservado em `results/run-18`; o adaptador atual suporta Gemini/OpenAI/OpenRouter e os três cenários B/C estão em `results/behavioral-bc.json`.
- **Condição de revisão:** decidir após medir a cobertura do parser/analisador e comparar uma saída determinística com uma saída assistida em fixtures controladas.

