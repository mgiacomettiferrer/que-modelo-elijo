"""Adaptadores de fuentes externas.

Cada fuente expone un `fetch` (trae crudo) y un `normalize` (a filas canonicas).
La conversion de unidades ocurre **en la frontera**: los precios de OpenRouter
vienen en USD por token y se multiplican por 1e6 al entrar, para no propagar la
unidad cruda (convencion de `pipeline-datos.instructions.md`).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from . import schema
from .aliases import BENCHMARK_ALIASES

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Pesos del costo ponderado (AGENTS.md -> Costo ponderado).
WEIGHTS_CACHE = (0.60, 0.20, 0.20)  # entrada / lectura de cache / salida
WEIGHTS_NOCACHE = (0.80, 0.20)  # entrada / salida

# Alias de proveedor para alinear el prefijo del slug con los laboratorios
# de MUST_INCLUDE_LABS.
PROVIDER_ALIASES: dict[str, str] = {
    "x-ai": "spacexai",
    "xai": "spacexai",
    "mistralai": "mistral",
    "moonshotai": "moonshot",
    "meta-llama": "meta",
    "zhipu": "z-ai",
    "zhipuai": "z-ai",
    "qwen": "alibaba",
    "01-ai": "01ai",
    "nvidia": "nvidia",
    "amazon": "amazon",
    "microsoft": "microsoft",
    "inclusionai": "inclusionai",
    "stepfun": "stepfun",
}


# --------------------------------------------------------------------------
# Utilidades de nombre y precio
# --------------------------------------------------------------------------


def parse_price(pricing: dict, key: str) -> float | None:
    """USD por token -> USD por 1M tokens.

    Un valor negativo en OpenRouter senala precio dinamico, no un precio real:
    se trata como faltante. Igual que un campo ausente.
    """
    raw = pricing.get(key)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return value * 1e6


def parse_price_per_call(pricing: dict, key: str) -> float | None:
    """USD por llamada. **No** se multiplica por 1e6: no es un precio por token.

    OpenRouter publica `web_search` como costo por request (`"0.01"` = USD 0,01),
    a diferencia de `prompt` / `completion`, que vienen en USD por token.
    """
    raw = pricing.get(key)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return None if value < 0 else value


def weighted_cost(
    price_in: float | None,
    price_out: float | None,
    cache_read: float | None,
    supports_cache: bool = True,
) -> tuple[float | None, str | None]:
    """Costo ponderado estimado, en USD por 1M tokens.

    Con tarifa de cache documentada: 60/20/20.

    Sin tarifa de cache documentada: se asume que el cache **no da descuento**
    (`cache_hit = precio_entrada`). Es una cota superior, nunca subestima, y
    algebraicamente equivale al perfil 80/20:

        0,60*in + 0,20*in + 0,20*out == 0,80*in + 0,20*out

    La columna `price_cache_read_usd_per_mtok` queda **nula**: no se inventa el
    dato, solo se declara el supuesto en `weighted_cost_profile`.

    Devuelve (None, None) solo si falta el precio de entrada o el de salida.
    """
    if price_in is None or price_out is None:
        return None, None

    if supports_cache and cache_read is not None:
        w_in, w_cache, w_out = WEIGHTS_CACHE
        total = w_in * price_in + w_cache * cache_read + w_out * price_out
        return total, "60/20/20"

    # Sin tarifa de cache: el cache no aporta descuento.
    w_in, w_out = WEIGHTS_NOCACHE
    return w_in * price_in + w_out * price_out, "80/20"


def strip_variant(slug: str) -> str:
    """Quita las variantes que no cambian el modelo de negocio."""
    for suffix in schema.VARIANT_SUFFIX:
        if slug.endswith(suffix):
            slug = slug[: -len(suffix)]
    return slug


def family_key(slug: str) -> str:
    """Linea de familia: slug sin version, esfuerzo ni estado.

    `anthropic/claude-opus-5.5` -> `claude-opus`
    `openai/gpt-6-astra`       -> `gpt-astra`
    `google/gemini-3.8-flash`  -> `gemini-flash`
    """
    text = strip_variant(slug).lower()
    text = text.split("/")[-1]
    text = re.sub(r"[:/]", "-", text)
    text = re.sub(r"(\d)", r"-\1", text)  # separa digitos pegados a letras
    text = re.sub(r"\d+", " ", text)  # fuera numeros de version y fechas
    tokens = [t for t in re.split(r"[-_.\s]+", text) if t]
    tokens = [t for t in tokens if t not in schema.FAMILY_STOPWORDS]
    # dedupe preservando el orden
    return "-".join(dict.fromkeys(tokens)) or "unknown"


def provider_from_slug(slug: str) -> str:
    prefix = slug.split("/")[0].lower()
    return PROVIDER_ALIASES.get(prefix, prefix)


def is_excluded(slug: str) -> str | None:
    """Devuelve el patron que excluye al modelo, o None si entra al universo."""
    lowered = slug.lower()
    for pattern in schema.EXCLUDE_ALL:
        if re.search(pattern, lowered):
            return pattern
    return None


def match_key(name: str) -> str:
    """Clave para unir un puntaje de benchmark con una fila del dataset.

    Conservadora a proposito: **no borra numeros**. Borrarlos hace colisionar
    `gemma-4-31b` con `gemma-4-12b` y `gemini-3.8-flash` con
    `gemini-3.5-flash-lite`, que es como se contaminan los datos en silencio.

    Lo que si normaliza:
      - el prefijo `Proveedor: ` que trae la columna `name` del dataset
      - el esfuerzo entre parentesis (`(low with fallback)`, `(xhigh)`)
      - fechas `YYYYMMDD`, fechas con guiones `YYYY-MM-DD` y temporada `-2512`
      - la frontera letra|digito (`qwen3.7` == `qwen 3.7`)
      - sufijos que no identifican (`-it`, `-base`, `-latest`)

    Las tres primeras se agregaron tras auditar los pares que quedaban sin unir:
    son separadores de ruido, no identidad. Siguen **sin** borrarse numeros.
    """
    text = name.lower().split("/")[-1]
    text = re.sub(r"^\w+:\s+", " ", text)  # prefijo `Proveedor: `
    text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)  # fecha con guiones
    text = re.sub(r"\([^)]*\)", " ", text)  # esfuerzo / notas
    text = re.sub(r"20\d{6}", " ", text)  # fecha YYYYMMDD
    text = re.sub(r"(?<=-)\d{4}(?![0-9])", " ", text)  # sufijo de temporada
    text = re.sub(r"([a-z])(\d)", r"\1-\2", text)  # frontera letra|digito
    text = re.sub(r"(\d)([a-z])", r"\1-\2", text)  # frontera digito|letra
    text = re.sub(r"[\s_]+", "-", text)
    tokens = [t for t in re.split(r"-+", text) if t]
    tokens = [t for t in tokens if t not in schema.MATCH_STOPWORDS]
    return "-".join(tokens) or "unknown"


def effort_of(name: str) -> tuple[str | None, int]:
    """Variante de esfuerzo declarada en el nombre y su rango.

    `Claude Opus 5.5 (low with fallback)` -> ("low with fallback", 3)
    """
    found = re.findall(r"\(([^)]*)\)", name)
    for chunk in found:
        for token, rank in schema.EFFORT_RANK.items():
            if token in chunk.lower():
                return chunk, rank
    return None, schema.EFFORT_RANK["default"]


# --------------------------------------------------------------------------
# OpenRouter
# --------------------------------------------------------------------------


def fetch_openrouter(timeout: int = 40) -> dict:
    """Trae el catalogo completo. Endpoint publico, sin API key."""
    response = requests.get(OPENROUTER_MODELS_URL, timeout=timeout)
    response.raise_for_status()
    return response.json()


def normalize_openrouter(payload: dict, cutoff: date) -> list[dict]:
    """Payload crudo de OpenRouter -> filas canonicas.

    Solo hace conversion de tipos y unidades. Los filtros de universo
    (ventana, exclusiones, deduplicacion) son responsabilidad de `clean`.
    """
    rows: list[dict] = []
    for item in payload.get("data", []):
        model_id = item.get("id")
        if not model_id:
            continue

        slug = strip_variant(item.get("canonical_slug") or model_id)
        pricing = item.get("pricing") or {}
        architecture = item.get("architecture") or {}
        top_provider = item.get("top_provider") or {}
        supported = set(item.get("supported_parameters") or [])
        input_modalities = set(architecture.get("input_modalities") or [])

        price_in = parse_price(pricing, "prompt")
        price_out = parse_price(pricing, "completion")
        cache_read = parse_price(pricing, "input_cache_read")
        cache_write = parse_price(pricing, "input_cache_write")
        reasoning = parse_price(pricing, "internal_reasoning")
        web_search = parse_price_per_call(pricing, "web_search")

        # Razonamiento: si comparte tarifa con la salida va dentro de price_out.
        if reasoning is not None and price_out is not None and abs(reasoning - price_out) < 1e-9:
            reasoning = None

        cost, profile = weighted_cost(price_in, price_out, cache_read, supports_cache=True)

        created = item.get("created")
        release: date | None = None
        if isinstance(created, (int, float)) and created > 0:
            release = datetime.fromtimestamp(int(created), tz=timezone.utc).date()

        hf_id = item.get("hugging_face_id") or None

        rows.append(
            {
                "model_id": model_id,
                "canonical_slug": slug,
                "name": item.get("name") or slug,
                "provider": provider_from_slug(slug),
                "family": family_key(slug),
                "release_date": release,
                "hugging_face_id": hf_id,
                "context_length": _as_float(item.get("context_length")),
                "max_output_tokens": _as_float(top_provider.get("max_completion_tokens")),
                # Inferido: OpenRouter no expone un flag de pesos abiertos.
                "is_open_weights": hf_id is not None,
                "price_in_usd_per_mtok": price_in,
                "price_out_usd_per_mtok": price_out,
                "price_cache_read_usd_per_mtok": cache_read,
                "price_cache_write_usd_per_mtok": cache_write,
                "price_reasoning_usd_per_mtok": reasoning,
                "price_web_search_usd_per_call": web_search,
                "weighted_cost_usd_per_mtok": cost,
                "weighted_cost_profile": profile,
                "supports_tools": "tools" in supported,
                "supports_reasoning": bool({"reasoning", "include_reasoning"} & supported),
                "supports_vision": "image" in input_modalities,
                "supports_audio": "audio" in input_modalities,
                "src_openrouter": True,
                "src_artificial_analysis": False,
                "src_lmarena": False,
                "src_hf": hf_id is not None,
                "src_vals": False,
                "src_livebench": False,
                # Interno: lo usa clean para el filtro de solo texto.
                "_output_modalities": set(architecture.get("output_modalities") or ["text"]),
                # Unico dato del catalogo: el match es exacto por construccion.
                "row_confidence": 1.0,
                "_cutoff": cutoff,
            }
        )
    return rows


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Snapshots de benchmark
# --------------------------------------------------------------------------

# Las fuentes de benchmark (Vals, Arena, Artificial Analysis) bloquean el
# acceso programatico: Vals y Arena devuelven 403/404 sin navegador, y la API
# de AA pide key (401). LiveBench publica CSV en GitHub pero su ultima tabla
# es del 2026-06-25 y no cubre los modelos de septiembre/octubre.
#
# Por eso los puntajes entran por snapshot manual, con este formato:
#
#   {
#     "_meta": {"source": "vals.ai", "fetched_at": "2026-10-16", "errors": []},
#     "scores": {
#       "legal_bench_pct": {"Claude Opus 5.5 (max)": 72.4, "...": 0.0}
#     }
#   }
#
# La clave de cada entrada es el nombre tal como lo publica el leaderboard;
# `clean` la reduce con `match_key` y registra la confianza del match.


def load_benchmark_snapshot(path: Path) -> tuple[dict[str, dict[str, float]], dict]:
    """Lee un snapshot de benchmarks. Devuelve (scores, meta).

    Estructura devuelta: {columna_de_benchmark: {nombre_fuente: valor}}.
    """
    if not path.exists():
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    meta = payload.get("_meta", {})
    raw_scores = payload.get("scores", {})

    scores: dict[str, dict[str, float]] = {}
    for column, entries in raw_scores.items():
        if column not in schema.SNAPSHOT_COLUMNS:
            raise ValueError(
                f"Columna de snapshot desconocida: {column!r}. "
                "Declararla en src/schema.py (BENCHMARK_SLOTS o "
                "DIRECT_METRIC_COLUMNS) antes de usarla."
            )
        clean_entries: dict[str, float] = {}
        for source_name, value in (entries or {}).items():
            number = _as_float(value)
            if number is not None:
                clean_entries[source_name] = number
        scores[column] = clean_entries
    return scores, meta


# Host del leaderboard -> bandera de procedencia del contrato.
HOST_SRC_FLAG: dict[str, str] = {
    "artificialanalysis.ai": "src_artificial_analysis",
    "arena.ai": "src_lmarena",
    "vals.ai": "src_vals",
    "livebench.ai": "src_livebench",
    "swebench.com": "src_hf",
    "gorilla.cs.berkeley.edu": "src_hf",
    "spreadsheetbench.github.io": "src_hf",
}


def src_flag_for_column(column: str) -> str | None:
    """Que bandera `src_*` corresponde a una columna del snapshot."""
    for slot in schema.BENCHMARK_SLOTS:
        if slot.column == column:
            return HOST_SRC_FLAG.get(slot.host.lower())
    if column in schema.DIRECT_METRIC_COLUMNS:
        return "src_artificial_analysis"
    return None


def merge_benchmarks(
    rows: list[dict],
    scores: dict[str, dict[str, float]],
    aliases: dict[str, str] | None = None,
) -> dict:
    """Une los puntajes a las filas: primero por alias explicito, despues por `match_key`.

    Tres salvaguardas contra el error silencioso:

    1. **Alias explicito**: un nombre revisado a mano (`src/aliases.py`) va a la
       fila que declara, sin pasar por `match_key`. Se consulta primero.
    2. **Colision**: si dos nombres distintos de la fuente caen en la misma
       clave, se elige de forma determinista la variante de mayor esfuerzo y se
       registran las descartadas. No se promedian ni se pisan entre si.
    3. **Sin match**: un nombre que no encuentra fila se cuenta pero no se
       imputa. Mejor un faltante declarado que un valor de otro modelo.

    Ni el alias ni la clave pisan un dato ya escrito: si la celda esta ocupada,
    se registra en `collapsed_variants` y se conserva el valor existente.
    """
    aliases = BENCHMARK_ALIASES if aliases is None else aliases

    index: dict[str, dict] = {}
    for row in rows:
        for key in {match_key(row["canonical_slug"]), match_key(row["name"])}:
            index.setdefault(key, row)
    by_slug = {row["canonical_slug"]: row for row in rows}

    summary: dict[str, dict] = {}
    for column, entries in scores.items():
        collapsed: list[str] = []
        unmatched: list[str] = []
        matched = 0
        aliased = 0

        # 1) Alias revisados a mano: mandan sobre cualquier parecido.
        pending: dict[str, list[str]] = {}
        for source_name, value in entries.items():
            slug = aliases.get(source_name)
            if slug is None:
                pending.setdefault(match_key(source_name), []).append(source_name)
                continue
            target = by_slug.get(slug)
            if target is None:
                unmatched.append(source_name)
                collapsed.append(f"alias sin fila: {source_name!r} -> {slug}")
                continue
            if target.get(column) is not None:
                collapsed.append(f"alias {source_name!r} descartado: la celda ya tenia valor")
                continue
            target[column] = value
            flag = src_flag_for_column(column)
            if flag:
                target[flag] = True
            aliased += 1
            matched += 1

        # 2) El resto, por clave conservadora.
        for key, names in pending.items():
            target = index.get(key)
            if target is None:
                unmatched.extend(names)
                continue
            winner = sorted(names, key=lambda n: (-effort_of(n)[1], n))[0]
            if len(names) > 1:
                others = [n for n in names if n != winner]
                label, _ = effort_of(winner)
                collapsed.append(f"{key}: {winner!r} (esfuerzo {label})")
                for other in others[:3]:
                    collapsed.append(f"{key}: descartado {other!r}")
            if target.get(column) is not None:
                collapsed.append(f"{key}: no pisa el valor existente")
                continue
            target[column] = entries[winner]
            flag = src_flag_for_column(column)
            if flag:
                target[flag] = True
            matched += 1

        summary[column] = {
            "declared": len(entries),
            "matched": matched,
            "aliased": aliased,
            "unmatched": len(unmatched),
            "collapsed_variants": collapsed,
        }
    return summary


def write_raw_snapshot(payload: dict, out_path: Path, url: str, errors: list[str]) -> None:
    """Escribe el crudo inmutable con su bloque `_meta`."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "_meta": {
            "source": "openrouter",
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_rows": len(payload.get("data", [])),
            "errors": errors,
        },
        "data": payload.get("data", []),
    }
    out_path.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def cutoff_dates(today: date | None = None) -> tuple[date, date]:
    """(inicio de la ventana de 12 meses, limite de frescura)."""
    today = today or datetime.now(timezone.utc).date()
    return today - timedelta(days=schema.WINDOW_DAYS), today - timedelta(days=schema.FRESHNESS_DAYS)
