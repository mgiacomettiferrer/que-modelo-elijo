---
name: cluster-llm-pipeline
description: 'Pipeline end-to-end para investigar, limpiar, normalizar y clusterizar modelos LLM y publicar el resultado como artículo en Markdown y post de LinkedIn. Usalo cuando pidan "clusterizar LLMs", "agrupar modelos por criterio", "elegir un LLM según criterios", "actualizar el dataset de modelos", "normalizar features de modelos", "generar el artículo de clusters", "escribir el post de LinkedIn de LLMs", o cuando mencionen las etapas research / clean / normalize / cluster / publish de este repo.'
argument-hint: '[etapa: research|clean|normalize|cluster|publish|all]'
---

# Pipeline de clusters de LLM

Convierte datos crudos de modelos LLM (precio, contexto, rendimiento, calidad) en una tabla clusterizada y luego en un artículo + post de LinkedIn que recomienda qué modelo usar según el criterio del lector.

## Cuándo usarlo

- Ingestar o refrescar datos de modelos desde OpenRouter, Artificial Analysis, LMArena y HuggingFace.
- Limpiar, deduplicar o normalizar el dataset de modelos.
- Correr o ajustar el clustering y evaluar la calidad de los grupos.
- Redactar/actualizar el artículo o el post de LinkedIn a partir de los clusters.

**No** lo uses para escribir código de la aplicación ni para responder consultas puntuales sobre un modelo: para eso alcanza con responder directo.

## Preflight

1. Leer `AGENTS.md` para el contrato de datos y las convenciones.
2. Verificar que existe `requirements.txt` y que el entorno está configurado.
3. Confirmar que `data/raw/` tiene un snapshot del día; si no, correr `research` primero.
4. Al terminar cada etapa, validar la salida contra el contrato de datos antes de avanzar a la siguiente.

## Etapas

### 1. research

Objetivo: un único snapshot crudo y trazable.

1. Consultar las fuentes según [`./references/fuentes-datos.md`](./references/fuentes-datos.md): OpenRouter (base), Artificial Analysis (calidad/latencia), LMArena (ELO por categoría), HuggingFace (params, licencia, popularidad).
2. Guardar cada respuesta cruda tal cual en `data/raw/models_<YYYY-MM-DD>.json` con un bloque `_meta` (`source`, `url`, `fetched_at`, `n_rows`).
3. No transformar ni filtrar en esta etapa. Si una fuente falla, registrar el error en `_meta.errors` y seguir con las demás.

### 2. clean

Objetivo: una fila por modelo comparable.

1. Parsear precios de string (USD/token) → float en USD por 1M tokens.
2. Deduplicar por `canonical_slug`; descartar variantes `:free`, `:nitro`, `:thinking`, `:extended`, aliases y snapshots con fecha, conservando el modelo canónico.
3. Descartar no-texto (embeddings, moderación, rerank, image-only) y modelos deprecados sin reemplazo.
4. Normalizar nombres de proveedor y familia (`anthropic`, `openai`, `google`, `meta`, `mistral`, …).
5. **Seleccionar el universo**: aplicar las reglas de [`./references/universo-modelos.md`](./references/universo-modelos.md) y verificar que quede en **41-100 puntos**, con los 20 laboratorios obligatorios presentes. Congelar la lista en `data/interim/universo_<fecha>.csv`.
6. Reportar el embudo: filas por fuente → tras dedupe → tras filtros → universo final, en `data/interim/clean_report.md`.

### 3. normalize

Objetivo: features listas para distancia euclídea.

1. `log1p` sobre las features de cola larga: `price_in_usd_per_mtok`, `price_out_usd_per_mtok`, `context_length`.
2. Escalar con `RobustScaler` (mediana/IQR) — es más estable que z-score ante outliers de precio.
3. Winsorizar a p1/p99 antes de escalar y dejarlo documentado.
4. Faltantes: imputar mediana **más** columna indicadora `<feature>_missing`; nunca imputar en silencio.
5. No mezclar índices de fuentes distintas en una sola feature (ver gotchas de `AGENTS.md`). Si hace falta una "calidad" combinada, usar el **rank percentil**, no el valor crudo.

Detalle de fórmulas y umbrales: [`./references/metodologia-clustering.md`](./references/metodologia-clustering.md).

### 4. cluster

Objetivo: grupos interpretables y una recomendación por criterio.

1. Reducir con PCA (guardar varianza explicada) y correr KMeans como baseline. La matriz de entrada lleva **solo atributos técnicos**: el precio no entra en la distancia.
2. Elegir `k` con codo + silhouette; contrastar con HDBSCAN para detectar outliers.
3. Evaluar con silhouette, Davies-Bouldin y Calinski-Harabasz; guardar la comparación en `data/processed/cluster_metrics.json`.
4. Etiquetar cada cluster con un nombre legible derivado del perfil de centroides, **usando solo features técnicas** ("contexto gigante", "razonamiento de frontera", "open-weights autohospedables", …) y listar las features más discriminantes.
5. **Representación (2ª etapa)**: scatter PC1×PC2, color = cluster y **tamaño del punto = costo ponderado** (área ∝ costo, `log1p`; pesos y fecha de precios en el pie). Reportar `explained_variance_ratio` y loadings.
6. Emitir `data/processed/llm_features.parquet` con `cluster_id` y `cluster_label`, y las figuras a `outputs/figures/`.

### 5. publish

Objetivo: artículo + post.

1. Artículo en `outputs/article/clusters-llm.md`: problema → método y fuentes → tabla de clusters → recomendación por criterio → limitaciones → fecha de corte. El costo se muestra con la etiqueta, los pesos y la fecha de precios que exige `AGENTS.md` → *Costo ponderado*.
2. Post en `outputs/article/linkedin.md` usando [`./assets/plantilla-linkedin.md`](./assets/plantilla-linkedin.md).
3. Cerrar con una tabla de recomendaciones del tipo "si tu criterio es X, mirá el cluster Y (modelos A, B)".
4. Revisar la prosa contra señales de escritura IA (contrastes "no X sino Y", tríadas forzadas, cierres de una línea, superlativos) y corregir antes de dar por terminado.

## Quality gates

- [ ] Cada etapa valida las columnas del contrato de datos antes de escribir salida.
- [ ] `data/raw/` intacto y con `_meta` completo.
- [ ] Todo número del artículo es reproducible desde `src/`.
- [ ] Se declaran las limitaciones (faltantes, cobertura desigual, fuentes con fechas distintas).
- [ ] Español para prosa, inglés para código y columnas.

## Referencias

- [`./references/universo-modelos.md`](./references/universo-modelos.md) — qué modelos son los puntos: ventana, una familia por proveedor, 41-100 puntos, laboratorios obligatorios y exclusiones.
- [`./references/fuentes-datos.md`](./references/fuentes-datos.md) — endpoints, campos y uniones entre fuentes.
- [`./references/dimensiones-benchmarks.md`](./references/dimensiones-benchmarks.md) — qué mide cada benchmark, mapeo caso de uso → ejes y qué dimensiones no podemos medir.
- [`./references/metodologia-clustering.md`](./references/metodologia-clustering.md) — normalización, métricas y etiquetado.
- [`./assets/plantilla-linkedin.md`](./assets/plantilla-linkedin.md) — estructura del post.
