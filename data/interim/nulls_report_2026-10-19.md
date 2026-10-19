# Reporte de nulos por atributo

- Corte: **2026-10-19**
- Filas (universo): **89**
- Atributos: **145**
- Cota de universo declarada: 41-100 -> OK
- Fuentes: OpenRouter (catalogo en vivo)

## Feature elegida por dimension

Los ejes agregados **no** entran en la matriz de distancia: promedian ranks de benchmarks que no cubren a los mismos modelos, asi que dos filas con el mismo valor no son la misma medicion. Cada dimension se representa con **un solo** benchmark, el de menos nulos.

| Dimension | Benchmark | Fuente | Valid | % nulos | Candidatos |
|---|---|---|---:|---:|---:|
| general **(fuera)** | `arena_elo` | arena.ai | 0 | 100.00 | 1 |
| reasoning | `proof_bench_pct` | vals.ai | 29 | 67.42 | 5 |
| coding | `vibe_code_bench_pct` | vals.ai | 39 | 56.18 | 6 |
| agentic | `terminal_bench_4_0_pct` | vals.ai | 26 | 70.79 | 6 |
| professional | `finance_agent_v2_pct` | vals.ai | 35 | 60.67 | 10 |
| data | `excel_modeling_pct` | vals.ai | 34 | 61.80 | 3 |
| browser **(fuera)** | `arena_agent_score` | arena.ai | 0 | 100.00 | 2 |
| multimodal **(fuera)** | `arena_vision_elo` | arena.ai | 0 | 100.00 | 2 |
| long_context **(fuera)** | `aa_lcr_v1_1_pct` | artificialanalysis.ai | 0 | 100.00 | 2 |
| instruction **(fuera)** | `ifbench_pct` | artificialanalysis.ai | 0 | 100.00 | 1 |

## Resumen por rol

| Rol | Atributos | Con datos | 100% nulos |
|---|---:|---:|---:|
| Entrenamiento (features de clustering) | 7 | 7 | 0 |
| Insumo (alimenta los ejes de calidad) | 43 | 26 | 17 |
| Faltantes (indicadores de imputacion) | 50 | 50 | 0 |
| Metadata (filtra / etiqueta) | 15 | 14 | 1 |
| Visualizacion (canal grafico) | 8 | 7 | 1 |
| Reporte (se publica, no es feature) | 13 | 6 | 7 |
| Auditoria (procedencia y confiabilidad) | 7 | 7 | 0 |
| Salida del clustering | 2 | 0 | 2 |

## Entrenamiento (features de clustering)

7 atributos, 0 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `terminal_bench_4_0_pct` | benchmark:agentic | float64 | 63 | 70.79 | 24 | 58.08 |
| `proof_bench_pct` | benchmark:reasoning | float64 | 60 | 67.42 | 24 | 100.0 |
| `excel_modeling_pct` | benchmark:data | float64 | 55 | 61.80 | 34 | 76.67 |
| `finance_agent_v2_pct` | benchmark:professional | float64 | 54 | 60.67 | 34 | 58.88 |
| `vibe_code_bench_pct` | benchmark:coding | float64 | 50 | 56.18 | 38 | 90.26 |
| `latency_ttft_s` | rendimiento | float64 | 39 | 43.82 | 50 | 9.94 |
| `speed_tok_s` | rendimiento | float64 | 39 | 43.82 | 47 | 183.0 |

## Insumo (alimenta los ejes de calidad)

43 atributos, 17 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `aa_analyst_agent_pct` **!!** | benchmark:data | float64 | 89 | 100.00 | 0 |  |
| `aa_lcr_v1_1_pct` **!!** | benchmark:long_context | float64 | 89 | 100.00 | 0 |  |
| `arena_agent_score` **!!** | benchmark:browser | float64 | 89 | 100.00 | 0 |  |
| `arena_elo` **!!** | benchmark:general | float64 | 89 | 100.00 | 0 |  |
| `arena_vision_elo` **!!** | benchmark:multimodal | float64 | 89 | 100.00 | 0 |  |
| `bfcl_pct` **!!** | benchmark:agentic | float64 | 89 | 100.00 | 0 |  |
| `gpqa_diamond_pct` **!!** | benchmark:reasoning | float64 | 89 | 100.00 | 0 |  |
| `hle_pct` **!!** | benchmark:reasoning | float64 | 89 | 100.00 | 0 |  |
| `ifbench_pct` **!!** | benchmark:instruction | float64 | 89 | 100.00 | 0 |  |
| `livebench_2_0_agentic` **!!** | benchmark:agentic | float64 | 89 | 100.00 | 0 |  |
| `livebench_2_0_browser_use` **!!** | benchmark:browser | float64 | 89 | 100.00 | 0 |  |
| `livebench_2_0_coding` **!!** | benchmark:coding | float64 | 89 | 100.00 | 0 |  |
| `livebench_2_0_data_analysis` **!!** | benchmark:data | float64 | 89 | 100.00 | 0 |  |
| `livebench_2_0_reasoning` **!!** | benchmark:reasoning | float64 | 89 | 100.00 | 0 |  |
| `livebench_2_0_research` **!!** | benchmark:long_context | float64 | 89 | 100.00 | 0 |  |
| `mmmu_pro_pct` **!!** | benchmark:multimodal | float64 | 89 | 100.00 | 0 |  |
| `swe_bench_verified_pct` **!!** | benchmark:coding | float64 | 89 | 100.00 | 0 |  |
| `skillsbench_pct` | benchmark:agentic | float64 | 75 | 84.27 | 14 | 61.55 |
| `sre_bench_pct` | benchmark:agentic | float64 | 72 | 80.90 | 16 | 22.9 |
| `legal_bench_pct` | benchmark:professional | float64 | 68 | 76.40 | 21 | 88.51 |
| `public_benefits_bench_pct` | benchmark:professional | float64 | 68 | 76.40 | 21 | 74.9 |
| `terminal_bench_science_pct` | benchmark:reasoning | float64 | 67 | 75.28 | 12 | 40.0 |
| `cyberbench_pct` | benchmark:agentic | float64 | 64 | 71.91 | 24 | 70.42 |
| `programbench_pct` | benchmark:coding | float64 | 64 | 71.91 | 11 | 7.0 |
| `sage_pct` | benchmark:professional | float64 | 64 | 71.91 | 25 | 48.53 |
| `ioi_pct` | benchmark:coding | float64 | 63 | 70.79 | 26 | 90.78 |
| `vals_index_pct` | benchmark:professional | float64 | 63 | 70.79 | 26 | 65.83 |
| `medcode_pct` | benchmark:professional | float64 | 61 | 68.54 | 28 | 53.51 |
| `medscribe_pct` | benchmark:professional | float64 | 60 | 67.42 | 29 | 91.29 |
| `tax_agent_bench_pct` | benchmark:professional | float64 | 56 | 62.92 | 33 | 49.19 |
| `harvey_lab_pct` | benchmark:professional | float64 | 55 | 61.80 | 20 | 6.67 |
| `legal_research_pct` | benchmark:professional | float64 | 55 | 61.80 | 31 | 55.29 |
| `code_migration_pct` | benchmark:coding | float64 | 54 | 60.67 | 35 | 54.61 |
| `quality_agentic_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 5 | 0 |
| `quality_browser_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 1 | 0 |
| `quality_coding_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 5 | 0 |
| `quality_data_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 2 | 0 |
| `quality_general_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 1 | 0 |
| `quality_instruction_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 1 | 0 |
| `quality_long_context_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 1 | 0 |
| `quality_multimodal_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 1 | 0 |
| `quality_professional_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 9 | 0 |
| `quality_reasoning_n_sources` | calidad-ejes | Int64 | 0 | 0.00 | 3 | 0 |

## Faltantes (indicadores de imputacion)

50 atributos, 0 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `aa_analyst_agent_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `aa_lcr_v1_1_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `arena_agent_score_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `arena_elo_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `arena_vision_elo_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `bfcl_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `code_migration_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `cyberbench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `excel_modeling_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `finance_agent_v2_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `gpqa_diamond_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `harvey_lab_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `hle_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `ifbench_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `ioi_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `latency_ttft_s_missing` | faltantes | boolean | 0 | 0.00 | 2 | False |
| `legal_bench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `legal_research_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `livebench_2_0_agentic_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `livebench_2_0_browser_use_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `livebench_2_0_coding_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `livebench_2_0_data_analysis_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `livebench_2_0_reasoning_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `livebench_2_0_research_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `medcode_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `medscribe_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `mmmu_pro_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `programbench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `proof_bench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `public_benefits_bench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `quality_agentic_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `quality_browser_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `quality_coding_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `quality_data_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `quality_general_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `quality_instruction_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `quality_long_context_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `quality_multimodal_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `quality_professional_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `quality_reasoning_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `sage_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `skillsbench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `speed_tok_s_missing` | faltantes | boolean | 0 | 0.00 | 2 | False |
| `sre_bench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `swe_bench_verified_pct_missing` | faltantes | boolean | 0 | 0.00 | 1 | True |
| `tax_agent_bench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `terminal_bench_4_0_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `terminal_bench_science_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `vals_index_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |
| `vibe_code_bench_pct_missing` | faltantes | boolean | 0 | 0.00 | 2 | True |

## Metadata (filtra / etiqueta)

15 atributos, 1 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `n_providers` **!!** | mercado | float64 | 89 | 100.00 | 0 |  |
| `hugging_face_id` | identidad | string | 44 | 49.44 | 45 | arcee-ai/Trinity-Large-Thinking |
| `canonical_slug` | identidad | string | 0 | 0.00 | 89 | amazon/nova-2-lite-v1 |
| `context_length` | capacidad | float64 | 0 | 0.00 | 22 | 1000000.0 |
| `family` | identidad | string | 0 | 0.00 | 89 | nova |
| `is_open_weights` | capacidad | boolean | 0 | 0.00 | 2 | False |
| `max_output_tokens` | capacidad | float64 | 0 | 0.00 | 29 | 65535.0 |
| `model_id` | identidad | string | 0 | 0.00 | 89 | amazon/nova-2-lite-v1 |
| `name` | identidad | string | 0 | 0.00 | 89 | Amazon: Nova 2 Lite |
| `provider` | identidad | string | 0 | 0.00 | 36 | amazon |
| `release_date` | identidad | datetime64[ms] | 0 | 0.00 | 71 | 2025-12-02 00:00:00 |
| `supports_audio` | modalidades | boolean | 0 | 0.00 | 2 | False |
| `supports_reasoning` | modalidades | boolean | 0 | 0.00 | 2 | True |
| `supports_tools` | modalidades | boolean | 0 | 0.00 | 2 | True |
| `supports_vision` | modalidades | boolean | 0 | 0.00 | 2 | True |

## Visualizacion (canal grafico)

8 atributos, 1 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `price_reasoning_usd_per_mtok` **!!** | precio | float64 | 89 | 100.00 | 0 |  |
| `price_cache_write_usd_per_mtok` | precio | float64 | 78 | 87.64 | 7 | 12.5 |
| `price_web_search_usd_per_call` | precio | float64 | 67 | 75.28 | 6 | 0.01 |
| `price_cache_read_usd_per_mtok` | precio | float64 | 18 | 20.22 | 41 | 0.625 |
| `price_in_usd_per_mtok` | precio | float64 | 0 | 0.00 | 45 | 0.3 |
| `price_out_usd_per_mtok` | precio | float64 | 0 | 0.00 | 53 | 2.5 |
| `weighted_cost_profile` | costo | string | 0 | 0.00 | 2 | 80/20 |
| `weighted_cost_usd_per_mtok` | costo | float64 | 0 | 0.00 | 79 | 0.74 |

## Reporte (se publica, no es feature)

13 atributos, 7 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `coding_index` **!!** | calidad-reporte | float64 | 89 | 100.00 | 0 |  |
| `math_index` **!!** | calidad-reporte | float64 | 89 | 100.00 | 0 |  |
| `quality_browser` **!!** | calidad-ejes | float64 | 89 | 100.00 | 0 |  |
| `quality_general` **!!** | calidad-ejes | float64 | 89 | 100.00 | 0 |  |
| `quality_instruction` **!!** | calidad-ejes | float64 | 89 | 100.00 | 0 |  |
| `quality_long_context` **!!** | calidad-ejes | float64 | 89 | 100.00 | 0 |  |
| `quality_multimodal` **!!** | calidad-ejes | float64 | 89 | 100.00 | 0 |  |
| `quality_reasoning` | calidad-ejes | float64 | 60 | 67.42 | 27 | 0.8918495297805643 |
| `quality_agentic` | calidad-ejes | float64 | 59 | 66.29 | 30 | 0.8244731738849386 |
| `quality_data` | calidad-ejes | float64 | 55 | 61.80 | 34 | 1.0 |
| `quality_professional` | calidad-ejes | float64 | 52 | 58.43 | 37 | 0.9169098366136905 |
| `quality_coding` | calidad-ejes | float64 | 50 | 56.18 | 39 | 0.9133516483516483 |
| `intelligence_index` | calidad-reporte | float64 | 42 | 47.19 | 33 | 53.0 |

## Auditoria (procedencia y confiabilidad)

7 atributos, 0 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `row_confidence` | procedencia | float64 | 0 | 0.00 | 1 | 1.0 |
| `src_artificial_analysis` | procedencia | boolean | 0 | 0.00 | 2 | True |
| `src_hf` | procedencia | boolean | 0 | 0.00 | 2 | False |
| `src_livebench` | procedencia | boolean | 0 | 0.00 | 1 | False |
| `src_lmarena` | procedencia | boolean | 0 | 0.00 | 1 | False |
| `src_openrouter` | procedencia | boolean | 0 | 0.00 | 1 | True |
| `src_vals` | procedencia | boolean | 0 | 0.00 | 2 | False |

## Salida del clustering

2 atributos, 2 sin ningun dato.

| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |
|---|---|---|---:|---:|---:|---|
| `cluster_id` **!!** | clustering | Int64 | 89 | 100.00 | 0 |  |
| `cluster_label` **!!** | clustering | string | 89 | 100.00 | 0 |  |

## Bloqueantes para clusterizar

Ninguno: todas las features de entrenamiento tienen datos.

## Insumos de los ejes de calidad

43 columnas de insumo, 17 de ellas sin ningun dato.

## Features de entrenamiento utilizables hoy

| Atributo | Cobertura |
|---|---:|
| `excel_modeling_pct` | 38.20% |
| `finance_agent_v2_pct` | 39.33% |
| `latency_ttft_s` | 56.18% |
| `proof_bench_pct` | 32.58% |
| `speed_tok_s` | 56.18% |
| `terminal_bench_4_0_pct` | 29.21% |
| `vibe_code_bench_pct` | 43.82% |
