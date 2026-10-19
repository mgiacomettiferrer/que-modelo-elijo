# Tabla de analisis: solo Artificial Analysis

- Fuente de la tabla: `aa_models_2026-10-19.parquet`
- Filas en la fuente: 27
- Criterio: al menos 6 de 7 features de analisis
- Filas que quedan: **24**
- Filas descartadas: 3

## Features y su columna de origen

La fuente no mide los mismos benchmarks que el pipeline principal. Cada
feature usa el equivalente de la misma dimension, y el cambio queda
declarado aca: promediar `scicode_pct` con `vibe_code_bench_pct` de Vals
seria entreverar hosts.

| Feature | Columna de la fuente | Benchmark | Con dato |
|---|---|---|---:|
| `speed_tok_s` | `speed_tok_s` | medias propias de AA | 24/24 |
| `latency_ttft_s` | `latency_ttft_s` | medias propias de AA | 24/24 |
| `reasoning` | `gdpval_normalized_pct` | GDPval-AA v2.1 | 24/24 |
| `coding` | `scicode_pct` | SciCode | 24/24 |
| `agentic` | `terminal_bench_4_0_pct` | Terminal-Bench 4.0 | 24/24 |
| `professional` | `gdp_pdf_all_pass_pct` | GDP.pdf | 24/24 |
| `data` | `analyst_agent_pct` | AA-AnalystAgent | 16/24 |

## Distribucion de features por fila

| Features presentes | Filas |
|---|---:|
| 6 | 8 |
| 7 | 16 |

## Filas descartadas

| Modelo | Features | Faltan |
|---|---:|---|
| Gemini 4 Argon (High) | 5 |  |
| Muse Wonder Full (Max) | 4 |  |
| MiniMax-M3.1-Flash | 4 |  |

## Cobertura por columna de la tabla

| Columna | Con dato | % |
|---|---:|---:|
| `aa_slug` | 24 | 100.0% |
| `aa_name` | 24 | 100.0% |
| `creator_name` | 24 | 100.0% |
| `release_date` | 24 | 100.0% |
| `context_window_tokens` | 24 | 100.0% |
| `parameters_billions` | 13 | 54.2% |
| `is_open_weights` | 24 | 100.0% |
| `speed_tok_s` | 24 | 100.0% |
| `latency_ttft_s` | 24 | 100.0% |
| `gdpval_normalized_pct` | 24 | 100.0% |
| `scicode_pct` | 24 | 100.0% |
| `terminal_bench_4_0_pct` | 24 | 100.0% |
| `gdp_pdf_all_pass_pct` | 24 | 100.0% |
| `analyst_agent_pct` | 16 | 66.7% |
| `n_features` | 24 | 100.0% |
| `intelligence_index` | 24 | 100.0% |
| `aa_lcr_pct` | 24 | 100.0% |
| `mmmu_pro_pct` | 13 | 54.2% |
| `omniscience_index` | 24 | 100.0% |
| `harvey_lab_pct` | 15 | 62.5% |
| `frontier_code_pct` | 18 | 75.0% |
| `price_in_usd_per_mtok` | 24 | 100.0% |
| `price_out_usd_per_mtok` | 24 | 100.0% |
| `ii_output_tokens_per_task` | 24 | 100.0% |
| `ii_time_per_task_s` | 24 | 100.0% |
