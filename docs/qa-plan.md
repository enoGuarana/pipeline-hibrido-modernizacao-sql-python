# Plano de Testes

## Camadas

1. Unitários: contratos, parser, comparação e métricas.
2. Integração: API, LangGraph, PostgreSQL e persistência.
3. Artefatos: hashes, metadados, origem e código exportados.
4. Comportamentais: referência SQL versus Python em schema isolado.

## Comandos

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check src tests scripts
.venv\Scripts\python.exe scripts/evaluate_results.py --results-dir results
```

## Critérios

- Falhas de geração e validação permanecem no denominador.
- Equivalência só é marcada após comparação executada.
- O código gerado não é executado pela API.

## Evidência atual

A última verificação registrada passou com 20 testes e Ruff. O relatório B/C
registra 3/3 cenários equivalentes. Isso não cobre D–F.
