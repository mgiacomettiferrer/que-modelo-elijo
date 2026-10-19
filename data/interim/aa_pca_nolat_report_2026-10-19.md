# PCA de las features de clustering

- Entrada: `aa_tabla_zscore_2026-10-19.parquet`
- Filas: 24 | variables originales: 5
- Variables: `speed_tok_s_z`, `reasoning_z`, `coding_z`, `agentic_z`, `professional_z`
- Excluidas: `data_z`, `latency_ttft_s_z`
- Componentes retenidos: 2
- Las features ya venian normalizadas, asi que esto equivale al PCA de la
  matriz de correlacion.

## Varianza por componente

| Componente | Autovalor | Varianza | Acumulada |
|---|---:|---:|---:|
| PC1 ** | 3.658 | 0.701 | 0.701 |
| PC2 ** | 0.708 | 0.136 | 0.837 |
| PC3 | 0.427 | 0.082 | 0.919 |
| PC4 | 0.303 | 0.058 | 0.977 |
| PC5 | 0.121 | 0.023 | 1.000 |

Los 2 componentes retenidos conservan **83.7%** de la varianza. El resto (16.3%) se descarta.

## Cargas (que mide cada componente)

| Feature | PC1 | PC2 |
|---|---:|---:|
| speed_tok_s | -0.357 | +0.868 |
| reasoning | +0.476 | +0.321 |
| coding | +0.457 | +0.205 |
| agentic | +0.485 | +0.277 |
| professional | +0.450 | -0.157 |

## Coordenadas de cada modelo

| Modelo | Proveedor | PC1 | PC2 |
|---|---|---:|---:|
| Claude Opus 5.5 (Max, Default Fallback) | Anthropic | +2.92 | +0.94 |
| Claude Fable 5.1 (Max, Default Fallback) | Anthropic | +2.32 | +0.16 |
| Claude Sonnet 5.5 (Max, Default Fallback) | Anthropic | +2.29 | +1.14 |
| Muse Wonder (Max) | Meta | +2.09 | +0.82 |
| GPT-6 Astra (Max) | OpenAI | +1.87 | -0.37 |
| GPT-6.1 Sol (Max) | OpenAI | +1.74 | -0.67 |
| MiMo-V2.6-Pro | Xiaomi | +1.23 | -0.42 |
| Qwen3.8 Max (0902) | Alibaba | +0.95 | -1.11 |
| Grok 4.7 (Xhigh) | SpaceXAI | +0.59 | -0.01 |
| Kimi K3 (Max) | Kimi | +0.52 | -1.28 |
| GLM-5.3 (Max) | Z AI | +0.35 | +0.44 |
| Step 5 Preview | StepFun | +0.24 | +0.11 |
| DeepSeek V4.1 Flash 1017 (Max) | DeepSeek | +0.14 | +1.18 |
| Claude Haiku 5.5 (Max) | Anthropic | -0.02 | +0.88 |
| GLM-5.3-Flash | Z AI | -0.11 | -0.28 |
| Mistral Large 4 Preview | Mistral | -0.30 | -0.78 |
| Gemini 3.8 Flash (High) | Google | -0.41 | -0.01 |
| GPT-6 Luna (Max) | OpenAI | -0.55 | -0.42 |
| Muse Spark Open (Xhigh) | Meta | -0.76 | -0.15 |
| Qwen3.8 27B (Xhigh) | Alibaba | -1.35 | -1.83 |
| Beam 1.0 | Reflection | -3.03 | +0.11 |
| Inkling (Xhigh) | Thinking Machines | -3.20 | -0.54 |
| Nemotron 3.5 Super VL | NVIDIA | -3.59 | +0.47 |
| K2 Horizon 375B A23B | Institute of Foundation Models | -3.94 | +1.63 |
