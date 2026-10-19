# Reporte de limpieza

- Corte: **2026-10-19**
- Crudo de entrada: `465` modelos
- Universo resultante: **89** modelos
- Cota declarada: 41-100 -> OK

## Embudo

| Paso | Filas |
|---|---|
| Crudas (catalogo completo) | 465 |
| Tras dedupe de variantes | 377 |
| Tras exclusiones | 308 |
| Tras filtro de solo texto | 308 |
| Tras ventana de 12 meses | 193 |
| Familias con representante | 102 |
| Tras colapsar tiers de servicio | 89 |
| **Universo final** | **89** |

Descartados por frescura (publicados hace menos de 7 dias): 8.
Familias que quedaron sin representante por eso: 8.

## Exclusiones aplicadas

| Patron | Modelos descartados |
|---|---|
| `^~` | 19 |
| `-image` | 9 |
| `^aion-` | 6 |
| `^openrouter/` | 6 |
| `hy-mt2` | 3 |
| `schematron` | 2 |
| `lyria` | 2 |
| `gpt-audio` | 2 |
| `relace` | 2 |
| `morph-v3` | 2 |
| `euryale` | 2 |
| `pareto` | 1 |
| `summarize` | 1 |
| `nano-banana` | 1 |
| `jev-router` | 1 |
| `switchyard` | 1 |
| `content-safety` | 1 |
| `safeguard` | 1 |
| `cydonia` | 1 |
| `uncensored` | 1 |
| `llama-guard` | 1 |
| `skyfall` | 1 |
| `unslopnemo` | 1 |
| `magnum` | 1 |
| `mythomax` | 1 |

## Benchmarks

Fuentes de benchmark:

- `benchmarks_aa_2026-10-16.json` -> source `aa` (2026-10-16T17:11:44+00:00), 273 filas
- `benchmarks_vals_2026-10-16.json` -> source `vals` (2026-10-16T18:04:05+00:00), 1483 filas

`declaradas` son los nombres que publica la fuente; `unidas` los que encontraron fila en el catalogo; `en el universo` los que sobrevivieron a la seleccion. La ultima es la cobertura que importa.

| Columna | Declaradas | Unidas | Por alias | En el universo (89) | Cobertura |
|---|---:|---:|---:|---:|---:|
| `code_migration_pct` | 77 | 70 | 1 | 35 | 39.3% |
| `cyberbench_pct` | 47 | 40 | 0 | 25 | 28.1% |
| `excel_modeling_pct` | 74 | 67 | 1 | 34 | 38.2% |
| `finance_agent_v2_pct` | 78 | 69 | 1 | 35 | 39.3% |
| `harvey_lab_pct` | 79 | 69 | 1 | 34 | 38.2% |
| `intelligence_index` | 134 | 62 | 3 | 47 | 52.8% |
| `ioi_pct` | 44 | 40 | 0 | 26 | 29.2% |
| `latency_ttft_s` | 161 | 72 | 5 | 50 | 56.2% |
| `legal_bench_pct` | 150 | 91 | 1 | 21 | 23.6% |
| `legal_research_pct` | 78 | 68 | 1 | 34 | 38.2% |
| `medcode_pct` | 107 | 79 | 1 | 28 | 31.5% |
| `medscribe_pct` | 109 | 81 | 1 | 29 | 32.6% |
| `programbench_pct` | 64 | 56 | 0 | 25 | 28.1% |
| `proof_bench_pct` | 52 | 45 | 0 | 29 | 32.6% |
| `public_benefits_bench_pct` | 50 | 43 | 0 | 21 | 23.6% |
| `sage_pct` | 91 | 70 | 1 | 25 | 28.1% |
| `skillsbench_pct` | 34 | 33 | 0 | 14 | 15.7% |
| `speed_tok_s` | 161 | 72 | 5 | 50 | 56.2% |
| `sre_bench_pct` | 35 | 30 | 0 | 17 | 19.1% |
| `tax_agent_bench_pct` | 69 | 62 | 1 | 33 | 37.1% |
| `terminal_bench_4_0_pct` | 48 | 43 | 0 | 26 | 29.2% |
| `terminal_bench_science_pct` | 41 | 37 | 0 | 22 | 24.7% |
| `vals_index_pct` | 48 | 43 | 0 | 26 | 29.2% |
| `vibe_code_bench_pct` | 108 | 90 | 1 | 39 | 43.8% |

### Variante de esfuerzo elegida

La fuente publica el mismo modelo en varios niveles de esfuerzo, que dan numeros distintos. Se elige de forma determinista el de mayor rango; nunca se promedian.

Modelos con mas de una variante: 86

| Clave | Variante elegida |
|---|---|
| `claude-opus-5.5` | 'Claude Opus 5.5 (max with fallback)' (esfuerzo max with fallback) |
| `claude-sonnet-5.5` | 'Claude Sonnet 5.5 (max with fallback)' (esfuerzo max with fallback) |
| `claude-fable-5.1` | 'Claude Fable 5.1 (max with fallback)' (esfuerzo max with fallback) |
| `gpt-6-astra` | 'GPT-6 Astra (max)' (esfuerzo max) |
| `gpt-6.1-sol` | 'GPT-6.1 Sol (max)' (esfuerzo max) |
| `muse-spark-1.3` | 'Muse Spark 1.3 (max)' (esfuerzo max) |
| `grok-4.7` | 'Grok 4.7 (xhigh)' (esfuerzo xhigh) |
| `glm-5.3` | 'GLM-5.3 (max)' (esfuerzo max) |
| `kimi-k-3` | 'Kimi K3 (max)' (esfuerzo max) |
| `claude-haiku-5.5` | 'Claude Haiku 5.5 (max)' (esfuerzo max) |
| `gpt-5.6-terra` | 'GPT-5.6 Terra (max)' (esfuerzo max) |
| `gemini-3.8-flash` | 'Gemini 3.8 Flash (high)' (esfuerzo high) |
| `deepseek-v-4.1-flash` | 'DeepSeek V4.1 Flash (max)' (esfuerzo max) |
| `gpt-6-luna` | 'GPT-6 Luna (max)' (esfuerzo max) |
| `deepseek-v-4-pro-0813` | 'DeepSeek V4 Pro 0813 (max)' (esfuerzo max) |
| `qwen-3.8-27-b` | 'Qwen3.8 27B (xhigh)' (esfuerzo xhigh) |
| `claude-opus-5.5` | 'Claude Opus 5.5 (max with fallback)' (esfuerzo max with fallback) |
| `claude-sonnet-5.5` | 'Claude Sonnet 5.5 (max with fallback)' (esfuerzo max with fallback) |
| `claude-fable-5.1` | 'Claude Fable 5.1 (max with fallback)' (esfuerzo max with fallback) |
| `gpt-6-astra` | 'GPT-6 Astra (max)' (esfuerzo max) |
| `gpt-6.1-sol` | 'GPT-6.1 Sol (max)' (esfuerzo max) |
| `muse-spark-1.3` | 'Muse Spark 1.3 (max)' (esfuerzo max) |
| `grok-4.7` | 'Grok 4.7 (xhigh)' (esfuerzo xhigh) |
| `glm-5.3` | 'GLM-5.3 (max)' (esfuerzo max) |
| `kimi-k-3` | 'Kimi K3 (max)' (esfuerzo max) |

## Cobertura de fuentes

- `src_openrouter`: 89 / 89
- `src_artificial_analysis`: 51 / 89
- `src_lmarena`: 0 / 89
- `src_vals`: 41 / 89
- `src_livebench`: 0 / 89
- Laboratorios obligatorios ausentes: china-mobile, institute-of-foundation-models, motif-technologies, reflection, sapiens-ai

Proveedores en el universo (36): alibaba, amazon, anthropic, arcee-ai, bytedance-seed, cohere, deepseek, dots-studio, fireworks, google, ibm-granite, inception, inclusionai, liquid, meituan, meta, minimax, mistral, moonshot, nex-agi, nvidia, openai, perceptron, perplexity, poolside, prism-ml, rekaai, sakana, spacexai, stepfun, tencent, thinkingmachines, upstage, writer, xiaomi, z-ai
