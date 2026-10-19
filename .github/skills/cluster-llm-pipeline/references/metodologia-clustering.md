# Normalización y clustering

## Normalización

Objetivo: que la distancia euclídea entre modelos refleje diferencias reales y no diferencias de unidad o de cola.

**El clustering se hace solo con dos bloques: rendimiento y calidad.** Todo lo demás —capacidad, precio, modalidades, mercado, procedencia, parámetros, descargas— es metadata: se muestra, se filtra o se grafica, pero **no entra en la distancia**.

### Features de clustering

| Feature | Transformación | Motivo |
|---|---|---|
| `speed_tok_s` | winsor → `RobustScaler` | rendimiento; escala acotada |
| `latency_ttft_s` | winsor → `RobustScaler` | rendimiento; escala acotada |
| un benchmark por dimensión | rank percentil → `RobustScaler` | ver *Una feature por dimensión* |

**Una feature por dimensión.** El eje agregado **no** entra en la distancia: promedia ranks de benchmarks que no cubren a los mismos modelos, así que dos filas con el mismo valor de eje no son la misma medición. Cada dimensión se representa con **un solo** benchmark: el de menos nulos, medido sobre el universo. Una dimensión sin ningún dato queda fuera de la matriz.

La elección se recalcula en cada corrida y queda registrada en `data/interim/dimension_selection.json` junto con la cobertura de cada candidato. Sin ese registro el clustering deja de ser reproducible: si cambia la cobertura, cambia la feature.

Efecto lateral útil: la selección es sensible a la cobertura, no a la importancia aparente. En el corte 2026-10-16 eligió `finance_agent_v2_pct` para `professional` por encima de `legal_bench_pct`, porque LegalBench retenía 16 modelos del universo contra 28.

### Metadata y canales visuales (NO entran en la distancia)

| Columna | Uso | Transformación |
|---|---|---|
| `context_length`, `max_output_tokens` | capacidad; filtro y etiqueta | crudo |
| `is_open_weights`, `supports_*` | modalidad; define subconjuntos de análisis | crudo |
| `n_providers` | mercado; disponibilidad | crudo |
| `src_*`, `row_confidence` | procedencia; auditoría del match entre fuentes | crudo |
| `params_total`, `hf_downloads` | tamaño y popularidad; etiqueta, no distancia | crudo |
| `weighted_cost_usd_per_mtok` | **tamaño del punto** en el scatter PC1×PC2 | `log1p`, y **área** ∝ costo |

Reglas:

- **RobustScaler** (mediana/IQR) como default. Usar z-score solo si se justifica y se documenta.
- Winsorizar antes de escalar; registrar los cuantiles usados.
- Faltantes → mediana + columna `<feature>_missing` (0/1). Nunca imputar sin dejar el indicador.
- Booleans (`supports_*`, `is_open_weights`) se usan tal cual (0/1) o definen subconjuntos de análisis, no distancias.
- Nunca promediar índices de fuentes distintas. Si hace falta una "calidad" combinada, promediar **ranks** y documentarlo.
- `models_scaled.parquet` lleva **solo las features de clustering** (rendimiento + los ejes de calidad). El precio y el resto de la metadata quedan crudos y se usan en el paso de figura, no en la matriz que recibe PCA/KMeans.

### Agregación por dimensión (solo para el reporte)

Los `quality_*` se siguen calculando, pero **no son features**: sirven para describir cada dimensión en el artículo. Si se metieran en la matriz de distancia, la calidad pesaría una vez por benchmark y el rendimiento dos veces en total, y además el promedio mezclaría mediciones distintas.

1. Llevar cada benchmark crudo a **rank percentil** sobre el universo.
2. Promediar los ranks disponibles de cada dimensión → `quality_<dim>`.
3. Guardar `<dim>_n_sources`: cuántos benchmarks aportaron en ese modelo.
4. Si un modelo no tiene ningún benchmark de una dimensión, queda nulo con `_n_sources = 0`. Nunca completar con la mediana sin marca.

`intelligence_index` **no** entra como feature: es un compuesto de 10 evaluaciones que ya están repartidas entre los ejes, y usarlo además de sus componentes cuenta doble. Se conserva como métrica de reporte y como orden del universo de modelos.

### Una versión y un host por benchmark

Los benchmarks se rehacen: cambian los ítems, el prompt, el scoring o el conjunto de tareas. Los puntajes de dos versiones del mismo benchmark **no son comparables y no se mezclan nunca**.

1. **Un slot = una versión.** El eje se arma con una sola versión por benchmark, fijada con la fecha de corte. `terminal_bench_4_0_pct` y `terminal_bench_2_1_pct` son dos columnas distintas, no dos fuentes de lo mismo.
2. **Un slot = un host.** El mismo benchmark corrido por dos hosts da números distintos, porque cada uno usa su plantilla de prompt, su scoring y su configuración de esfuerzo. `Terminal-Bench 4.0` lo publican AA (32 modelos) y Vals (48 modelos) con protocolos propios: se elige **uno** y no se promedian.
3. **Un modelo sin esa versión queda faltante.** Nunca se rellena con la versión anterior: `Terminal-Bench 2.0` no cubre el hueco de `4.0`.
4. **La versión va en el nombre de la columna** (`swe_bench_verified_pct`, `mmlu_pro_pct`, `livebench_2_0_*`), para que el número sea auditable sin abrir el código.
5. **Migrar es reemplazar, no promediar.** Al adoptar una versión nueva se recalcula la columna entera. Mezclar la vieja con la nueva dentro del mismo eje es el error más fácil de cometer y el más difícil de detectar.
6. **Cambio de nombre ≠ misma prueba.** `MMLU` → `MMLU-Pro`, `GPQA` → `GPQA Diamond`, `SWE-bench` → `SWE-bench Verified`, `OSWorld` → `OSWorld-Verified` y `AIME 2024` → `AIME 2025` son tests distintos.
7. **La variante de esfuerzo también fija el puntaje.** Un mismo modelo puntúa distinto en `(max)`, `(high)` y `(xhigh)`. Se elige **una** configuración por modelo, se declara en la fila, y no se mezclan esfuerzos dentro de un eje.

**Efecto sobre la cobertura**: el conteo de modelos se hace **por versión y por host**, no por familia. "Terminal-Bench" no tiene 32+48 modelos; cada combinación versión-host tiene los suyos.

## Reducción y clustering

1. **PCA** sobre la matriz escalada de features de clustering (rendimiento + ejes de calidad). Guardar `explained_variance_ratio` y elegir los componentes que expliquen ≥80%. Usar la matriz reducida solo si mejora silhouette; si no, clusterizar sobre todas las features escaladas.
2. **KMeans** (baseline, `random_state=42`, `n_init=10`). Barrido `k = 2..12`.
   - Elegir `k` con el codo de inercia + máximo silhouette; priorizar interpretabilidad.
   - Rango razonable con 41-100 puntos: **3-8 clusters**; el artículo suele funcionar mejor con 4-6.
3. **HDBSCAN** (contraste): detecta clusters de forma arbitraria y marca outliers (`-1`). No forzarlo a tener el mismo `k`; sirve para validar que los grupos de KMeans no son artefactos y para identificar modelos inclasificables.
4. **Ward jerárquico** (opcional): útil para el dendrograma que se muestra en el artículo y para justificar el corte.

## Evaluación

| Métrica | Qué dice | Umbral orientativo |
|---|---|---|
| Silhouette | separación vs cohesión | > 0.25 aceptable en este dataset heterogéneo |
| Davies-Bouldin | menor es mejor | comparar entre candidatos, sin valor absoluto |
| Calinski-Harabasz | mayor es mejor | comparar entre candidatos |
| Tamaño mínimo de cluster | no dejar clusters de 1-2 modelos | ≥ 5 modelos; con N > 60, ≥ 8 |

Escribir la comparación completa en `data/processed/cluster_metrics.json` (una entrada por `k`, con las tres métricas y el tamaño de cada cluster).

## Etiquetado e interpretación

Un cluster sin nombre legible no sirve para el artículo.

1. Calcular el centroide en el espacio **escalado** para las features más discriminantes (mayor varianza entre centroides).
2. Traducir el centroide a una etiqueta corta en español, **usando solo atributos técnicos** del grupo: p. ej. "contexto gigante (>1M)", "razonamiento de frontera", "rápidos de gama media", "open-weights autohospedables", "multimodales con audio y video", "especializados en código". Una etiqueta como "baratos y rápidos" **no** es válida: el precio no es una feature del clustering.
3. Listar 3-5 features que más distinguen al cluster (mayor `|centroide|` estandarizado) — son el argumento del artículo.
4. Verificar el rango de las features técnicas en unidades crudas (contexto, velocidad, latencia, índices). El precio **no** sirve para validar el clustering: que un cluster mezcle tiers de precio es un resultado esperado y publicable, no un error de normalización.

## Representación (2ª etapa): scatter PC1×PC2

Terminado el clustering, se representa el resultado en el plano de los dos primeros componentes principales.

1. Ajustar **PCA solo con la matriz de features técnicas** — nunca con el precio.
2. Scatter con **PC1 en el eje x y PC2 en el eje y**; color = `cluster_label`.
3. **Tamaño del punto = costo ponderado** (ver `AGENTS.md` → *Costo ponderado*). Reglas:
   - Mapear **área** ∝ costo, no radio: en `matplotlib`, `s` ya es área, así que `s = k * valor`.
   - Con costos de cola larga, mapear `log1p(costo)`; si no, los modelos gratis desaparecen y los premium tapan el gráfico.
   - Poner un piso de tamaño para que un modelo gratis siga siendo visible.
   - Declarar en el pie los pesos usados (`60/20/20` u `80/20`) y la fecha de consulta de precios. Un modelo sin costo disponible se dibuja con tamaño mínimo y marca aparte, nunca con tamaño cero.
4. Etiquetar solo los puntos que importan (extremos y líderes de cada cluster); el resto sin leyenda, para no saturar.
5. Reportar en el pie: `explained_variance_ratio` de PC1 y PC2, las features con mayor peso (loadings) en cada componente, los pesos del costo ponderado y la fecha de consulta de precios.

**Lo que la figura tiene que dejar ver:** si los clusters se separan por capacidad técnica y el tamaño (precio) **no** sigue ese orden, ese es el hallazgo del artículo — grupos con capacidad comparable a precios muy distintos. Si el tamaño crece monótonamente con PC1, entonces la capacidad es casi un proxy del precio y hay que decirlo explícitamente.

## Determinismo y artefactos

- `random_state=42` en PCA, KMeans, train/test de cualquier cosa aleatoria.
- Ordenar filas por `canonical_slug` antes de clusterizar para que los ids sean estables entre corridas.
- Artefactos: `data/processed/llm_features.parquet` (contrato), `data/processed/cluster_metrics.json`, `data/processed/cluster_profiles.csv`, `outputs/figures/pca_scatter.png` (PC1×PC2, color = cluster, **tamaño = precio**), `outputs/figures/silhouette_k.png`, `outputs/figures/cluster_heatmap.png`.
