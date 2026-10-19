# Imputacion MICE de las features de clustering

- Entrada: `models_scaled.parquet`
- Columnas imputadas: `speed_tok_s_scaled`, `latency_ttft_s_scaled`, `excel_modeling_pct_scaled` …
- Filas: 89
- Features: 7
- Filas con al menos un dato (imputables): 59
- Filas sin ningun dato (excluidas): 30
- Celdas imputadas: 150

## Por que las filas vacias quedan nulas

MICE regresiona cada faltante contra las otras features de la misma fila.
Si la fila no tiene **ninguna** observacion, no hay regresores: el
imputador devuelve la media de la columna. Eso no es una estimacion del
modelo, es la media con otro nombre. Esas filas se dejan nulas y marcadas
en sus columnas `_imputed`, que quedan en `False`. Son 30 de
89.

## Celdas imputadas por feature

| Feature | Observadas | Imputadas | Cobertura final |
|---|---:|---:|---:|
| `speed_tok_s` | 50 | 9 | 66.3% |
| `latency_ttft_s` | 50 | 9 | 66.3% |
| `excel_modeling_pct` | 34 | 25 | 66.3% |
| `finance_agent_v2_pct` | 35 | 24 | 66.3% |
| `proof_bench_pct` | 29 | 30 | 66.3% |
| `terminal_bench_4_0_pct` | 26 | 33 | 66.3% |
| `vibe_code_bench_pct` | 39 | 20 | 66.3% |

## Validacion: MICE contra la mediana

Se tapo una celda observada por fila en 57 filas con al menos dos
datos, se imputo y se comparo contra el valor real. La mediana es el piso
que cualquier metodo tiene que superar para justificarse.

| Feature | n | MAE MICE | MAE mediana | Cociente | RMSE MICE | RMSE mediana |
|---|---:|---:|---:|---:|---:|---:|
| `speed_tok_s` | 13 | 0.6087 | 0.5119 | 1.19 | 0.7381 | 0.5499 |
| `latency_ttft_s` | 14 | 2.9100 | 0.1653 | 17.60 | 3.6127 | 0.2915 |
| `excel_modeling_pct` | 8 | 0.3222 | 0.6515 | 0.49 | 0.3658 | 0.6950 |
| `finance_agent_v2_pct` | 8 | 0.6835 | 0.7572 | 0.90 | 0.8579 | 0.7702 |
| `proof_bench_pct` | 5 | 0.3213 | 0.5241 | 0.61 | 0.3879 | 0.5500 |
| `terminal_bench_4_0_pct` | 3 | 0.2087 | 0.5733 | 0.36 | 0.2437 | 0.6320 |
| `vibe_code_bench_pct` | 6 | 0.5547 | 0.4956 | 1.12 | 0.6800 | 0.6078 |

El cociente es MAE MICE / MAE mediana: **menor que 1 significa que MICE
gana**. Se usa el cociente y no el MAE absoluto porque este ultimo esta en
unidades escaladas y no es comparable entre features.

MICE mejora a la mediana en **4 de 7** features.

## Pares con menos casos completos

Cada regresion de MICE se ajusta sobre las filas donde el par
(feature a imputar, feature explicativa) tiene ambos valores. Estos son los
pares mas flacos: con pocos casos, la estimacion es fragil aunque el
algoritmo converja.

| Par | Casos completos |
|---|---:|
| `speed_tok_s` x `terminal_bench_4_0_pct` | 22 |
| `latency_ttft_s` x `terminal_bench_4_0_pct` | 22 |
| `speed_tok_s` x `proof_bench_pct` | 25 |
| `latency_ttft_s` x `proof_bench_pct` | 25 |
| `proof_bench_pct` x `terminal_bench_4_0_pct` | 25 |
| `excel_modeling_pct` x `terminal_bench_4_0_pct` | 26 |
| `finance_agent_v2_pct` x `terminal_bench_4_0_pct` | 26 |
| `terminal_bench_4_0_pct` x `vibe_code_bench_pct` | 26 |
