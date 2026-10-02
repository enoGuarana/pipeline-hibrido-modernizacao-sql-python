import re

with open('DESAFIO_CONTEXTO.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract SQL blocks
sql_blocks = []
in_sql = False
current_block = []
for line in content.split('\n'):
    if line.startswith('### Anexo '):
        sql_blocks.append(line)
    elif line.startswith('```sql'):
        in_sql = True
        sql_blocks.append(line)
    elif line.startswith('```') and in_sql:
        in_sql = False
        sql_blocks.append(line)
        sql_blocks.append('')
    elif in_sql:
        sql_blocks.append(line)

new_content = """# Contexto do Desafio: Modernização PL/pgSQL -> Python (Refatorado)

Este documento consolida os principais pontos identificados do desafio técnico de modernização de stored procedures.

## 1. Objetivo Principal
Construir um **pipeline híbrido (Regras + LLM)** que converta rotinas PL/pgSQL para **Python 3.14**, exposto como uma API local orquestrada via **LangGraph CLI**.

## 2. Requisitos da Arquitetura (Pipeline em 4 Etapas)
Cada etapa deve ser um nó no LangGraph com estado tipado:
1. **Parsing**: Gerar AST ou estrutura intermediária (IR) usando ferramentas como `sqlglot`, `pglast` ou `sqlparse`.
2. **Análise Semântica**: Extrair parâmetros, variáveis e identificar riscos (cursores, transações, CTEs).
3. **Geração (LLM)**: Usar o contexto construído nas etapas anteriores para gerar o código Python. Exige decisão documentada sobre reescrita de lógica vs. delegação ao SGBD.
4. **Validação**: Verificação estática do código gerado (ex: `ast.parse` e linting).

## 3. Endpoints e Persistência Obrigatórios
- **GET /health**: Status da aplicação.
- **POST /modernize**: Recebe o código SQL e retorna o Python gerado + relatório de execução.
- **PostgreSQL**: Tabela `modernization_history` guardando todos os processamentos (sucesso, falha ou parcial) com detalhes em JSONB.

## 4. Requisitos Bônus (Diferenciais)
- **Observabilidade**: Integração com Langfuse/LangSmith (traces, spans e custos).
- **QA**: Validação com linters e testes automatizados via `pytest`.
- **Evaluation**: Implementar métrica automática de qualidade da migração (ex: taxa de parsing, LLM-as-judge).

## 5. Pontos de Atenção (Casos de Teste B a F)
A avaliação utilizará os scripts de A a F. Principais armadilhas:
- **Tipos de Dados**: Cuidado com `NUMERIC` vs `float` (dinheiro).
- **Controle Transacional**: A conversão de `EXCEPTION`, `ROLLBACK` e loops (`FOR UPDATE`) exige design cuidadoso no Python.
- **Recursão e Cursores**: Desafio extra no Anexo F (CTE recursiva) e E (Cursor com lógica interna). Cuidado com queries N+1.

## 6. SQLs Originais dos Anexos A-F

""" + '\n'.join(sql_blocks)

with open('DESAFIO_CONTEXTO_REFATORADO.md', 'w', encoding='utf-8') as f:
    f.write(new_content)
