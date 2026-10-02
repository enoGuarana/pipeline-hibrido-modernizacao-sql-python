# ADR-005 — Validação incremental da equivalência

- **Status:** aceito como estratégia de validação
- **Contexto:** o desafio exige validação estática mínima e apresenta B–F como casos obrigatórios; equivalência comportamental é desejada, mas os anexos têm complexidades e efeitos diferentes.
- **Alternativas:** somente validação estática; validação comportamental completa de B–F antes de qualquer entrega.
- **Decisão:** executar validação estática para B–F. Construir o oráculo comportamental começando por B e D, respectivamente uma função simples e uma procedure transacional, e expandi-lo para C, E e F conforme os efeitos forem suportados. O nível de evidência será registrado por procedure.
- **Prós/contras:** entrega cobertura inicial de todos os anexos e evidência comportamental cedo; alguns anexos podem permanecer apenas com validação estática e a equivalência geral não pode ser declarada antes da expansão.
- **Evidência:** testes estáticos cobrem B–F e `results/behavioral-bc.json` registra três cenários comportamentais B/C equivalentes. A expansão para D–F continua sem evidência comparável.
- **Condição de revisão:** revisar a ordem se B ou D revelarem que o harness não representa corretamente transações, efeitos ou erros; nunca elevar validação estática a equivalência comportamental.

