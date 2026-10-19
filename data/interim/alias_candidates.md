# Candidatos de alias para revision manual

Generado por `python -m src.alias_review`. **No** se aplica nada al dataset: cada par necesita confirmacion humana.

- Corte: 2026-10-16
- Filas en el universo: 89
- Nombres de fuente sin aparear: 226
- Pares propuestos: 24
- Alias confirmados y aplicados por `src/aliases.py`: 6
- Pares descartados en revision: 3

## Como leer los niveles

| Nivel | Significado | Que se espera |
|---|---|---|
| `T1` | tokens identicos, difiere el formato | confirmar |
| `T1E` | difiere solo el esfuerzo | confirmar |
| `T2` | la fuente agrega o quita palabras | revisar |
| `T2S` | la fuente omite el tamano o la version | revisar |
| `T3` | conflicto de version, tamano o escalon | descartar salvo evidencia |

Un escalon es `Mini`, `Nano`, `Pro`, `Flash`, `Lite`, `Max`, `Ultra`, `Super`, `Omni`, `VL`, `Codex`, `Plus`. Que aparezca en un lado y no en el otro son modelos distintos, no formato. `Preview`, `Beta` y `Exp` no cuentan: son estado.

## T1 - solo difiere el formato (casi seguro el mismo modelo)

| # | Modelo del universo | Slug | Nombre en la fuente | Fuente | Rellena | Sobra en fuente | Sobra en fila | Sim | Aviso | Mismo? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Amazon: Nova 2 Lite | `amazon/nova-2-lite-v1` | Nova 2.0 Lite (high) | artificialanalysis.ai | — | — | — | 0.782 |  |  |

## T2S - la fuente omite el tamano o la version que la fila si declara

| # | Modelo del universo | Slug | Nombre en la fuente | Fuente | Rellena | Sobra en fuente | Sobra en fila | Sim | Aviso | Mismo? |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | NVIDIA: Nemotron 3 Nano 30B A3B | `nvidia/nemotron-3-nano-30b-a3b` | Nemotron 3 Nano (non-reasoning) | artificialanalysis.ai | — | — | 30b, 3b, a | 0.524 | COLISION: el mismo nombre lo pide tambien NVIDIA: Nemotron 3 Nano Omni (free) (`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428`) |  |

## T3 - conflicto de version, tamano o escalon (probablemente NO es el mismo)

| # | Modelo del universo | Slug | Nombre en la fuente | Fuente | Rellena | Sobra en fuente | Sobra en fila | Sim | Aviso | Mismo? |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Qwen: Qwen3.8 Omni Flash | `qwen/qwen3.8-omni-flash-20260918` | Qwen3.5 Omni Flash | artificialanalysis.ai | `latency_ttft_s`, `speed_tok_s` | 3.5 | 3.8 | 0.705 |  |  |
| 4 | inclusionAI: Ling 3.0 Flash VL | `inclusionai/ling-3.0-flash-vl-20260910` | Ling 3.0 Flash | vals.ai | `excel_modeling_pct`, `finance_agent_v2_pct`, `vibe_code_bench_pct` | — | vl | 0.693 | COLISION: el mismo nombre lo pide tambien inclusionAI: Ling 3.1 Flash (`inclusionai/ling-3.1-flash-20261002`) |  |
| 5 | NVIDIA: Nemotron 3 Nano Omni (free) | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428` | Nemotron 3 Nano (non-reasoning) | artificialanalysis.ai | — | — | omni | 0.678 | COLISION: el mismo nombre lo pide tambien NVIDIA: Nemotron 3 Nano 30B A3B (`nvidia/nemotron-3-nano-30b-a3b`) |  |
| 6 | Cohere: Command A+ | `cohere/command-a-plus-05-2026` | Command A | artificialanalysis.ai | — | — | plus | 0.667 |  |  |
| 7 | OpenAI: GPT-5.1-Codex-Mini | `openai/gpt-5.1-codex-mini-20251113` | GPT 5.1 Codex | vals.ai | `vibe_code_bench_pct` | — | mini | 0.657 |  |  |
| 8 | IBM: Granite 4.2 8B | `ibm-granite/granite-4.2-8b-20260831` | Granite 4.2 3B | artificialanalysis.ai | — | 3b | 8b | 0.644 |  |  |
| 9 | Qwen: Qwen3.8 Flash | `qwen/qwen3.8-flash-20260826` | Qwen 3.5 Flash | vals.ai | — | 3.5 | 3.8 | 0.644 |  |  |
| 10 | Xiaomi: MiMo-V2.5 | `xiaomi/mimo-v2.5-20260422` | MiMo V2.5 Pro | vals.ai | `terminal_bench_4_0_pct` | pro | — | 0.642 |  |  |
| 11 | Qwen: Qwen3.7 Plus | `qwen/qwen3.7-plus-20260602` | Qwen 3.5 Plus | vals.ai | — | 3.5 | 3.7 | 0.637 |  |  |
| 12 | DeepSeek: DeepSeek V4 Flash Vision Exp | `deepseek/deepseek-v4-flash-vision-exp-20260821` | DeepSeek V4 Flash 0731 | vals.ai | `excel_modeling_pct`, `finance_agent_v2_pct`, `proof_bench_pct`, `terminal_bench_4_0_pct`, `vibe_code_bench_pct` | 0731 | vision | 0.633 |  |  |
| 13 | Qwen: Qwen3.8 27B | `qwen/qwen3.8-27b-20260814` | Qwen 3.6 27B | vals.ai | — | 3.6 | 3.8 | 0.629 |  |  |
| 14 | Mistral: Mistral Large 4 | `mistralai/mistral-large-4-0-20261006` | Mistral Large 3 | vals.ai | — | 3 | 4 | 0.609 |  |  |
| 15 | Google: Gemma 4 31B | `google/gemma-4-31b-it-20260402` | Gemma 4 12B | artificialanalysis.ai | — | 12b | 31b | 0.583 |  |  |
| 16 | DeepSeek: DeepSeek V3.2 | `deepseek/deepseek-v3.2-20251201` | DeepSeek V3 | vals.ai | — | 3 | 3.2 | 0.574 |  |  |
| 17 | Google: Gemini 3.1 Pro Preview | `google/gemini-3.1-pro-preview-20260219` | Gemini 3.1 Flash Lite Preview | vals.ai | `excel_modeling_pct`, `finance_agent_v2_pct`, `vibe_code_bench_pct` | flash, lite | pro | 0.572 |  |  |
| 18 | OpenAI: GPT-5.4 Mini | `openai/gpt-5.4-mini-20260317` | GPT 5.4 (high) | vals.ai | — | — | mini | 0.569 |  |  |
| 19 | inclusionAI: Ling 3.1 Flash | `inclusionai/ling-3.1-flash-20261002` | Ling 3.0 Flash | vals.ai | `excel_modeling_pct`, `finance_agent_v2_pct`, `vibe_code_bench_pct` | 3 | 3.1 | 0.567 | COLISION: el mismo nombre lo pide tambien inclusionAI: Ling 3.0 Flash VL (`inclusionai/ling-3.0-flash-vl-20260910`) |  |
| 20 | NVIDIA: Nemotron 3 Super | `nvidia/nemotron-3-super-120b-a12b-20230311` | Nemotron 3.5 Super VL | artificialanalysis.ai | `latency_ttft_s`, `speed_tok_s` | 3.5, vl | 3 | 0.556 |  |  |
| 21 | OpenAI: GPT-5.4 Nano | `openai/gpt-5.4-nano-20260317` | GPT 5.4 | vals.ai | — | — | nano | 0.556 |  |  |
| 22 | Mistral: Ministral 3 14B 2512 | `mistralai/ministral-14b-2512` | Ministral 3 8B | artificialanalysis.ai | `latency_ttft_s`, `speed_tok_s` | 8b | 14b | 0.552 |  |  |
| 23 | OpenAI: GPT-5.3-Codex | `openai/gpt-5.3-codex-20260224` | GPT 5.2 Codex | vals.ai | — | 5.2 | 5.3 | 0.544 |  |  |
| 24 | Google: Gemma 4 26B A4B  | `google/gemma-4-26b-a4b-it-20260403` | Gemma 4 E4B | artificialanalysis.ai | — | e | 26b, a | 0.536 |  |  |

## Colisiones: revisar antes que nada

Estas filas proponen el **mismo** nombre de la fuente. A lo sumo una puede ser correcta; si se aplicaran todas, dos modelos distintos compartirian los mismos puntajes.

- `Nemotron 3 Nano (non-reasoning)` -> NVIDIA: Nemotron 3 Nano 30B A3B (`nvidia/nemotron-3-nano-30b-a3b`), nivel T2S, sim 0.524
- `Ling 3.0 Flash` -> inclusionAI: Ling 3.0 Flash VL (`inclusionai/ling-3.0-flash-vl-20260910`), nivel T3, sim 0.693
- `Nemotron 3 Nano (non-reasoning)` -> NVIDIA: Nemotron 3 Nano Omni (free) (`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428`), nivel T3, sim 0.678
- `Ling 3.0 Flash` -> inclusionAI: Ling 3.1 Flash (`inclusionai/ling-3.1-flash-20261002`), nivel T3, sim 0.567

## Decisiones ya tomadas

Viven en `src/aliases.py` y `merge_benchmarks` las aplica antes de `match_key`. No hace falta revisarlas de nuevo; quedan aca como registro.

### Confirmados

| Nombre en la fuente | Fila |
|---|---|
| Grok 4.20 (Reasoning) | `x-ai/grok-4.20-multi-agent-20260309` |
| Muse Glimmer (high) | `meta/muse-glimmer-30b-20260810` |
| Nemotron 3 Nano | `nvidia/nemotron-3-nano-30b-a3b` |
| Nemotron 3 Nano Omni 30B A3B | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428` |
| Nova 2.0 Lite (low) | `amazon/nova-2-lite-v1` |
| Qwen3.8-Flash-Next | `qwen/qwen3.8-flash-20260826` |

### Descartados

| Nombre en la fuente | Motivo |
|---|---|
| Laguna XS.2 | no confirmado contra poolside/laguna-xs-2.1-20260625 |
| Ministral 3 14B | no confirmado contra mistralai/ministral-14b-2512 |
| Mistral Large 4 Preview | no confirmado contra mistralai/mistral-large-4-0-20261006 |

## Para aplicar las decisiones

Marcar la columna **Mismo?** con `si` / `no`. Los pares confirmados se convierten en un mapa `nombre_en_la_fuente -> canonical_slug` que `merge_benchmarks` consulta **antes** de recurrir a `match_key`, de modo que la clave conservadora sigue siendo el default.
