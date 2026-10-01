# Instruções para agentes e colaboradores

## Contexto obrigatório

Antes de alterar qualquer arquivo:

1. Leia `DESAFIO_CONTEXTO.md`, se ele existir.
2. Inspecione o estado do Git, os arquivos relevantes e os ADRs existentes.
3. Se `DESAFIO_CONTEXTO.md` estiver ausente, registre a ausência e use apenas as fontes disponíveis; não invente decisões ou requisitos.

## Trabalho por etapas

- Execute somente a etapa solicitada.
- Separe requisitos obrigatórios, bônus e recomendações.
- Trate propostas do desafio e dos ADRs como propostas até que haja decisão explícita e evidência.
- Para decisões arquiteturais relevantes, crie ou atualize um ADR curto com contexto, alternativas, decisão, prós/contras, evidência e condição de revisão.
- Preserve mudanças existentes; não faça resets, exclusões ou reescritas amplas sem autorização.

## Verificação e documentação

- Antes e depois das alterações, verifique `git status` e `git diff`.
- Não declare testes, benchmarks, execução, equivalência ou cobertura sem evidência reproduzível.
- Ao usar APIs, CLIs ou configurações sujeitas a mudança, consulte a documentação oficial atual e registre a fonte quando ela influenciar uma decisão.
- Atualize `docs/requirements.md`, `docs/implementation-plan.md` e os ADRs quando o escopo, a evidência ou o status de uma decisão mudar.
- Ao concluir, informe: mudanças realizadas, verificações executadas, incertezas restantes e critério objetivo para avançar.

