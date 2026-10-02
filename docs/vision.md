# Documento de Visão

## Problema

A modernização manual de PL/pgSQL para Python pode perder tipos, efeitos,
transações, exceções e rastreabilidade.

## Visão

Oferecer um fluxo que transforme uma rotina SQL em análise estruturada, contexto
de geração, código Python e relatório verificável, sem confundir validade
sintática com equivalência comportamental.

## Usuários

- Engenheiro responsável pela modernização.
- Revisor técnico que audita decisões e evidências.
- Operador que diagnostica uma execução.
- Equipe de plataforma que compara provedores e acompanha métricas de avaliação.

## Não objetivos

Não corrigir regra de negócio automaticamente, não executar código gerado na
API e não prometer equivalência sem testes comparativos.
