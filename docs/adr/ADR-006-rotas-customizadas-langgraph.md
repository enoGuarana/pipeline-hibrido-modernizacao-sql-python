# ADR-006 — Rotas customizadas no runtime LangGraph

- **Status:** aceito para a integração local; limites de servidor de desenvolvimento permanecem
- **Contexto:** o requisito O1 exige execução pelo LangGraph CLI, mas as rotas FastAPI existentes não eram montadas pelo runtime padrão. A configuração atual do CLI oferece `http.app` para carregar uma aplicação Starlette/FastAPI customizada.
- **Alternativas:** manter FastAPI separado; duplicar `/health` e `/modernize` em handlers do CLI; configurar `http.app` apontando para `pipeline.api:app`.
- **Decisão:** usar `http.app` em `langgraph.json`, apontando para `pipeline.api:app`, preservando as rotas e o lifespan existentes.
- **Prós/contras:** evita duplicação e mantém os contratos atuais; o lifespan da aplicação passa a bloquear a prontidão quando o PostgreSQL não autentica, exigindo configuração explícita do banco.
- **Evidência:** a documentação oficial descreve `http.app` como caminho de uma aplicação customizada; o CLI registrou `Loaded custom app from pipeline.api:app`. Com PostgreSQL isolado, `/health` respondeu 200 e a execução real B respondeu por `/modernize` com histórico persistido.
- **Condição de revisão:** revisar se a inicialização com PostgreSQL configurado não expuser `/health` e `/modernize`, ou se o bloqueio do banco exigir separar prontidão da API e inicialização da persistência.
