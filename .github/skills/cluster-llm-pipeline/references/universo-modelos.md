# Universo de modelos

Define **qué modelos son los puntos** del clustering y del scatter. La matriz tiene que tener **entre 41 y 100 puntos**: con menos de 40 el clustering es inestable y el artículo queda pobre; con más de 100 el scatter se vuelve ilegible y entran modelos irrelevantes.

## Reglas de selección

1. **Ventana**: solo modelos lanzados en los últimos 12 meses respecto de la fecha de corte.
2. **Uno por (proveedor, línea de familia)**, siempre el más nuevo de esa línea. Líneas distintas del mismo proveedor **sí** entran: Opus / Sonnet / Haiku; Astra / Sol / Luna / Terra; Argon / Flash / Flash-Lite; GLM / GLM Flash.
3. **Descartar lo publicado hace menos de 1 semana**: todavía tiene pocas pruebas cargadas.
4. **Solo modelos de texto generalistas**: aplicar la sección "Exclusiones" antes de contar.
5. **Piso obligatorio**: el modelo mejor posicionado de cada laboratorio de la tabla "Laboratorios que deben estar" tiene que estar presente. Esta regla **tiene prioridad sobre las reglas 2 y 3**: si el flagship de un laboratorio obligatorio es el único de su línea o tiene menos de una semana, entra igual. En ese caso sus benchmarks faltantes se declaran con el indicador `<feature>_missing`, no se imputan ni se descartan.
6. **Rango**: ajustar hasta caer en 41-100 aplicando "Relleno y recorte".

## Laboratorios que deben estar

Entrada **curada por el autor** y congelada a la fecha de corte. No se deriva del dataset: "tamaño y presencia en las noticias" no es medible con nuestras fuentes. El `AI Index` es el Artificial Analysis Intelligence Index del mejor modelo de cada laboratorio y sirve como **orden**, no como filtro automático.

| # | Laboratorio | Modelo mejor posicionado | AI Index |
|---|---|---|---|
| 1 | Anthropic | Claude Opus 5.5 — max con fallback | 58 |
| 2 | Meta | Muse Wonder Full — max | 56 |
| 3 | OpenAI | GPT-6 Astra — max | 53 |
| 4 | Google | Gemini 4 Argon — high | 53 |
| 5 | SpaceXAI | Grok 4.7 — xhigh | 46 |
| 6 | Xiaomi | MiMo-V2.6-Pro | 46 |
| 7 | Alibaba | Qwen3.8 Max — 0902 | 45 |
| 8 | Z AI | GLM-5.3 — max | 45 |
| 9 | StepFun | Step 5 Preview | 44 |
| 10 | Kimi / Moonshot AI | Kimi K3 — max | 44 |
| 11 | InclusionAI | Ling 3.1 Flash | 41 |
| 12 | DeepSeek | DeepSeek V4.1 Flash — max | 39 |
| 13 | Mistral AI | Mistral Large 4 Preview | 38 |
| 14 | Sapiens AI | Agnes 2.5 Pro Beta | 35 (estimado) |
| 15 | China Mobile | JT-4.1 Flash 236B A21B | 34 |
| 16 | Motif Technologies | Motif 3 | 34 (estimado) |
| 17 | Institute of Foundation Models | K2 Horizon 375B A23B | 31 |
| 18 | Reflection | Beam 1.0 | 30 |
| 19 | MiniMax | MiniMax-M3 | 29 |
| 20 | Nex AGI | Nex-N2-Pro | 28 (estimado) |

Los "(estimado)" son los que AA publica con asterisco: score parcial, no verificado completo. Al citarlos en el artículo, aclararlo.

## Relleno y recorte

**Si quedan menos de 41 puntos:**

- Agregar la segunda línea de familia de los laboratorios grandes (Sonnet 5.5 y Haiku 5.5 de Anthropic, Flash de Google, Luna y Terra de OpenAI, GLM Flash de Z.ai, Qwen3.8 Flash de Alibaba, Gemini Flash de Google).
- Sumar el siguiente escalón de proveedores, que ya aparece con `AI Index` razonable: Upstage, Multiverse Computing, NVIDIA, Tencent, Thinking Machines, Baidu, Amazon, IBM, LG AI Research, Naver, Microsoft, Nous Research, Ai2, Cohere, Poolside, Reka AI, Liquid AI, OpenBMB, Sarvam, Arcee AI, Inception, Celeris, Meta (Spark), Alibaba (Qwen3.8 27B / 2.4T), DeepSeek (V4 Pro).

**Si superan los 100 puntos**, recortar en este orden:

1. Duplicados de familia que no aportan un eje nuevo (dos versiones casi idénticas del mismo proveedor).
2. Los de menor `AI Index` cuyo proveedor ya está representado por otro modelo.
3. Nunca sacar un laboratorio de la tabla obligatoria.

## Exclusiones

Fuera del universo aunque estén en el catálogo de OpenRouter:

- **Routers y aliases**: `openrouter/auto*`, `openrouter/fusion`, `openrouter/pareto-*`, `openrouter/free`, `~*/…-latest`, `nvidia/switchyard`, `typesafe/jev-router`. No son modelos.
- **Guardrails y clasificadores**: `*-content-safety`, `llama-guard-*`, `gpt-oss-safeguard-*`.
- **Modelos de una sola tarea**: apply/patch de código (`morph-v3-*`, `relace-*`), extracción (`schematron-*`), resumen (`scaledown/summarize`), traducción (`hy-mt2-*`).
- **Imagen / audio / música puros**: `nano-banana*`, `*-image*`, `gpt-image*`, `gpt-audio*`, `lyria-*`.
- **Roleplay y narrativa**: `aion-*`, `cydonia-*`, `skyfall-*`, `euryale-*`, `magnum-*`, `unslopnemo-*`, `mythomax-*`, `venice/uncensored`.
- **Variantes del mismo modelo**: `:free`, `:batch`, `:nitro`, `:thinking`, `:extended` y snapshots con fecha.
- **Embeddings y rerank**.

Desempate: si un modelo tiene datos en menos de dos fuentes (`src_*`), probablemente no merece un punto — `row_confidence` bajo. Se excluye o se declara su faltante.

## Verificación antes de clusterizar

- [ ] `40 < N ≤ 100`
- [ ] los 20 laboratorios obligatorios están presentes
- [ ] ninguna violación de "Exclusiones"
- [ ] todos dentro de la ventana de 12 meses
- [ ] cada punto tiene `row_confidence` aceptable o su faltante declarado
- [ ] la lista final (`canonical_slug`, proveedor, familia, fecha de lanzamiento) queda **congelada** en `data/interim/universo_<fecha>.csv`

Congelar la lista es lo que hace reproducible el clustering: si el universo cambia, cambian los clusters y el artículo deja de ser verificable.
