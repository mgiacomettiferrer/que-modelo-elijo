# Cluster de LLM

Proyecto de investigación y análisis de datos cuyo producto es un **artículo en Markdown** (`outputs/article/`) y su **post para LinkedIn**, sobre cómo agrupar modelos LLM en clusters y elegir cuál usar según distintos criterios (precio, contexto, velocidad, calidad, modalidad).

El detalle procedimental de cada etapa vive en el skill [`cluster-llm-pipeline`](./.github/skills/cluster-llm-pipeline/SKILL.md). Este archivo es solo el contexto del repo: no lo dupliques ahí.

## Pipeline (5 etapas)

| # | Etapa | Entrada | Salida |
|---|-------|---------|--------|
| 1 | research | APIs/fuentes externas | `data/raw/models_<fecha>.json` |
| 2 | clean | `data/raw/` | `data/interim/models_clean.parquet` |
| 3 | normalize | `data/interim/` | `data/interim/models_scaled.parquet` + `data/processed/llm_features.parquet` |
| 4 | cluster | `data/interim/models_scaled.parquet` | agrega `cluster_id` y `cluster_label` a `llm_features.parquet` + `outputs/figures/` |
| 5 | publish | `data/processed/` | `outputs/article/*.md` + `outputs/article/linkedin.md` |

**Restricción de tamaño**: el universo de modelos (los puntos del scatter) tiene que quedar entre **41 y 100**, e incluir el mejor modelo de cada laboratorio de referencia. Reglas en `.github/skills/cluster-llm-pipeline/references/universo-modelos.md`.

## Estructura

```
src/            scripts Python modulares, uno por etapa, + cli.py
src/aliases.py  mapa de alias revisado a mano (se consulta antes de match_key)
data/raw/       CRUDO INMUTABLE — nunca se sobrescribe ni se edita a mano
data/interim/   intermedio, regenerable
data/processed/ llm_features.parquet  (contrato de datos entre etapas)
outputs/figures/ figuras + el código que las generó
outputs/article/ artículo y post
```

## Contrato de datos

`data/processed/llm_features.parquet` es la interfaz entre etapas. Una fila = un modelo comparable (no una variante de proveedor). Columnas canónicas:

- Identidad: `model_id`, `canonical_slug`, `name`, `provider`, `family`, `release_date`, `hugging_face_id`
- Capacidad: `context_length`, `max_output_tokens`, `is_open_weights`
- Precio (USD por 1M tokens): `price_in_usd_per_mtok`, `price_out_usd_per_mtok`, `price_cache_read_usd_per_mtok`, `price_cache_write_usd_per_mtok`, `price_reasoning_usd_per_mtok` (nulo = misma tarifa que la salida)
- Precio por uso (USD por llamada, se informa aparte): `price_web_search_usd_per_call`
- Costo derivado: `weighted_cost_usd_per_mtok` (nulo si falta el precio de lectura de caché), `weighted_cost_profile` (`60/20/20` o `80/20`)
- Features booleanas: `supports_tools`, `supports_reasoning`, `supports_vision`, `supports_audio`
- Rendimiento: `speed_tok_s`, `latency_ttft_s`
- Calidad cruda (una columna por benchmark; catálogo en `references/dimensiones-benchmarks.md`): `arena_elo`, `intelligence_index`, `coding_index`, `math_index`, `livebench_2_0_*`, `vals_index_pct`, `swe_bench_verified_pct`, `bfcl_pct`, `terminal_bench_4_0_pct`, `legal_bench_pct`, `excel_modeling_pct`, `mmmu_pro_pct`, `aa_lcr_pct`, `ifbench_pct`
- Calidad agregada por dimension (**reporte, no feature**): `quality_general`, `quality_reasoning`, `quality_coding`, `quality_agentic`, `quality_professional`, `quality_data`, `quality_browser`, `quality_multimodal`, `quality_long_context`, `quality_instruction` + `<dim>_n_sources`
- Mercado: `n_providers`
- Procedencia: `src_openrouter`, `src_artificial_analysis`, `src_lmarena`, `src_hf`, `src_vals`, `src_livebench` (bool) + `row_confidence` (0-1)

**Features de clustering**: `speed_tok_s`, `latency_ttft_s` y **un benchmark por dimension**, el de menos nulos medida sobre el universo. Los ejes `quality_*` son reporte: promedian ranks de benchmarks que no cubren a los mismos modelos, asi que con cobertura parcial dos filas con el mismo valor no son la misma medicion. La eleccion se recalcula en cada corrida y se registra en `data/interim/dimension_selection.json`; una dimension sin datos queda fuera. Capacidad, precio, modalidades, mercado, procedencia, parametros y descargas son metadata o canales visuales y **no entran en la distancia**.

**No renombres ni agregues columnas sin actualizar esta tabla de contrato y el skill.**

## Comandos

Implementadas: instalar, ingesta, limpieza, normalizacion, reporte de nulos y revision de alias.
Pendientes: clustering y publicacion.

| Accion | Comando |
|---|---|
| Instalar | `pip install -r requirements.txt` |
| Ingesta | `python -m src.research --out data/raw/models_<fecha>.json` |
| Limpieza | `python -m src.clean --in data/raw/models_<fecha>.json [--benchmarks data/raw/benchmarks_<fecha>.json]` |
| Normalizacion | `python -m src.normalize --in data/interim/models_clean.parquet` |
| Reporte de nulos | `python -m src.report_nulls --in data/processed/llm_features.parquet` |
| Revision de alias | `python -m src.alias_review --in data/processed/llm_features.parquet --aa data/raw/benchmarks_aa_<fecha>.json --vals data/raw/benchmarks_vals_<fecha>.json --out data/interim/alias_candidates.md` |
| Dataset AA | `python -m src.aa_dataset --payload data/raw/aa_payload_<fecha>.txt` |
| Imputar (MICE) | `python -m src.impute_mice --in data/interim/models_scaled.parquet` |
| Scrape de leaderboard | `python -m src.page_parse --page data/interim/aa_page_<fecha>.txt --source aa --url <url> --out data/raw/benchmarks_aa_<fecha>.json` |
| Scrape de Vals | `python -m src.page_parse --page data/raw/vals_raw_<fecha>.json --source vals --out data/raw/benchmarks_vals_<fecha>.json` |
| Exportar datos para la web | `python -m src.web_export` (escribe `data/web/models.json` y `outputs/web/que-modelo-elijo/data/models.js`) |
| Articulo a PDF | `python -m src.article_pdf` (escribe `outputs/article/que-modelo-elijo-para-mi-agente.pdf`, que no se publica; requiere Chrome o Edge) |
| Clustering (pendiente) | `python -m src.cluster --in data/interim/models_scaled.parquet --k auto` |
| Publicar (pendiente) | `python -m src.publish --in data/processed/llm_features.parquet` |

El esquema canonico, los roles de cada columna y el mapa benchmark -> eje viven en `src/schema.py`, que es la fuente de verdad ejecutable.

## Convenciones

- **Idioma**: español para prosa y entregables; inglés para nombres de código, columnas y archivos.
- **Determinismo**: `random_state=42` en todo lo aleatorio; versiones pinneadas en `requirements.txt`; `data/raw/` es append-only con timestamp en el nombre.
- **Unidades**: precios siempre en USD por 1M tokens (sufijo `_usd_per_mtok`). Nunca dejar precios por token en columnas finales.
- **Escalas muy sesgadas**: `context_length` y las demás features de cola larga se transforman con `log1p` antes de escalar.
- **El precio no es feature de clustering**: se resume con la fórmula de la sección *Costo ponderado* y ese valor alimenta el tamaño del punto del scatter PC1×PC2, mapeado con `log1p` sobre el área.
- **Trazabilidad**: cada figura se genera por código versionado en `src/`; no se guardan imágenes hechas a mano.
- **Citas**: toda tabla, figura y número del artículo lleva fuente y fecha de corte.

## Costo ponderado

Métrica derivada para comparar el costo de serving en una base común. No es feature de clustering (ver *Convenciones*): se calcula, se muestra y alimenta el tamaño del punto del scatter.

### Fórmula

```
costo_ponderado = w_in × precio_entrada_sin_cache
                + w_cache × precio_lectura_cache
                + w_out × precio_salida
```

- **Con caché (default)**: `0,60` entrada · `0,20` lectura de caché · `0,20` salida.
- **Sin caché**: `0,80` entrada · `0,20` salida.

**Ejemplo**: entrada USD 2,00, lectura de caché USD 0,20, salida USD 10,00 →
`0,60×2,00 + 0,20×0,20 + 0,20×10,00 = 1,20 + 0,04 + 2,00 = USD 3,24`

### Condiciones

1. **Mismo alcance**: los precios tienen que ser del mismo proveedor, modelo y modalidad de servicio. Si uno viene de otro proveedor, no se calcula.
2. **Sin caché**: usar el perfil `80/20` (entrada / salida).
3. **Con caché pero sin tarifa de lectura**: usar `precio_cache_hit = precio_entrada`. Es una **cota superior** —nunca subestima— y equivale algebraicamente al perfil `80/20`, porque `0,60·in + 0,20·in = 0,80·in`. La columna del precio de caché queda **nula**: no se inventa el dato, el supuesto se declara en `weighted_cost_profile`.
4. **Razonamiento facturable**: si comparte tarifa con la salida, se incluye dentro de `precio_salida`. Si tiene tarifa propia, se calcula aparte con pesos explícitos y se informa por separado.
5. **Cargos adicionales**: los cobros por herramientas (búsqueda web, ejecución de código) y por **escritura** de caché se informan aparte y no entran en la fórmula.
6. **Pesos configurables**: son parámetros, no constantes, y deben sumar 100%. Si cambian, se documenta el cambio y se recalcula todo.
7. **Precisión**: calcular con precisión completa y redondear solo al mostrar, a **2 decimales**.

### Presentación

Todo lugar que muestre el costo (tabla, figura, párrafo) lleva:

- Etiqueta exacta: **«Costo ponderado estimado (USD / 1M tokens)»**
- Pesos usados (p. ej. `60/20/20`), y si la tarifa de lectura de caché se asumió igual a la de entrada
- Fuente de los precios y fecha de consulta

Y al pie: los pesos representan **proporciones de tokens consumidos**, no el costo real por tarea. El resultado **no equivale al costo por tarea** — eso requiere tokens por tarea, no precios por token.

## Gotchas

- OpenRouter devuelve `pricing.prompt` / `pricing.completion` como **string y en USD por token** → parsear a float y multiplicar por `1e6`.
- `pricing.web_search` viene en **USD por request**, no por token: no multiplicar por `1e6` (0,01 = USD 0,01 por búsqueda).
- Precio de caché **ausente ≠ 0**: OpenRouter omite `pricing.input_cache_read` en modelos que sí soportan caché. Asumir cero haría parecer gratis un modelo caro; la regla es usar el precio de entrada como tarifa de caché y marcar el perfil `80/20`.
- `overrides` cambia la tarifa por tramo de tokens de entrada: la fórmula usa la tarifa base. Declararlo al citar el costo.
- **Los puntajes de benchmark no se entreveran entre versiones.** `Terminal-Bench 2.0 ≠ 4.0`, `LiveBench 1.0 ≠ 2.0`, `MMLU ≠ MMLU-Pro`, `GPQA ≠ GPQA Diamond`, `SWE-bench ≠ SWE-bench Verified`, `OSWorld ≠ OSWorld-Verified`, `AIME 2024 ≠ 2025`. Tampoco entre hosts: el mismo benchmark en AA y en Vals da números distintos. Cada combinación **versión + host** es un slot propio con su columna; un modelo sin esa versión queda faltante y no se imputa con la anterior.
- Deduplicar por `canonical_slug`, no por `id`: existen variantes `:free`, `:nitro`, `:thinking`, `:extended` y snapshots con fecha (`-20250514`).
- Los índices entre fuentes **no son comparables entre sí** (ELO de LMArena ≠ Intelligence Index de Artificial Analysis). Normalizá cada feature por separado o usá ranks, nunca promedies escalas distintas.
- Un modelo sin datos en una fuente no es un 0: marcar como faltante y excluir del feature, o imputar mediana **con indicador de faltante**.- `match_key` normaliza **ruido**, nunca identidad: prefijo `Proveedor: `, fechas `YYYYMMDD` y `YYYY-MM-DD`, temporada `-2512` y frontera letra|digito (`qwen3.7` == `qwen 3.7`). Los numeros no se borran: borrarlos hace colisionar `gemma-4-31b` con `gemma-4-12b`.
- Un nombre de la fuente que no aparece **no se imputa**: se propone con `src.alias_review` y se confirma a mano. El comparador es mas estricto que `match_key` y descarta los pares con conflicto de version, tamano, escalon (`Mini`, `Pro`, `Flash`) o letra (`Command A+` != `Command A`). La decision confirmada va a `src/aliases.py` (`BENCHMARK_ALIASES`), que `merge_benchmarks` consulta **antes** de `match_key`; la descartada va a `REJECTED_ALIASES` para que el reporte no la vuelva a proponer.- El repo es Windows: usar rutas relativas desde la raíz del workspace y evitar rutas absolutas hardcodeadas.

## Customizaciones relacionadas

- Skill: `.github/skills/cluster-llm-pipeline/`
- Instructions de datos y código: `.github/instructions/pipeline-datos.instructions.md`
- Universo de modelos y laboratorios obligatorios: `.github/skills/cluster-llm-pipeline/references/universo-modelos.md`
