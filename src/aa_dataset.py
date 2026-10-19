"""Dataset construido **solo** con artificialanalysis.ai/models.

Origen del dato: la pagina `/models` no expone un endpoint de datos publico (su
API v2 responde 401 sin key). Los registros vienen embebidos en el stream RSC de
Next.js que sirve la pagina, y de ahi se extraen dos estructuras:

- `releases` (512): catalogo de modelos con creador y fecha de lanzamiento.
  Es la columna vertebral de identidad.
- `initialModels` (27): los modelos del grafico por defecto, con ~90 campos de
  metricas por benchmark. Es la unica via para obtener puntajes por evaluacion
  sin API key.

Limite honesto de la fuente: la pagina entrega metricas completas de **27**
modelos, no de los 706 del catalogo. El resto solo tiene identidad y fecha.

Regla de version: se agrupa por (creador, familia) y se conserva la version mas
reciente. La familia descarta el numero de version y las etiquetas de esfuerzo,
pero **conserva el tamano** (`27b`) y el escalon (`flash`, `pro`): son modelos
distintos, no versiones del mismo.

Uso:
    python -m src.aa_dataset --payload data/raw/aa_payload_2026-10-19.txt
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

AA_URL = "https://artificialanalysis.ai/models"

# Etiquetas de esfuerzo y de estado: no distinguen familia.
#
# `max` NO va aca: en esta fuente distingue productos (`Qwen3.8 Max` != `Qwen3.8`),
# igual que `flash`, `pro`, `mini`, `omni` o `lite`. Cuando aparece entre
# parentesis se descarta antes de tokenizar, porque ahi si es el esfuerzo.
NOISE_WORDS = {
    "high", "xhigh", "low", "medium", "minimal", "default", "fallback",
    "none", "non", "preview", "beta", "alpha", "exp", "experimental", "latest",
    "it", "instruct", "base", "chat", "thinking", "reasoning", "the", "and",
    "model", "models",
}

# Columna canonica -> como se saca del registro crudo.
SCALARS: dict[str, str] = {
    "aa_slug": "slug",
    "aa_name": "name",
    "aa_release_slug": "release.slug",
    "release_date": "releaseDate",
    "knowledge_cutoff_date": "knowledgeCutoffDate",
    "deprecated": "deprecated",
    "is_open_weights": "isOpenWeights",
    "open_source_categorization": "openSourceCategorization",
    "size_class": "sizeClass",
    "license_name": "licenseName",
    "context_window_tokens": "contextWindowTokens",
    "parameters_billions": "parameters",
    "active_parameters_billions": "inferenceParametersActiveBillions",
    "is_reasoning": "isReasoning",
    "reasoning_tokens": "reasoningTokens",
    "price_in_usd_per_mtok": "price1mInputTokens",
    "price_out_usd_per_mtok": "price1mOutputTokens",
    "price_blended_1to1_usd_per_mtok": "price1mBlended0To1To1",
    "price_cache_hit_usd_per_mtok": "cacheHitPrice",
    "price_cache_write_usd_per_mtok": "cacheWritePrice",
    "cache_hit_discount_pct": "cacheHitDiscountPercent",
    "input_modality_text": "inputModalityText",
    "input_modality_image": "inputModalityImage",
    "input_modality_speech": "inputModalitySpeech",
    "input_modality_video": "inputModalityVideo",
    "output_modality_text": "outputModalityText",
    "output_modality_image": "outputModalityImage",
    "output_modality_speech": "outputModalitySpeech",
    "output_modality_video": "outputModalityVideo",
    # Calidad
    "intelligence_index": "intelligenceIndex",
    "intelligence_index_is_estimated": "intelligenceIndexIsEstimated",
    "omniscience_index": "omniscience",
    "omniscience_accuracy_pct": "omniscienceAccuracy",
    "omniscience_hallucination_pct": "omniscienceHallucinationRate",
    "aa_lcr_pct": "lcr",
    "ifbench_pct": "ifbench",
    "mmmu_pro_pct": "mmmuPro",
    "hle_pct": "hle",
    "hle_diamond_pct": "hleDiamond",
    "gpqa_pct": "gpqa",
    "aime25_pct": "aime25",
    "scicode_pct": "scicode",
    "livecodebench_pct": "livecodebench",
    "critpt_pct": "critpt",
    "gdp_pdf_all_pass_pct": "gdpPdfAllPass",
    "gdpval_normalized_pct": "gdpvalNormalized",
    "terminal_bench_4_0_pct": "terminalBench40",
    "terminal_bench_21_pct": "terminalBench21",
    "terminal_bench_hard_pct": "terminalbenchHard",
    "terminal_bench_science_pct": "terminalBenchScience",
    "frontier_code_pct": "frontierCode",
    "it_bench_sre_pct": "itBenchSre",
    "tau2_pct": "tau2",
    "tau_banking_pct": "tauBanking",
    "harvey_lab_pct": "harveyLab",
    "enterprise_ops_gym_pct": "enterpriseOpsGym",
    "analyst_agent_pct": "analystAgent",
    "apex_agents_pct": "apexAgents",
    "automation_bench_partial_pct": "automationBenchPartialScore",
    "mlcr_overall_pct": "mlcrOverall",
}

# Prefijo de columna -> prefijo del campo anidado.
NESTED: dict[str, tuple[str, ...]] = {
    "capabilities": ("capabilities",),
    "openness": ("openness",),
    "briefcase": ("briefcaseBreakdown",),
}

# Capability indexes por industria.
CAPABILITIES = {
    "cap_finance_and_accounting": "financeAndAccounting",
    "cap_strategy_and_ops": "strategyAndOps",
    "cap_legal": "legal",
    "cap_healthcare_and_medical": "healthcareAndMedical",
    "cap_engineering": "engineering",
    "cap_economics": "economics",
}

# Dimension del pipeline -> columna de este dataset. Se usa en el reporte.
DIMENSIONS = {
    "general": "intelligence_index",
    "reasoning": "gdpval_normalized_pct",
    "coding": "scicode_pct",
    "agentic": "terminal_bench_4_0_pct",
    "professional": "gdp_pdf_all_pass_pct",
    "data": "analyst_agent_pct",
    "browser": None,
    "multimodal": "mmmu_pro_pct",
    "long_context": "aa_lcr_pct",
    "instruction": "ifbench_pct",
}


# --------------------------------------------------------------------------
# Lectura del payload
# --------------------------------------------------------------------------


def decode_flight(path: Path) -> str:
    """Payload de Next.js -> texto del stream, con un nivel de escape resuelto."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    decoder = json.JSONDecoder()
    pieces: list[str] = []
    pos = 0
    while True:
        i = raw.find("push([1,", pos)
        if i < 0:
            break
        start = raw.find('"', i)
        if start < 0:
            break
        try:
            chunk, end = decoder.raw_decode(raw, start)
        except json.JSONDecodeError:
            pos = i + 9
            continue
        if isinstance(chunk, str):
            pieces.append(chunk)
        pos = end
    return "".join(pieces).replace('\\"', '"')


def biggest_array(flight: str, key: str) -> list:
    """Array mas largo que sigue a `"<key>":[` dentro del stream."""
    marker = f'"{key}":['
    decoder = json.JSONDecoder()
    best: list = []
    pos = 0
    while True:
        i = flight.find(marker, pos)
        if i < 0:
            break
        try:
            value, _ = decoder.raw_decode(flight, i + len(marker) - 1)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, list) and len(value) > len(best):
            best = value
        pos = i + 1
    return best


def dig(record: dict, dotted: str):
    """Valor anidado por ruta con puntos; None si falta."""
    current = record
    for part in dotted.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


# --------------------------------------------------------------------------
# Familia y regla de ultima version
# --------------------------------------------------------------------------


def family_key(name: str) -> str:
    """Familia del modelo: sin version ni esfuerzo, con tamano y escalon.

    `Claude Opus 5.5 (Max, Default Fallback)` -> `claude-opus`
    `Qwen3.8 27B (Xhigh)`                      -> `qwen-27b`
    `GLM-5.3-Flash`                            -> `glm-flash`
    """
    text = re.sub(r"\([^)]*\)", " ", (name or "").lower())
    tokens = re.findall(r"[a-z]+|\d+(?:[.]\d+)?[a-z]*", text)
    kept: list[str] = []
    for token in tokens:
        if token in NOISE_WORDS or token == "v":
            continue
        if re.fullmatch(r"\d+(?:[.]\d+)?", token):  # version o fecha suelta
            continue
        kept.append(token)
    return "-".join(kept) or "unknown"


def apply_latest_rule(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Una fila por (creador, familia): la version mas reciente."""
    if frame.empty:
        return frame, []
    work = frame.copy()
    work["family"] = work["aa_name"].map(family_key)
    work["_date"] = pd.to_datetime(work["release_date"], errors="coerce")
    work["_dep"] = work["deprecated"].fillna(False).astype(bool)
    work["_ii"] = pd.to_numeric(work.get("intelligence_index"), errors="coerce")

    ordered = work.sort_values(
        ["creator_slug", "family", "_date", "_dep", "_ii", "aa_slug"],
        ascending=[True, True, False, True, False, True],
        na_position="last",
    )
    kept = ordered.drop_duplicates(subset=["creator_slug", "family"], keep="first")
    dropped = ordered[~ordered["aa_slug"].isin(set(kept["aa_slug"]))]
    record = [
        {
            "familia": row.family,
            "se_descarta": row.aa_name,
            "se_conserva": kept.loc[
                (kept["creator_slug"] == row.creator_slug) & (kept["family"] == row.family),
                "aa_name",
            ].iloc[0],
        }
        for row in dropped.itertuples()
    ]
    kept = kept.drop(columns=["_date", "_dep", "_ii"])
    return kept.reset_index(drop=True), record


# --------------------------------------------------------------------------
# Armado
# --------------------------------------------------------------------------


def flatten(record: dict) -> dict:
    """Un registro crudo -> una fila canonica."""
    row: dict = {}
    for column, source in SCALARS.items():
        row[column] = dig(record, source)
    for column, source in CAPABILITIES.items():
        row[column] = dig(record, f"capabilities.{source}")

    timescale = dig(record, "timescaleData") or {}
    medium = dig(record, "performanceByPromptType.medium") or {}
    row["speed_tok_s"] = timescale.get("medianOutputSpeed") or medium.get("medianOutputSpeed")
    row["latency_ttft_s"] = timescale.get("medianTimeToFirstChunk") or medium.get(
        "medianTimeToFirstChunk"
    )
    # `timescaleData` refleja el tipo de prompt que la pagina muestra por defecto
    # (el largo). Se agrega el desglose para que la eleccion sea auditable.
    for ptype, prefix in (("medium", "medium"), ("hundredK", "hundredk")):
        block = dig(record, f"performanceByPromptType.{ptype}") or {}
        row[f"speed_{prefix}_tok_s"] = block.get("medianOutputSpeed")
        row[f"latency_{prefix}_s"] = block.get("medianTimeToFirstChunk")
    row["time_to_first_answer_token_s"] = dig(record, "timeToFirstAnswerToken.total")
    row["end_to_end_response_time_s"] = dig(record, "endToEndResponseTime.total")
    row["ii_output_tokens_per_task"] = dig(record, "intelligenceIndexOutputTokensPerTask.output")
    row["ii_time_per_task_s"] = dig(record, "intelligenceIndexTimePerTask")

    effort = dig(record, "effort") or {}
    row["effort_slug"] = effort.get("slug")
    row["effort_level"] = effort.get("level")

    openness = dig(record, "openness") or {}
    row["openness_index"] = openness.get("opennessIndex")

    row["creator_slug"] = dig(record, "creator.slug")
    row["creator_name"] = dig(record, "creator.name")
    return row


def build(
    payload: Path,
    catalog_out: Path,
    dataset_out: Path,
    report_out: Path,
    today: date | None = None,
) -> dict:
    today = today or datetime.now(timezone.utc).date()
    flight = decode_flight(payload)
    releases = biggest_array(flight, "releases")
    models = biggest_array(flight, "initialModels")
    if not models:
        raise SystemExit("[aa] no se encontraron registros en el payload")

    # 1) Catalogo completo: identidad y fecha.
    catalog = pd.DataFrame(
        [
            {
                "aa_slug": r.get("slug"),
                "aa_name": r.get("name"),
                "creator_slug": (r.get("creator") or {}).get("slug"),
                "creator_name": (r.get("creator") or {}).get("name"),
                "release_date": r.get("releaseDate"),
                "deprecated": r.get("deprecated"),
            }
            for r in releases
        ]
    )
    catalog["family"] = catalog["aa_name"].map(family_key)
    catalog_dedup, catalog_dropped = apply_latest_rule(catalog)

    # 2) Dataset de metricas: los modelos con puntajes.
    rows = [flatten(m) for m in models]
    metrics = pd.DataFrame(rows)
    dataset, dropped = apply_latest_rule(metrics)

    numeric = [c for c in dataset.columns if c not in {
        "aa_slug", "aa_name", "aa_release_slug", "release_date",
        "knowledge_cutoff_date", "open_source_categorization", "size_class",
        "license_name", "effort_slug", "creator_slug", "creator_name", "family",
    }]
    for column in numeric:
        dataset[column] = pd.to_numeric(dataset[column], errors="coerce")

    # La fuente publica los puntajes de benchmark como fraccion 0-1. El sufijo
    # `_pct` del contrato promete porcentaje, asi que se convierte aca y no en
    # cada consumidor.
    converted: list[str] = []
    for column in dataset.columns:
        if not column.endswith("_pct"):
            continue
        values = dataset[column]
        if values.notna().any() and values.max() <= 1.0:
            dataset[column] = values * 100.0
            converted.append(column)

    dataset = dataset.sort_values("intelligence_index", ascending=False, na_position="last")

    catalog_out.parent.mkdir(parents=True, exist_ok=True)
    dataset_out.parent.mkdir(parents=True, exist_ok=True)
    catalog_dedup.to_csv(catalog_out, index=False, encoding="utf-8")
    dataset.to_parquet(dataset_out, index=False)

    # 3) Reporte.
    lines = [
        "# Dataset de Artificial Analysis",
        "",
        f"- Fuente: {AA_URL}",
        f"- Payload crudo: `{payload.name}`",
        f"- Corte: {today.isoformat()}",
        f"- Catalogo en la fuente: {len(catalog)} lanzamientos, "
        f"{catalog['creator_name'].nunique()} creadores",
        f"- Catalogo tras la regla de ultima version: {len(catalog_dedup)} "
        f"({len(catalog_dropped)} descartados)",
        f"- Modelos con metricas en la fuente: {len(models)}",
        f"- Dataset tras la regla de ultima version: {len(dataset)} "
        f"({len(dropped)} descartados)",
        "",
        "## Por que 27 y no el catalogo entero",
        "",
        "El selector de la pagina ofrece 706 entradas, que corresponden a 512",
        "lanzamientos distintos (el resto son variantes de esfuerzo). Pero el",
        "payload solo embebe metricas de los 27 modelos del grafico por defecto.",
        "El resto de los registros trae identidad y fecha, sin puntajes. La API v2",
        "del sitio responde `401` sin key, asi que este dataset es el techo obtenible",
        "sin credenciales. El catalogo completo queda igual, porque sirve para",
        "aplicar la regla de version y para saber que modelos existen.",
        "",
        "## Regla de ultima version",
        "",
        "Se agrupa por `(creador, familia)` y se conserva el `release_date` mas",
        "reciente. La familia descarta numero de version y etiquetas de esfuerzo,",
        "pero conserva tamano (`27b`) y escalon (`flash`, `pro`): son modelos",
        "distintos, no versiones del mismo.",
        "",
    ]
    if dropped:
        lines += ["| Familia | Se conserva | Se descarta |", "|---|---|---|"]
        for item in dropped[:30]:
            lines.append(f"| `{item['familia']}` | {item['se_conserva']} | {item['se_descarta']} |")
        if len(dropped) > 30:
            lines.append(
                f"| … | … | y {len(dropped) - 30} versiones anteriores mas |"
            )
        lines.append("")

    lines += [
        "## Unidades",
        "",
        "- Precios: USD por 1M tokens (`_usd_per_mtok`), tal como los publica la fuente.",
        "- Puntajes de benchmark: la fuente los da como fraccion 0-1; aca se",
        "  convierten a porcentaje porque el contrato del repo usa el sufijo `_pct`.",
        "- `intelligence_index` y `omniscience_index` quedan en su escala original",
        "  (0-100 y -100..100 respectivamente): no son porcentajes.",
        "",
    ]

    lines += [
        "## Lectura del bloque de tiempos",
        "",
        "`speed_tok_s` y `latency_ttft_s` salen de `timescaleData`, que refleja el",
        "tipo de prompt que la pagina muestra por defecto (el largo). `speed_medium_*`",
        "y `speed_hundredk_*` dan la misma medicion con los otros dos tipos, para que",
        "la eleccion del eje sea auditable.",
        "",
        "**`latency_ttft_s` parece un error y no lo es.** En los modelos de esfuerzo",
        "maximo llega a centenares de segundos: Claude Opus 5.5 mide 615 s aca y",
        "666 s en el leaderboard de la misma fuente, y con el prompt de 100k sube a",
        "757 s. Es tiempo hasta el primer chunk incluyendo el razonamiento, no un",
        "error de unidades. Los dos valores no coinciden exacto porque la fuente",
        "re-mide en cada actualizacion.",
        "",
    ]

    lines += [
        "## Cobertura por columna",
        "",
        "| Columna | Con dato | % |",
        "|---|---:|---:|",
    ]
    total = len(dataset)
    for column in dataset.columns:
        if column == "family":
            continue
        count = int(dataset[column].notna().sum())
        lines.append(f"| `{column}` | {count} | {round(count / total * 100, 1)}% |")

    lines += [
        "",
        "## Que dimension del pipeline alimenta cada columna",
        "",
        "| Dimension | Columna de este dataset | Con dato |",
        "|---|---|---:|",
    ]
    for dimension, column in DIMENSIONS.items():
        if column is None:
            lines.append(f"| `{dimension}` | sin equivalente en esta fuente | 0 |")
        elif column in dataset.columns:
            lines.append(
                f"| `{dimension}` | `{column}` | {int(dataset[column].notna().sum())} |"
            )
        else:
            lines.append(f"| `{dimension}` | `{column}` (no vino) | 0 |")
    lines.append("")

    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text("\n".join(lines), encoding="utf-8")

    return {
        "catalogo": len(catalog),
        "catalogo_dedup": len(catalog_dedup),
        "modelos": len(models),
        "dataset": len(dataset),
        "descartados": len(dropped),
        "reporte": str(report_out),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", default="data/raw/aa_payload_2026-10-19.txt")
    parser.add_argument("--catalog", default="data/interim/aa_catalogo_2026-10-19.csv")
    parser.add_argument("--out", default="data/processed/aa_models_2026-10-19.parquet")
    parser.add_argument("--report", default="data/interim/aa_report_2026-10-19.md")
    args = parser.parse_args(argv)

    summary = build(
        Path(args.payload), Path(args.catalog), Path(args.out), Path(args.report)
    )
    print(f"[aa] catalogo en la fuente: {summary['catalogo']}")
    print(f"[aa] catalogo tras ultima version: {summary['catalogo_dedup']}")
    print(f"[aa] modelos con metricas: {summary['modelos']}")
    print(f"[aa] dataset tras ultima version: {summary['dataset']} "
          f"({summary['descartados']} descartados)")
    print(f"[aa] reporte -> {summary['reporte']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
