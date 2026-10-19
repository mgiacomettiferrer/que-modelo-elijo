# KMeans sobre la tabla de Artificial Analysis

- Entrada: `aa_tabla_zscore_2026-10-19.parquet`
- Filas: 24 | features: 6
- Features: `speed_tok_s_z`, `latency_ttft_s_z`, `reasoning_z`, `coding_z`, `agentic_z`, `professional_z`
- Excluida: `data_z` (16 de 24 valores; entrenar con ella costaba 8 modelos)
- KMeans: `random_state=42`, `n_init=10`

## Indicadores por k

| k | Inercia (WCSS) | Entre (BCSS) | Entre/Dentro | Var. explicada | Calinski-Harabasz | Davies-Bouldin | Silueta | Tamanos | Min | Cumple min 5 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 3 | 45.684 | 98.316 | 2.152 | 0.683 | 22.60 | 0.865 | 0.402 | 4/7/13 | 4 | no |
| 4 | 36.679 | 107.321 | 2.926 | 0.745 | 19.51 | 1.003 | 0.325 | 4/4/6/10 | 4 | no |
| 5 | 30.697 | 113.303 | 3.691 | 0.787 | 17.53 | 1.077 | 0.313 | 4/4/4/6/6 | 4 | no |
| 6 | 26.502 | 117.498 | 4.434 | 0.816 | 15.96 | 0.958 | 0.323 | 2/3/4/4/4/7 | 2 | no |

### Como leer el ratio entre/dentro

`BCSS / WCSS` mide cuanto de la dispersion total quedó entre clusters en vez
de dentro de ellos: mas alto es mejor. Pero **crece con k por construccion**
—cada cluster nuevo siempre explica algo mas—, asi que no sirve para elegir
k comparando valores crudos. Para eso esta Calinski-Harabasz, que es el mismo
cociente normalizado por los grados de libertad:

```
CH = (BCSS / (k - 1)) / (WCSS / (n - k))
```

Davies-Bouldin y la silueta van en la dirección contraria: mas bajo el
primero, mas alta la segunda.

## k elegido: **3**

Criterio: ningun k cumple el minimo por cluster; se toma la mejor silueta.

| Cluster | n | Etiqueta | Modelos |
|---|---:|---|---|
| 0 | 13 | latency_ttft_s bajo + speed_tok_s bajo | DeepSeek V4.1 Flash 1017 (Max) | GLM-5.3 (Max) | GLM-5.3-Flash | GPT-6 Luna (Max) | Gemini 3.8 Flash (High) | Grok 4.7 (Xhigh) | Kimi K3 (Max) | MiMo-V2.6-Pro | Mistral Large 4 Preview | Muse Spark Open (Xhigh) | Qwen3.8 27B (Xhigh) | Qwen3.8 Max (0902) | Step 5 Preview |
| 1 | 4 | reasoning bajo + speed_tok_s alto | Beam 1.0 | Inkling (Xhigh) | K2 Horizon 375B A23B | Nemotron 3.5 Super VL |
| 2 | 7 | latency_ttft_s alto + agentic alto | Claude Fable 5.1 (Max, Default Fallback) | Claude Haiku 5.5 (Max) | Claude Opus 5.5 (Max, Default Fallback) | Claude Sonnet 5.5 (Max, Default Fallback) | GPT-6 Astra (Max) | GPT-6.1 Sol (Max) | Muse Wonder (Max) |

## Perfil de los centroides (media de z por feature)

| Cluster | speed_tok_s | latency_ttft_s | reasoning | coding | agentic | professional |
|---|---:|---:|---:|---:|---:|---:|
| 0 | -0.42 | -0.44 | +0.08 | +0.08 | -0.21 | -0.18 |
| 1 | +1.66 | -0.92 | -1.70 | -1.55 | -1.38 | -1.46 |
| 2 | -0.17 | +1.34 | +0.82 | +0.74 | +1.19 | +1.16 |
