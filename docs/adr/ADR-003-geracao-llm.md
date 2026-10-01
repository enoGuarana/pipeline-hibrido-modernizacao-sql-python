# ADR-003 — Uso de LLM na geração

- **Status:** proposta, não aceita
- **Contexto:** a geração pode usar LLM, mas o desafio exige rastreabilidade do contexto e validação da saída.
- **Decisão proposta:** se LLM for adotada, receberá estrutura semântica, riscos e schema, nunca somente SQL bruto; a saída passará por validação estática e comportamental.
- **Alternativas:** regras determinísticas; LLM direta sem estrutura intermediária.
- **Prós/contras:** contexto estruturado melhora auditabilidade, mas aumenta custo/latência; regras são reprodutíveis, porém têm cobertura inicial limitada.
- **Evidência:** nenhum provedor, prompt ou chamada foi implementado; nenhuma comparação foi executada.
- **Condição de revisão:** decidir após medir a cobertura do parser/analisador e comparar uma saída determinística com uma saída assistida em fixtures controladas.

