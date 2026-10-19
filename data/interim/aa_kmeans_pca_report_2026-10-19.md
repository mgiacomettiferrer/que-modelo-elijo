# KMeans sobre la tabla de Artificial Analysis

- Entrada: `aa_pca_nolat_2026-10-19.parquet`
- Filas: 24 | features: 2
- Features: `pc1`, `pc2`
- Excluida: `data_z` (16 de 24 valores; entrenar con ella costaba 8 modelos)
- KMeans: `random_state=42`, `n_init=10`

## Indicadores por k

| k | Inercia (WCSS) | Entre (BCSS) | Entre/Dentro | Var. explicada | Calinski-Harabasz | Davies-Bouldin | Silueta | Tamanos | Min | Cumple min 5 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 3 | 21.233 | 79.180 | 3.729 | 0.789 | 39.16 | 0.667 | 0.476 | 4/7/13 | 4 | no |
| 4 | 15.432 | 84.981 | 5.507 | 0.846 | 36.71 | 0.677 | 0.459 | 4/4/5/11 | 4 | no |
| 5 | 10.217 | 90.196 | 8.828 | 0.898 | 41.93 | 0.631 | 0.466 | 4/4/5/5/6 | 4 | no |
| 6 | 7.646 | 92.768 | 12.133 | 0.924 | 43.68 | 0.535 | 0.467 | 1/4/4/5/5/5 | 1 | no |

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
| 0 | 4 | pc1 bajo + pc2 alto | Beam 1.0 | Inkling (Xhigh) | K2 Horizon 375B A23B | Nemotron 3.5 Super VL |
| 1 | 7 | pc1 alto + pc2 alto | Claude Fable 5.1 (Max, Default Fallback) | Claude Opus 5.5 (Max, Default Fallback) | Claude Sonnet 5.5 (Max, Default Fallback) | GPT-6 Astra (Max) | GPT-6.1 Sol (Max) | MiMo-V2.6-Pro | Muse Wonder (Max) |
| 2 | 13 | pc2 bajo + pc1 bajo | Claude Haiku 5.5 (Max) | DeepSeek V4.1 Flash 1017 (Max) | GLM-5.3 (Max) | GLM-5.3-Flash | GPT-6 Luna (Max) | Gemini 3.8 Flash (High) | Grok 4.7 (Xhigh) | Kimi K3 (Max) | Mistral Large 4 Preview | Muse Spark Open (Xhigh) | Qwen3.8 27B (Xhigh) | Qwen3.8 Max (0902) | Step 5 Preview |

## Perfil de los centroides (media de z por feature)

| Cluster | pc1 | pc2 |
|---|---:|---:|
| 0 | -3.44 | +0.42 |
| 1 | +2.07 | +0.23 |
| 2 | -0.05 | -0.25 |
