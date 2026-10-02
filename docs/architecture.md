# Arquitetura mínima e contratos

## Escopo

Esta arquitetura descreve o núcleo mínimo para o desafio. Ela não aprova automaticamente as propostas do contexto e não implementa a tradução completa. A estratégia de parsing continua proposta no [ADR-007](adr/ADR-007-estrategia-de-parsing.md).

## Fluxo

```mermaid
flowchart LR
    HTTP[POST /modernize] --> P[Persistir pending]
    P --> G[LangGraph]
    G --> N1[parsing]
    N1 --> N2[análise semântica]
    N2 --> N3[geração]
    N3 --> N4[validação]
    N4 --> F[finalizar histórico]
    F --> R[resposta]
    N1 -. erro .-> F
    N2 -. erro .-> F
    N3 -. erro .-> F
    N4 -. erro .-> F
    DB[(PostgreSQL modernization_history)] --- P
    DB --- F
    LLM[cliente LLM substituível] --- N3
    SQL[PostgreSQL legado/teste] --- N1
    SQL --- N2
```

## Diagrama de componentes e fronteiras

```mermaid
flowchart TB
    Client[Cliente HTTP] --> API[pipeline.api]
    API --> History[(PostgreSQL<br/>modernization_history)]
    API --> Graph[pipeline.graph]
    Graph --> Parse[pipeline.parsing]
    Parse --> IR[IR tipada]
    IR --> Analysis[Análise semântica]
    Analysis --> Prompt[Contexto versionado]
    Prompt --> Provider[Cliente Gemini]
    Provider --> Validation[ast.parse + Ruff]
    Validation --> History
    Graph --> Evaluation[pipeline.evaluation]
    Evaluation --> History
    Isolated[Harness comportamental isolado] -.não executado pela API.-> Evaluation
```

As setas pontilhadas representam uma fronteira de avaliação, não um caminho
de produção. O comparador só deve receber observações capturadas em ambiente
isolado e nunca inferir equivalência a partir da validação estática.

## Componentes e responsabilidades

| Componente | Responsabilidade | Não é responsável por |
|---|---|---|
| `pipeline.api` | Validar entrada, obter pool, iniciar/finalizar histórico e responder HTTP | Implementar parsing ou executar código gerado |
| `pipeline.graph` | Registrar os quatro nós e as transições do LangGraph | Decidir sozinho a equivalência |
| `pipeline.contracts` | Tipos de entrada, IR, relatórios, erros e resposta | Persistir ou chamar provedores |
| `pipeline.state` | Estado compartilhado do grafo | Ser banco de histórico |
| `pipeline.db` | Criar pool, schema mínimo e atualizar histórico | Controlar semântica da rotina legada |
| nó de parsing | Produzir estrutura de origem e IR; marcar desconhecidos | Inferir correção de negócio |
| nó de análise | Produzir fatos, riscos e decisões rastreáveis | Corrigir o SQL legado |
| nó de geração | Produzir código conforme contexto e contrato | Validar comportamento por execução |
| nó de validação | Executar `ast.parse`, lint e checks de contrato | Declarar equivalência comportamental |

## Contratos tipados

Os tipos estão em `src/pipeline/contracts.py` e o estado em `src/pipeline/state.py`.

### Entrada

```json
{
  "source_code": "SELECT 1;",
  "schema": null
}
```

`source_code` é obrigatório e não vazio. `schema` é opcional e não deve ser tratado como instância automática do banco.

### Representação intermediária

A IR deve preservar, quando disponível: nome/tipo da rotina, linguagem, parâmetros e modos, retorno, variáveis, operações, tabelas, chamadas, trechos de origem e construções não suportadas. Fato extraído e inferência devem ser campos ou achados distinguíveis no relatório; a IR não pode ocultar ausência de extração.

### Relatório por etapa

Cada entrada de `stage_reports` contém estágio, status, achados, decisões, avisos, erros e duração somente quando medida. Duração, tokens, custo e versão de modelo não podem ser preenchidos com estimativas.

### Erros e estados

- `pending`: registro criado, mas a pipeline ainda não terminou ou a fatia atual deliberadamente não implementa a etapa.
- `success`: todas as validações exigidas para a etapa passaram; não significa equivalência comportamental.
- `failure`: a execução terminou com erro impeditivo e o relatório foi finalizado.
- `partial`: houve saída utilizável, mas uma etapa ou validação ficou incompleta/limitada.

`ExecutionError` deve informar código, mensagem, estágio, possibilidade de recuperação e detalhes seguros. Segredos e SQL desnecessariamente duplicado não devem entrar em logs.

## Transações e finalização

1. A API cria o registro `pending` antes de iniciar nós.
2. Cada operação de persistência confirma sua própria transação.
3. O grafo não deve depender apenas do caminho de sucesso para finalizar o histórico.
4. Falha controlada deve tentar atualizar `failure` ou `partial`; se o banco cair durante essa atualização, a resposta deve declarar que a persistência não foi confirmada.
5. Interrupção de processo entre criação e finalização permanece uma lacuna conhecida; não há recuperação de crash nesta etapa.

## Tentativas e ciclos

`generation_attempts` conta tentativas de geração. O fluxo pode permitir no máximo uma tentativa de reparo após uma validação objetiva; sem uma política explicitamente implementada, o fluxo deve finalizar em vez de repetir. Não há loop ilimitado implícito no grafo.

## Troca de modelo e dialeto

O cliente LLM deve ser uma fronteira pequena, recebendo contexto estruturado e devolvendo texto/metadata conforme contrato. Um novo modelo não deve mudar o estado do grafo. Um novo dialeto deve fornecer parser/normalizador separado e declarar capacidades; não se cria uma abstração genérica antes de existir um segundo dialeto.

## Exemplos de contrato

### Sucesso estático

```json
{
  "run_id": 10,
  "status": "success",
  "generated_code": "def saldo_cliente(...): ...",
  "report": {"validation": {"ast_parse": "passed", "lint": "passed"}}
}
```

Isso demonstra somente validação estática; não prova equivalência.

### Falha de parsing

```json
{
  "run_id": 11,
  "status": "failure",
  "report": {"errors": [{"code": "PARSE_UNSUPPORTED", "stage": "parsing"}]}
}
```

### Falha de validação

```json
{
  "run_id": 12,
  "status": "failure",
  "report": {
    "validation": {"ast_parse": "failed"},
    "generation_attempts": 1
  }
}
```

Os exemplos são contratos ilustrativos, não resultados de testes executados.

## Lacunas antes da implementação do fluxo completo

- A IR ainda não é produzida por um nó real.
- Não há testes automatizados nem fixtures versionadas B–F.
- O relatório de cada nó ainda não é propagado pelo grafo.
- O reparo limitado ainda não foi implementado.
- A persistência de `success`, `failure` e `partial` ainda não foi verificada.

## Decisões arquiteturais e validações pertinentes

Esta seção consolida decisões confirmadas durante a validação do projeto:

| Decisão | Evidência/validação | Limite e condição de revisão |
|---|---|---|
| Usar Python 3.14 com LangGraph CLI atualizado e versionado | A CLI carregou a aplicação customizada; as versões devem ser verificadas novamente após a atualização | Revisar se a documentação oficial ou a instalação limpa indicar incompatibilidade |
| Manter PostgreSQL isolado em Docker Compose | O container isolado respondeu e persistiu `modernization_history` | Não usar bancos existentes; revisar para ambiente de produção |
| Usar parsing híbrido e IR própria | Os experimentos mostraram que nenhum parser candidato cobre sozinho PL/pgSQL completo | Marcar construções desconhecidas e revisar quando a cobertura B–F for medida |
| Preservar queries, tipos, locking e transações no PostgreSQL quando necessário | Decisão alinhada aos riscos de semântica dos anexos e ao contrato de conexão assíncrona | Revisar somente com evidência comportamental comparável |
| Manter o cliente LLM pequeno e o modelo configurável | Permite registrar modelo/prompt e trocar provedor sem alterar o grafo | Não criar abstrações adicionais antes de uma necessidade comprovada |
| Permitir no máximo um reparo | Evita ciclos ilimitados e preserva tentativas anteriores | Revisar apenas com métricas de custo e taxa de correção |

### Regra de fidelidade ao legado

Uma tradução não pode corrigir silenciosamente uma regra, validação, ordem, arredondamento, exceção, efeito transacional ou outro comportamento do legado. Todo comportamento aparentemente incorreto deve ser classificado separadamente como **achado do legado**, com trecho de origem e evidência disponível. Uma correção só pode entrar no código gerado quando houver decisão explícita registrada, justificativa e validação própria.

As validações devem distinguir: fato extraído do SQL, inferência da análise, comportamento observado em banco, comportamento ainda não testado e divergência identificada. `ast.parse`, lint e ausência de erro não autorizam alegação de equivalência.
