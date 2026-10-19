---
description: "Convenciones para trabajar con datos de modelos LLM y notebooks en este repo: nombres de archivos con timestamp, data/raw inmutable, unidades de precio (USD por 1M tokens), dtypes, faltantes y trazabilidad. Use when editing or creating data files (CSV/JSON/Parquet) or notebooks in the Cluster de LLM project."
applyTo: ["data/**", "**/*.ipynb", "**/*.csv", "**/*.parquet"]
---

# Manejo de datos

## `data/raw/` es inmutable

- Nunca editar, ni sobrescribir, ni "arreglar a mano" un archivo de `data/raw/`.
- Nombre con timestamp: `models_<YYYY-MM-DD>.json`. Un snapshot por día.
- Cada archivo lleva un bloque `_meta` con `source`, `url`, `fetched_at`, `n_rows` y `errors`.
- Si un dato está mal, se corrige en `clean` dejando registro, no en el crudo.

## Nombres y unidades

- Archivos y columnas en inglés, snake_case. Prosa y reportes en español.
- **Precio**: siempre `*_usd_per_mtok` (USD por 1M tokens). Si una fuente entrega USD por token, convertir en la frontera de entrada (`* 1e6`) y no propagar la unidad cruda.
- **Contexto** en tokens (`context_length`), **velocidad** en tokens/s (`speed_tok_s`), **latencia** en segundos (`latency_ttft_s`).
- Fechas en ISO-8601 (`YYYY-MM-DD`).

## Tipos y faltantes

- Al escribir en Parquet, castear explícitamente: precios y métricas a `float64`, flags a `bool` (nullable) o `int8`, fechas a `datetime64`.
- Un dato ausente **no es 0**: dejarlo nulo y agregar `<feature>_missing` cuando la feature entre en un modelo o distancia.
- Booleans derivados (`is_open_weights`, `supports_*`) documentan en el código cómo se infirieron (campo de origen o regla).

## Trazabilidad

- Toda columna derivada de una fuente externa tiene su bandera `src_*` y, si el match es por nombre, un `row_confidence` (0-1).
- Cada tabla, figura o número que salga del repo lleva fuente y fecha de corte.
- Si cambia el contrato de datos (`data/processed/llm_features.parquet`), actualizar `AGENTS.md` y el skill `cluster-llm-pipeline` en el mismo cambio.

## Notebooks

- Idempotentes: correr de arriba a abajo tiene que dar el mismo resultado.
- Sin rutas absolutas hardcodeadas (`f:\...`); usar rutas relativas a la raíz del workspace.
- Semillas fijas (`random_state=42`) en cualquier paso aleatorio.
- El notebook es para explorar, no para el pipeline: lo que queda se refactoriza a `src/`.
- Limpiar las salidas y reiniciar el contador de ejecución antes de commitear.
- Un notebook, un objetivo. Si mezcla limpieza y clustering, dividirlo.

## Encoding

- UTF-8 sin BOM. Cuidado con acentos si se escribe por consola en PowerShell: preferir escribir a archivo y verificar el resultado.
