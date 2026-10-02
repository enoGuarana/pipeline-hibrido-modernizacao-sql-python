# Resultados

Os resultados reais de geração devem ser salvos aqui com o mesmo identificador
da execução persistida.

Cada conjunto deve conter, no mínimo, SQL de origem, código produzido,
relatório JSON, modelo, versão do prompt e limitações. O stub simulado não é
resultado real de LLM e não pode ser usado para alegar equivalência.

Depois de uma execução real bem-sucedida, exporte o registro pelo identificador:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/modernization"
.\.venv\Scripts\python.exe scripts\export_result.py <run_id>
```

O exportador recusa execuções simuladas, código ausente e sobrescrita
de um diretório existente. Falhas reais com código são preservadas para manter
as tentativas auditáveis. O bundle contém `source.sql`, `generated.py`,
`report.json` e `metadata.json`; ele não executa o código gerado.

Para novas execuções, geração real significa `generation_mode=gemini`. A
tentativa OpenAI anterior permanece apenas como evidência histórica de falha.

Artefatos atuais:

- `run-11`: geração real com falha Ruff e reparo indisponível;
- `run-17`: geração e reparo reais, com falha Ruff final de ordenação de imports;
- `run-18`: geração real aprovada em `ast.parse` e Ruff na primeira tentativa.
- `run-19` a `run-22`: primeira rodada real C–F, com C/E aprovados estaticamente
  após reparo e D/F falhos.
- `run-23` a `run-26`: rodada com `modernize_v4`; C aprovado após reparo e D/E/F
  falhos por validação estática. A revisão está em `semantic-review.md`.

Nenhum desses bundles comprova equivalência comportamental.
