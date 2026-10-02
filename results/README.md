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

O exportador recusa execuções simuladas, falhas, código ausente e sobrescrita
de um diretório existente. O bundle contém `source.sql`, `generated.py`,
`report.json` e `metadata.json`; ele não executa o código gerado.
