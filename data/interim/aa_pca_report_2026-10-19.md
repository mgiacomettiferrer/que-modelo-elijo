# PCA de las features de clustering

- Entrada: `aa_tabla_zscore_2026-10-19.parquet`
- Filas: 24 | variables originales: 6
- Componentes retenidos: 2
- Las features ya venian normalizadas, asi que esto equivale al PCA de la
  matriz de correlacion.

## Varianza por componente

| Componente | Autovalor | Varianza | Acumulada |
|---|---:|---:|---:|
| PC1 ** | 4.195 | 0.670 | 0.670 |
| PC2 ** | 0.872 | 0.139 | 0.809 |
| PC3 | 0.617 | 0.099 | 0.908 |
| PC4 | 0.311 | 0.050 | 0.957 |
| PC5 | 0.148 | 0.024 | 0.981 |
| PC6 | 0.119 | 0.019 | 1.000 |

Los 2 componentes retenidos conservan **80.9%** de la varianza. El resto (19.1%) se descarta.

## Cargas (que mide cada componente)

| Feature | PC1 | PC2 |
|---|---:|---:|
| speed_tok_s | -0.302 | +0.789 |
| latency_ttft_s | +0.383 | +0.579 |
| reasoning | +0.434 | -0.055 |
| coding | +0.415 | -0.132 |
| agentic | +0.457 | +0.115 |
| professional | +0.438 | +0.097 |

## Coordenadas de cada modelo

| Modelo | Proveedor | PC1 | PC2 |
|---|---|---:|---:|
| Claude Opus 5.5 (Max, Default Fallback) | Anthropic | +3.40 | +0.76 |
| Claude Sonnet 5.5 (Max, Default Fallback) | Anthropic | +2.76 | +1.15 |
| Claude Fable 5.1 (Max, Default Fallback) | Anthropic | +2.61 | +0.15 |
| GPT-6 Astra (Max) | OpenAI | +2.33 | +0.63 |
| GPT-6.1 Sol (Max) | OpenAI | +2.16 | +0.39 |
| Muse Wonder (Max) | Meta | +2.14 | +0.59 |
| MiMo-V2.6-Pro | Xiaomi | +0.88 | -1.30 |
| Grok 4.7 (Xhigh) | SpaceXAI | +0.73 | -0.05 |
| Qwen3.8 Max (0902) | Alibaba | +0.61 | -1.34 |
| Claude Haiku 5.5 (Max) | Anthropic | +0.55 | +1.55 |
| Kimi K3 (Max) | Kimi | +0.21 | -1.51 |
| GLM-5.3 (Max) | Z AI | +0.01 | -0.79 |
| Step 5 Preview | StepFun | -0.09 | -0.81 |
| GPT-6 Luna (Max) | OpenAI | -0.14 | +0.62 |
| DeepSeek V4.1 Flash 1017 (Max) | DeepSeek | -0.23 | +0.03 |
| Gemini 3.8 Flash (High) | Google | -0.27 | +0.37 |
| GLM-5.3-Flash | Z AI | -0.40 | -0.80 |
| Mistral Large 4 Preview | Mistral | -0.62 | -0.94 |
| Muse Spark Open (Xhigh) | Meta | -1.11 | -0.57 |
| Qwen3.8 27B (Xhigh) | Alibaba | -1.50 | -1.23 |
| Beam 1.0 | Reflection | -3.19 | +0.39 |
| Inkling (Xhigh) | Thinking Machines | -3.27 | +0.23 |
| Nemotron 3.5 Super VL | NVIDIA | -3.71 | +0.67 |
| K2 Horizon 375B A23B | Institute of Foundation Models | -3.88 | +1.81 |
