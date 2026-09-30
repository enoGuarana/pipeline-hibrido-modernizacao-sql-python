# Contexto do desafio: modernização PL/pgSQL → Python

Fonte: `Desafio_Tecnico_Inovacao_v2_candidatos 4.pdf`. Este arquivo consolida o enunciado, as entradas originais e a proposta inicial de implementação. Requisitos do PDF e recomendações estão separados. O projeto ainda não foi implementado; propostas não representam decisões já testadas.

## 1. Objetivo e limites

Construir um pipeline híbrido (LLM + regras determinísticas) que recebe uma rotina PL/pgSQL e, opcionalmente, o schema das tabelas, produz um módulo Python 3.14 equivalente e retorna um relatório estruturado das etapas, decisões e validações.

- Prazo: até **2 dias corridos a partir do recebimento**; o momento do recebimento deve ser confirmado pelo candidato.
- Bibliotecas externas e assistentes de IA são permitidos; justificar bibliotecas no README e dominar as decisões para a defesa.
- Foco: desenho da pipeline e decisões de tradução; cobertura completa de PL/pgSQL não é exigida.
- Os anexos B–F são os cinco casos de teste obrigatórios. Não basta demonstrar B.
- O schema A é contexto opcional da geração; sua instanciação não é necessária para o pipeline básico. É útil para avaliação comportamental.
- A vaga menciona Java, Angular, Kubernetes, IaC, Object Storage, IA e modernização de legado. Essas tecnologias adicionais não são requisitos deste desafio. Não ampliar o escopo só por constarem na vaga.

## 2. Requisitos obrigatórios do PDF

| ID | Requisito | Evidência esperada |
|---|---|---|
| R01 | Backend local iniciado com **LangGraph CLI** | Configuração e comando reproduzível; uma API independente não basta |
| R02 | `POST /modernize`: receber SQL e schema opcional; retornar Python 3.14 e relatório | Exemplo de requisição/resposta e teste de integração |
| R03 | `GET /health`: retornar status do pipeline | Endpoint funcional |
| R04 | Orquestração com LangGraph, quatro etapas como nós e estado tipado | Grafo, contratos e diagrama no README |
| R05 | Parsing: AST, tokens classificados ou estrutura intermediária equivalente | Saída estruturada; justificar parser escolhido |
| R06 | Análise semântica: parâmetros IN/OUT, variáveis, cursores, transações, exceções, CTEs e chamadas a funções | Extrações e riscos no relatório |
| R07 | Marcar riscos como cursor, RAISE, FOR UPDATE, JSONB e recursão | Regras explícitas e testes |
| R08 | Geração de Python equivalente; se usar LLM, contexto baseado nas etapas anteriores | Prompt/contexto rastreável; SQL bruto sozinho não atende |
| R09 | Justificar SQL preservado no SGBD versus lógica reescrita em Python | Decisão e trade-offs documentados |
| R10 | Validar Python gerado com `ast.parse` e linting | Resultado das duas verificações, inclusive falhas |
| R11 | PostgreSQL com tabela `modernization_history` | Script de criação e integração funcional |
| R12 | Persistir toda execução, independentemente do desfecho | Casos de sucesso, falha e parcial |
| R13 | Separar API, grafo, nós, persistência e integrações | Organização modular compreensível |
| R14 | Arquitetura capaz de evoluir para volume, novos dialetos e modelos | Interfaces enxutas e propostas de evolução justificadas |
| R15 | Entregar código e relatórios das execuções de B–F | Resultados reais, associados às entradas |
| R16 | Docker Compose ou equivalente para servidor e PostgreSQL | Inicialização reproduzível |
| R17 | README com fluxo, execução, testes, diagrama, decisões, trade-offs, limitações e evolução | Outra pessoa consegue reproduzir |

O PDF sugere `sqlglot`, `pglast` ou `sqlparse`, mas não obriga uma biblioteca específica. LLM na geração é permitida e bem-vinda; a proposta deste projeto é utilizá-la.

### Persistência mínima

| Campo | Conteúdo exigido | Tipo sugerido, não imposto pelo PDF |
|---|---|---|
| `id` | Identificador único | UUID |
| `source_code` | SQL recebido | TEXT |
| `generated_code` | Python produzido | TEXT, nullable em falhas anteriores à geração |
| `report` | Relatório das etapas | JSONB |
| `status` | Sucesso, falha ou parcial | TEXT com valores controlados |
| `created_at` | Timestamp da execução | TIMESTAMPTZ |

## 3. Bônus e avaliação

| Bônus | Exigência para reivindicar o bônus |
|---|---|
| Observabilidade | Langfuse preferencialmente, ou LangSmith; traces por execução, spans por nó, custo e latência das chamadas LLM; screenshot real no README; documentar hospedagem |
| QA | Checks de qualidade estática e cobertura de testes com pytest |
| Evaluation | Ao menos uma métrica automática; resultados em scores no Langfuse ou tabela própria; endpoint ou notebook demonstrando B–F; explicar o que mede, limitações e evolução |

Métricas permitidas: aprovação em `ast.parse`, execuções sem erro, similaridade estrutural, equivalência comportamental ou LLM-as-judge com critérios objetivos. Validação estática não comprova equivalência. Testes comportamentais são evolução desejada, não o mínimo obrigatório.

| Critério | Peso transcrito |
|---|---:|
| Funcionamento geral | 30% |
| Código e estrutura | 20% |
| Arquitetura do pipeline | 15% |
| Banco de dados | 10% |
| Escalabilidade | 10% |
| Documentação | 10% |
| Bônus | Até +15 pontos percentuais |

**Inconsistências do documento:** os pesos obrigatórios listados somam 95%, embora a observação diga 100%; o item de entrega pede repositório público, mas as instruções gerais permitem repositório privado com acesso ou ZIP; a numeração repete “Bônus 3”. Não corrigir esses pontos silenciosamente. Adotar repositório público para cumprir a interpretação mais restritiva, salvo orientação do avaliador, sem publicar credenciais.

Após a entrega: revisão técnica de aproximadamente 45 minutos, com apresentação, walkthrough, decisões, trade-offs e evolução para produção.

## 4. Proposta arquitetural inicial — recomendações, não exigências

**Monólito modular**, com API integrada ao servidor LangGraph, PostgreSQL e cliente LLM substituível. Parsing/análise/validação predominantemente determinísticos; geração com LLM. Cada etapa é um nó; não há necessidade de quatro agentes autônomos.

Fluxo: registrar execução → parsing → análise → geração → validação → finalizar histórico → responder. Em falha de validação, permitir **uma tentativa de reparo** com feedback; depois encerrar. Erros dos nós devem convergir para finalização com relatório. A política de estados intermediários deve ser documentada.

- Verificar primeiro a montagem das rotas personalizadas pelo `langgraph.json` e a inicialização via CLI; não assumir que FastAPI isolado atende ao enunciado.
- Criar registro antes do processamento e atualizá-lo ao final; persistência não deve depender exclusivamente do caminho de sucesso do grafo.
- Se o banco estiver indisponível, retornar erro explícito; não alegar que a execução foi persistida. Recuperação após queda de processo é evolução futura.
- Preservar queries relacionais parametrizadas no PostgreSQL e mover o controle de fluxo para Python quando justificável. Apenas chamar a rotina original não demonstra a modernização proposta.
- Não executar código gerado dentro do servidor. Comparação comportamental, se implementada, deve ocorrer em ambiente de testes isolado.
- Fixar versões compatíveis com Python 3.14 e verificar instalação real; registrar limitações de dependências.
- Geração simulada é permitida na construção e em testes unitários; não apresentá-la como execução real da LLM.

### Contratos sugeridos

- Entrada: `source_code: str`, `schema: str | None`.
- Estado tipado: `run_id`, entrada, estrutura extraída/IR, análise, riscos, contexto, código gerado, validação, tentativas, erros, relatório e status.
- IR enxuta: nome/tipo da rotina, parâmetros/modos/tipos, retorno, variáveis, operações, tabelas, dependências, trechos de origem e construções não suportadas.
- Resposta: `run_id`, `status`, `generated_code` e `report`.
- Relatório por etapa: status, achados, decisões, avisos, erros e duração. Na geração, incluir modelo e versão do prompt; tokens/custo quando disponíveis. Não inventar medições.
- Definir explicitamente o significado de sucesso/falha/parcial. Sucesso estático não significa equivalência comprovada.

### Decisões a registrar em ADRs

| Decisão proposta | Benefício | Custo/risco |
|---|---|---|
| Monólito modular | Menor esforço operacional e execução simples | Escala inicialmente como aplicação única |
| Regras + LLM | Estrutura verificável e geração flexível | Cobertura das regras e variabilidade do modelo |
| SQL parametrizado preservado | Mantém recursos relacionais, locking e tipos do banco | Dependência do PostgreSQL |
| IR própria mínima | Contexto testável e extensibilidade | Risco de perda de informação |
| Reparo limitado | Recupera falhas simples com custo controlado | Não garante correção semântica |
| Validação estática + eval incremental | Entrega verificável no prazo | Limita conclusões sobre equivalência |

Cada ADR deve conter: contexto, alternativas, decisão, justificativa particular, prós/contras, evidência e condição de revisão. Não fabricar alternativas testadas nem registrar uma proposta como decisão validada.

### Organização sugerida

- `src/modernizer/`: `api.py`, `graph.py`, `state.py`, `contracts.py`, `nodes/`, `parsing/`, `analysis/`, `llm/`, `validation/`, `persistence/`.
- `tests/`: testes de extração, riscos, roteamento, validação, persistência e integração; avaliação comportamental se viável.
- `fixtures/`: schema A e rotinas B–F, copiados dos blocos SQL deste documento.
- `results/`: Python e JSON das execuções reais; métricas identificadas por execução.
- `docs/`: requisitos, arquitetura, ADRs, avaliação e limitações.
- Raiz: `README.md`, `AGENTS.md`, `DESAFIO_CONTEXTO.md`, `pyproject.toml`, lock de dependências, `langgraph.json`, `Dockerfile`, `docker-compose.yml`, `.env.example` e scripts de banco.

## 5. Resumo dos casos obrigatórios e cuidados semânticos

| Anexo | Rotina | Comportamento e decisões relevantes |
|---|---|---|
| B | `fn_saldo_cliente` | Soma saldo das contas ATIVAS de um cliente; COALESCE retorna zero; resultado numérico |
| C | `sp_atualizar_status_contas_inativas` | Valida dias positivos; inativa contas sem movimentação recente; retorna ROW_COUNT por OUT; audita; decidir representação da saída |
| D | `sp_transferir_entre_contas` | Valida valor, contas e saldo; locks FOR UPDATE; débito/crédito e inserts; EXCEPTION audita e relança; preservar atomicidade e analisar rollback |
| E | `sp_processar_lote_taxas` | Cursor de transações da data; busca taxa vigente mais recente; tarifa mínima/percentual e CASE; altera saldo, cria TARIFA e logs; discutir N+1 versus lote |
| F | `sp_relatorio_mensal_cliente` | Retorna tabela mensal por CTE recursiva; chama B; logs NOTICE/WARNING; captura erros e retorna fallback; definir dependência e representação de múltiplas linhas |

**Cuidados para não alterar silenciosamente o original:**

- Dinheiro: NUMERIC/Decimal, precisão, escala e arredondamento nas atribuições; não usar float indiscriminadamente.
- NULL e lógica SQL de três valores não equivalem automaticamente às condições Python.
- D possui atomicidade e EXCEPTION, mas não contém comandos explícitos COMMIT/ROLLBACK. Definir quem controla a transação e savepoints. O insert de auditoria seguido de RAISE não garante log durável após rollback.
- D não valida explicitamente a ausência da conta destino; não acrescentar correções de regra de negócio como se fossem tradução equivalente. Registrar achados separados.
- E arredonda valores em variáveis NUMERIC(18,2); processamento em lote precisa respeitar essas etapas. Tarifa zero pode violar o CHECK de transações. Há riscos de ordem, concorrência e repetição do lote; não alegar idempotência.
- F usa saldo atual somado a créditos menos débitos do mês; não substituir por um saldo histórico acumulado “mais correto”. A validação de período está dentro do bloco com EXCEPTION e pode terminar em fallback.
- Código sintaticamente válido, lint aprovado e ausência de erro não provam equivalência. Não confiar em LLM-as-judge como única evidência.
- Parser de SQL pode não interpretar o corpo PL/pgSQL. Verificar com B–F; não chamar extração incompleta de AST completa. Marcar construções desconhecidas.

## 6. Sequência de implementação e aceite final

1. Criar matriz de requisitos e ADRs iniciais; extrair fixtures dos SQLs abaixo.
2. Subir Python 3.14, servidor LangGraph CLI, `/health` e PostgreSQL.
3. Definir contratos, estado, IR, relatório e schema do histórico.
4. Fechar B ponta a ponta com geração simulada para desenvolvimento, incluindo falha persistida.
5. Implementar parsing/análise e verificar achados nos cinco anexos.
6. Integrar LLM real com contexto derivado das etapas anteriores.
7. Implementar ast.parse, lint, reparo limitado e finalização em erros.
8. Executar B–F; guardar códigos e relatórios reais; documentar limitações.
9. Implementar QA/evaluation; observabilidade somente após o núcleo funcional.
10. Reproduzir em checkout limpo e ensaiar defesa técnica.

Checklist de entrega:

- [ ] Servidor inicia pelo caminho documentado com LangGraph CLI.
- [ ] `/health` e `/modernize` funcionam.
- [ ] Quatro nós e estado tipado presentes; contexto da geração usa parsing/análise.
- [ ] ast.parse e lint verificam o Python gerado no runtime alvo.
- [ ] Histórico registra sucesso, falha e parcial com JSONB.
- [ ] B–F possuem resultados reais e limitações identificadas.
- [ ] Docker Compose ou equivalente e scripts de banco funcionam.
- [ ] README contém comandos, variáveis, diagrama, bibliotecas justificadas, decisões, trade-offs e limites.
- [ ] Evals/bônus reivindicados têm evidência; nenhum resultado simulado é apresentado como real.
- [ ] Repositório não contém segredos; candidato consegue explicar as decisões.

## 7. Orientações para o assistente de programação

Leia este arquivo antes de implementar. Use os SQLs abaixo como fixtures de referência; não reconstrua os exemplos de memória. Consulte o PDF apenas se houver dúvida não resolvida aqui. Se mudar uma decisão, atualize o ADR e a documentação correspondente. Faça alterações pequenas e verificáveis; reporte verificações executadas, falhas e pendências. Não adicione frontend, microserviços, filas, Kubernetes ou IaC sem necessidade demonstrada. Não declare compatibilidade ou equivalência sem evidência. Uma referência a este arquivo em `AGENTS.md` facilita seu uso recorrente.

## 8. SQLs originais dos anexos A–F

Os blocos a seguir preservam o conteúdo SQL do PDF, normalizando apenas espaçamento de extração e quebras de página. Não incluem melhorias de regras de negócio. Constituem a referência para as fixtures.

### Anexo A — Schema do banco legado

```sql
-- =============================================================
-- Schema do banco legado de referencia
-- Dominio: nucleo bancario simplificado
-- =============================================================

CREATE TABLE clientes (
    id              BIGSERIAL PRIMARY KEY,
    nome            VARCHAR(200) NOT NULL,
    cpf             CHAR(11) NOT NULL UNIQUE,
    data_cadastro   TIMESTAMP NOT NULL DEFAULT NOW(),
    status          VARCHAR(20) NOT NULL DEFAULT 'ATIVO'
                    CHECK (status IN ('ATIVO','INATIVO','BLOQUEADO'))
);

CREATE TABLE contas (
    id              BIGSERIAL PRIMARY KEY,
    cliente_id      BIGINT NOT NULL REFERENCES clientes(id),
    agencia         VARCHAR(10) NOT NULL,
    numero          VARCHAR(20) NOT NULL,
    tipo            VARCHAR(20) NOT NULL
                    CHECK (tipo IN ('CORRENTE','POUPANCA','SALARIO')),
    saldo           NUMERIC(18,2) NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'ATIVA'
                    CHECK (status IN ('ATIVA','INATIVA','ENCERRADA')),
    data_abertura   TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (agencia, numero)
);

CREATE TABLE transacoes (
    id                  BIGSERIAL PRIMARY KEY,
    conta_origem_id     BIGINT REFERENCES contas(id),
    conta_destino_id    BIGINT REFERENCES contas(id),
    tipo                VARCHAR(20) NOT NULL
                        CHECK (tipo IN ('DEPOSITO','SAQUE','TRANSFERENCIA','TARIFA')),
    valor               NUMERIC(18,2) NOT NULL CHECK (valor > 0),
    data_transacao      TIMESTAMP NOT NULL DEFAULT NOW(),
    status              VARCHAR(20) NOT NULL DEFAULT 'EFETIVADA'
                        CHECK (status IN ('EFETIVADA','CANCELADA','ESTORNADA'))
);

CREATE TABLE taxas (
    id               BIGSERIAL PRIMARY KEY,
    tipo_operacao    VARCHAR(20) NOT NULL,
    percentual       NUMERIC(7,4) NOT NULL DEFAULT 0,
    valor_minimo     NUMERIC(18,2) NOT NULL DEFAULT 0,
    vigente_de       DATE NOT NULL,
    vigente_ate      DATE
);

CREATE TABLE log_auditoria (
    id              BIGSERIAL PRIMARY KEY,
    entidade        VARCHAR(50) NOT NULL,
     entidade_id    BIGINT,
     acao           VARCHAR(50) NOT NULL,
     detalhes       JSONB,
     criado_em      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contas_cliente ON contas(cliente_id);
CREATE INDEX idx_transacoes_origem ON transacoes(conta_origem_id, data_transacao);
CREATE INDEX idx_transacoes_destino ON transacoes(conta_destino_id, data_transacao);
CREATE INDEX idx_log_entidade ON log_auditoria(entidade, entidade_id);
```

### Anexo B — fn_saldo_cliente (Complexidade: Baixa)

```sql
-- =============================================================
-- Anexo B: fn_saldo_cliente
-- Complexidade: Baixa
-- Retorna o saldo total consolidado de todas as contas ativas
-- de um cliente.
-- =============================================================

CREATE OR REPLACE FUNCTION fn_saldo_cliente(p_cliente_id BIGINT)
RETURNS NUMERIC(18,2)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total NUMERIC(18,2);
BEGIN
    SELECT COALESCE(SUM(saldo), 0)
       INTO v_total
       FROM contas
      WHERE cliente_id = p_cliente_id
        AND status = 'ATIVA';

       RETURN v_total;
END;
$$;
```

### Anexo C — sp_atualizar_status_contas_inativas (Complexidade: Baixa-Média)

```sql
-- =============================================================
-- Anexo C: sp_atualizar_status_contas_inativas
-- Complexidade: Baixa-Media
-- Marca como INATIVA toda conta que nao tenha movimentacao
-- ha mais de p_dias dias. Retorna a quantidade de contas afetadas.
-- =============================================================

CREATE OR REPLACE PROCEDURE sp_atualizar_status_contas_inativas(
    IN p_dias        INT,
    OUT p_afetadas   INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_dias IS NULL OR p_dias <= 0 THEN
        RAISE EXCEPTION 'Parametro p_dias deve ser positivo, recebido: %', p_dias;
    END IF;

       UPDATE contas c
          SET status = 'INATIVA'
        WHERE c.status = 'ATIVA'
          AND NOT EXISTS (
               SELECT 1
                 FROM transacoes t
                WHERE (t.conta_origem_id = c.id OR t.conta_destino_id = c.id)
                  AND t.data_transacao >= NOW() - (p_dias || ' days')::INTERVAL
          );

       GET DIAGNOSTICS p_afetadas = ROW_COUNT;

       INSERT INTO log_auditoria (entidade, acao, detalhes)
       VALUES (
           'contas',
           'INATIVACAO_LOTE',
           jsonb_build_object('dias', p_dias, 'afetadas', p_afetadas)
       );
END;
$$;
```

### Anexo D — sp_transferir_entre_contas (Complexidade: Média)

```sql
-- =============================================================
-- Anexo D: sp_transferir_entre_contas
-- Complexidade: Media
-- Transfere um valor entre duas contas em transacao atomica.
-- Valida saldo, status das contas e registra a transacao.
-- =============================================================

CREATE OR REPLACE PROCEDURE sp_transferir_entre_contas(
    IN p_conta_origem   BIGINT,
    IN p_conta_destino BIGINT,
    IN p_valor          NUMERIC(18,2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_saldo_origem    NUMERIC(18,2);
    v_status_origem   VARCHAR(20);
    v_status_destino VARCHAR(20);
BEGIN
    IF p_valor IS NULL OR p_valor <= 0 THEN
        RAISE EXCEPTION 'Valor invalido para transferencia: %', p_valor;
    END IF;

    IF p_conta_origem = p_conta_destino THEN
        RAISE EXCEPTION 'Conta de origem e destino nao podem ser iguais';
    END IF;

    SELECT saldo, status INTO v_saldo_origem, v_status_origem
      FROM contas WHERE id = p_conta_origem FOR UPDATE;

    SELECT status INTO v_status_destino
      FROM contas WHERE id = p_conta_destino FOR UPDATE;

    IF v_saldo_origem IS NULL THEN
        RAISE EXCEPTION 'Conta de origem % nao encontrada', p_conta_origem;
    END IF;

    IF v_status_origem <> 'ATIVA' OR v_status_destino <> 'ATIVA' THEN
        RAISE EXCEPTION 'Ambas as contas precisam estar ATIVAS';
    END IF;

    IF v_saldo_origem < p_valor THEN
        RAISE EXCEPTION 'Saldo insuficiente: saldo=% valor=%', v_saldo_origem, p_valor;
    END IF;

    UPDATE contas SET saldo = saldo - p_valor WHERE id = p_conta_origem;
    UPDATE contas SET saldo = saldo + p_valor WHERE id = p_conta_destino;

    INSERT INTO transacoes (conta_origem_id, conta_destino_id, tipo, valor)
    VALUES (p_conta_origem, p_conta_destino, 'TRANSFERENCIA', p_valor);
    INSERT INTO log_auditoria (entidade, entidade_id, acao, detalhes)
    VALUES (
        'transacoes',
        NULL,
        'TRANSFERENCIA_OK',
        jsonb_build_object(
            'origem', p_conta_origem,
            'destino', p_conta_destino,
            'valor',   p_valor
        )
    );

EXCEPTION
     WHEN OTHERS THEN
         INSERT INTO log_auditoria (entidade, acao, detalhes)
         VALUES (
             'transacoes',
             'TRANSFERENCIA_ERRO',
             jsonb_build_object(
                 'origem', p_conta_origem,
                 'destino', p_conta_destino,
                 'valor',   p_valor,
                 'erro',    SQLERRM
             )
         );
         RAISE;
END;
$$;
```

### Anexo E — sp_processar_lote_taxas (Complexidade: Alta)

```sql
-- =============================================================
-- Anexo E: sp_processar_lote_taxas
-- Complexidade: Alta
-- Percorre as transacoes efetivadas em uma data, calcula a tarifa
-- aplicavel conforme o tipo, registra a tarifa como uma nova
-- transacao do tipo TARIFA e mantem log detalhado em JSONB.
-- =============================================================

CREATE OR REPLACE PROCEDURE sp_processar_lote_taxas(
    IN p_data_referencia DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    cur_transacoes CURSOR FOR
        SELECT id, conta_origem_id, tipo, valor
          FROM transacoes
         WHERE DATE(data_transacao) = p_data_referencia
           AND status = 'EFETIVADA'
           AND tipo <> 'TARIFA';

    v_id           BIGINT;
    v_origem       BIGINT;
    v_tipo         VARCHAR(20);
    v_valor        NUMERIC(18,2);
    v_taxa         NUMERIC(18,2);
    v_percentual   NUMERIC(7,4);
    v_minimo       NUMERIC(18,2);
    v_total_taxas NUMERIC(18,2) := 0;
    v_count        INT := 0;
BEGIN
    OPEN cur_transacoes;

    LOOP
           FETCH cur_transacoes INTO v_id, v_origem, v_tipo, v_valor;
           EXIT WHEN NOT FOUND;

           SELECT percentual, valor_minimo
             INTO v_percentual, v_minimo
             FROM taxas
            WHERE tipo_operacao = v_tipo
              AND vigente_de <= p_data_referencia
              AND (vigente_ate IS NULL OR vigente_ate >= p_data_referencia)
            ORDER BY vigente_de DESC
            LIMIT 1;

           IF v_percentual IS NULL THEN
               CONTINUE;
           END IF;
          v_taxa := GREATEST(v_valor * v_percentual / 100.0, v_minimo);

          CASE v_tipo
              WHEN 'TRANSFERENCIA' THEN v_taxa := v_taxa;
              WHEN 'SAQUE'         THEN v_taxa := v_taxa * 1.10;
              ELSE                      v_taxa := v_taxa * 0.90;
          END CASE;

          IF v_origem IS NOT NULL THEN
              UPDATE contas SET saldo = saldo - v_taxa WHERE id = v_origem;

              INSERT INTO transacoes (conta_origem_id, tipo, valor, status)
              VALUES (v_origem, 'TARIFA', v_taxa, 'EFETIVADA');

              INSERT INTO log_auditoria (entidade, entidade_id, acao, detalhes)
              VALUES (
                  'transacoes', v_id, 'TARIFA_APLICADA',
                  jsonb_build_object(
                       'transacao_origem', v_id,
                       'tipo_origem',      v_tipo,
                       'valor_origem',     v_valor,
                       'percentual',       v_percentual,
                       'taxa_aplicada',    v_taxa
                  )
              );

               v_total_taxas := v_total_taxas + v_taxa;
               v_count       := v_count + 1;
           END IF;
       END LOOP;

       CLOSE cur_transacoes;

       INSERT INTO log_auditoria (entidade, acao, detalhes)
       VALUES (
           'lote_taxas', 'LOTE_PROCESSADO',
           jsonb_build_object(
               'data_referencia', p_data_referencia,
               'transacoes',      v_count,
               'total_taxas',     v_total_taxas
           )
       );
END;
$$;
```

### Anexo F — sp_relatorio_mensal_cliente (Complexidade: Muito Alta)

```sql
-- =============================================================
-- Anexo F: sp_relatorio_mensal_cliente
-- Complexidade: Muito Alta
-- Gera relatorio mensal de movimentacao de um cliente.
-- Usa CTE recursiva para encadear meses, chama fn_saldo_cliente
-- aninhada e retorna SETOF via RETURN QUERY. Captura excecao
-- com fallback degradado.
-- =============================================================

CREATE OR REPLACE FUNCTION sp_relatorio_mensal_cliente(
    p_cliente_id BIGINT,
    p_data_inicio DATE,
    p_data_fim     DATE
)
RETURNS TABLE (
    mes_referencia      DATE,
    total_creditos      NUMERIC(18,2),
    total_debitos       NUMERIC(18,2),
    saldo_consolidado NUMERIC(18,2),
    qtd_transacoes      INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_saldo_atual NUMERIC(18,2);
BEGIN
    IF p_data_inicio > p_data_fim THEN
        RAISE EXCEPTION 'Periodo invalido: inicio % > fim %', p_data_inicio, p_data_fim;
    END IF;

    v_saldo_atual := fn_saldo_cliente(p_cliente_id);
    RAISE NOTICE 'Saldo atual do cliente %: %', p_cliente_id, v_saldo_atual;

    RETURN QUERY
    WITH RECURSIVE meses AS (
        SELECT DATE_TRUNC('month', p_data_inicio)::DATE AS mes
        UNION ALL
        SELECT (mes + INTERVAL '1 month')::DATE
          FROM meses
         WHERE mes < DATE_TRUNC('month', p_data_fim)
    ),
    movimento AS (
        SELECT
            DATE_TRUNC('month', t.data_transacao)::DATE AS mes,
            SUM(CASE WHEN t.conta_destino_id IN (
                     SELECT id FROM contas WHERE cliente_id = p_cliente_id
                ) THEN t.valor ELSE 0 END) AS creditos,
            SUM(CASE WHEN t.conta_origem_id IN (
                     SELECT id FROM contas WHERE cliente_id = p_cliente_id
                ) THEN t.valor ELSE 0 END) AS debitos,
             COUNT(*) AS qtd
           FROM transacoes t
         WHERE t.status = 'EFETIVADA'
            AND t.data_transacao >= p_data_inicio
            AND t.data_transacao < p_data_fim + INTERVAL '1 day'
            AND (
                t.conta_origem_id IN (SELECT id FROM contas WHERE cliente_id =
p_cliente_id)
             OR t.conta_destino_id IN (SELECT id FROM contas WHERE cliente_id =
p_cliente_id)
            )
         GROUP BY 1
    )
    SELECT
        m.mes                                        AS mes_referencia,
        COALESCE(mv.creditos, 0)                     AS total_creditos,
        COALESCE(mv.debitos, 0)                      AS total_debitos,
        v_saldo_atual + COALESCE(mv.creditos, 0)
                       - COALESCE(mv.debitos, 0)     AS saldo_consolidado,
        COALESCE(mv.qtd, 0)::INT                     AS qtd_transacoes
      FROM meses m
      LEFT JOIN movimento mv ON mv.mes = m.mes
      ORDER BY m.mes;

EXCEPTION
    WHEN OTHERS THEN
         RAISE WARNING 'Falha ao gerar relatorio: %. Retornando linha de fallback.',
SQLERRM;

        RETURN QUERY
        SELECT
            DATE_TRUNC('month', p_data_inicio)::DATE,
            0::NUMERIC(18,2),
            0::NUMERIC(18,2),
            COALESCE(v_saldo_atual, 0),
            0::INT;
END;
$$;
```
