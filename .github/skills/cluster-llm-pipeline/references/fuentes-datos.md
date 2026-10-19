# Fuentes de datos

Tres fuentes principales + HuggingFace como enriquecimiento. Verificar endpoints y campos al momento de la ingesta: las APIs cambian. Toda fila final debe poder rastrearse hasta su fuente original.

## OpenRouter — fuente base (catálogo y precio)

- Endpoint: `GET https://openrouter.ai/api/v1/models` (sin auth). Proveedor: `GET /api/v1/models/{author}/{slug}/endpoints` para precios por proveedor.
- Estructura: `{ "data": [ { ... } ] }`.
- Campos útiles: `id`, `canonical_slug`, `hugging_face_id`, `name`, `created`, `context_length`, `architecture.{input_modalities,output_modalities,tokenizer,instruct_type}`, `pricing.{prompt,completion,request,input_cache_read,input_cache_write}`, `top_provider.{context_length,max_completion_tokens,is_moderated}`, `supported_parameters` (p. ej. `tools`, `reasoning`, `structured_outputs`), `per_request_limits`.
- **Precio**: `pricing.prompt` y `pricing.completion` vienen como **string en USD por token** → `float(x) * 1_000_000` para `*_usd_per_mtok`.
- Es la mejor fuente para: cobertura, precio, contexto, modalidades, tool-calling, y como clave de unión (`hugging_face_id`, nombre normalizado).

## Artificial Analysis — calidad y rendimiento de serving

- Endpoint: `GET https://artificialanalysis.ai/api/v2/data/llms/models` con header `x-api-key: <AA_API_KEY>`. Requiere registro; hay tier gratuito con límites. Verificar el path exacto vigente.
- Campos útiles: `name`, `slug`, `model_creator`, `release_date`, `evaluations` (índices compuestos de inteligencia/código/matemática), `pricing` (input, output y blended por 1M tokens), mediana de `output_tokens_per_second`, mediana de `time_to_first_token`.
- Mapear a: `intelligence_index`, `coding_index`, `math_index`, `speed_tok_s`, `latency_ttft_s`.
- Es la mejor fuente para: velocidad, latencia y un índice de calidad comparable **dentro de la propia fuente**.

## LMArena — preferencia humana (ELO)

- Fuente: leaderboard en `https://lmarena.ai/leaderboard`; datos históricos como dataset en HuggingFace (`lmarena-ai/arena-human-preference-*`) o el leaderboard space.
- Campos útiles: rating/ELO global y por categoría (hard prompts, coding, math, creative writing, longer query, multi-turn), rank, intervalos de confianza, votos.
- Mapear a: `arena_elo` (y, si se usan, `arena_elo_<categoria>`).
- Es la mejor fuente para: preferencia percibida por humanos. **El ELO no es comparable con el Intelligence Index.**

## HuggingFace — enriquecimiento

- Herramientas: `huggingface_hub.HfApi.model_info(repo_id)` y la librería `datasets`.
- Unión: `OpenRouter.hugging_face_id` → `HfApi.model_info`. Con eso se obtiene: parámetros totales (`safetensors.total`), `downloads`, `likes`, `license`, `created_at`, `tags`.
- Mapear a: `params_total`, `hf_downloads`, `hf_likes`, `license`, y de ahí derivar `is_open_weights`.
- Nota: el ranking tipo "Open LLM Leaderboard" fue archivado; preferir datasets activos y verificar vigencia antes de usarlos como benchmark.

## Reglas de unión

1. **Clave primaria**: `canonical_slug` de OpenRouter, tras quitar sufijos de variante.
2. **Unión por nombre normalizado** cuando no hay `hugging_face_id`: minúsculas, sin espacios ni puntuación, sin sufijos de fecha/proveedor. Guardar el score de match y marcar los dudosos como `row_confidence` bajo.
3. **Dirección de la unión**: `left join` desde OpenRouter. Un modelo que no está en OpenRouter no entra (es donde el usuario efectivamente puede usar el modelo).
4. Cobertura desigual es esperable: reportar el porcentaje de filas con datos por fuente en `clean_report.md`.
5. Cada columna derivada de una fuente externa debe dejar su bandera `src_*`.

## Criterios de selección para el artículo

El artículo responde "¿qué modelo uso si mi criterio es X?". Features por criterio:

**Aviso**: la fila "Costo" es un criterio de decisión del lector, **no** una feature de clustering. El clustering se hace solo con atributos técnicos; el precio se comunica como tamaño del punto en el scatter PC1×PC2.

| Criterio del lector | Features que lo representan |
|---|---|
| Costo | `weighted_cost_usd_per_mtok` (fórmula en `AGENTS.md` → *Costo ponderado*) |
| Contexto / documentos largos | `context_length` |
| Velocidad / baja latencia (chat, agentes) | `speed_tok_s`, `latency_ttft_s` |
| Razonamiento y código | `intelligence_index`, `coding_index`, `math_index` |
| Preferencia percibida | `arena_elo` |
| Privacidad / autohospedaje | `is_open_weights`, `license`, `params_total` |
| Multimodalidad y tools | `supports_vision`, `supports_audio`, `supports_tools` |
| Confiabilidad operativa | `n_providers` |

## Dimensiones de benchmark

Esta tabla es la versión corta. El mapa completo de dimensiones (con los benchmarks concretos por eje, el mapeo caso de uso → ejes y los gaps de MCP / PC-navegador / Excel) está en [`./dimensiones-benchmarks.md`](./dimensiones-benchmarks.md).
