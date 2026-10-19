"""Tabla de analisis construida **solo** con artificialanalysis.ai.

No depende de `llm_features.parquet` ni de OpenRouter ni de Vals: parte de
`aa_models_<fecha>.parquet`, que ya contiene solo lo que publica la fuente, y
recorta las filas que tienen al menos 6 de las 7 features de analisis.

Mapeo de las 7 features del pipeline a columnas de esta fuente. En varios casos
la fuente no tiene el mismo benchmark, asi que se usa el equivalente de la misma
dimension y se declara el cambio:

    speed_tok_s             <- speed_tok_s            (medias de AA)
    latency_ttft_s          <- latency_ttft_s
    reasoning               <- gdpval_normalized_pct  (GDPval-AA v2.1)
    coding                  <- scicode_pct            (SciCode)
    agentic                 <- terminal_bench_4_0_pct (Terminal-Bench 4.0)
    professional            <- gdp_pdf_all_pass_pct   (GDP.pdf)
    data                    <- analyst_agent_pct      (AA-AnalystAgent)

Uso:
    python -m src.aa_table --in data/processed/aa_models_2026-10-19.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Feature de analisis -> columna de la fuente.
FEATURES: dict[str, str] = {
    "speed_tok_s": "speed_tok_s",
    "latency_ttft_s": "latency_ttft_s",
    "reasoning": "gdpval_normalized_pct",
    "coding": "scicode_pct",
    "agentic": "terminal_bench_4_0_pct",
    "professional": "gdp_pdf_all_pass_pct",
    "data": "analyst_agent_pct",
}

IDENTITY = [
    "aa_slug",
    "aa_name",
    "creator_name",
    "release_date",
    "context_window_tokens",
    "parameters_billions",
    "is_open_weights",
]

# Calidad y mercado que no entran en la distancia pero se publican.
EXTRA = [
    "intelligence_index",
    "aa_lcr_pct",
    "mmmu_pro_pct",
    "omniscience_index",
    "harvey_lab_pct",
    "frontier_code_pct",
    "price_in_usd_per_mtok",
    "price_out_usd_per_mtok",
    "ii_output_tokens_per_task",
    "ii_time_per_task_s",
]

MIN_FEATURES = 6


def build(source: Path, out: Path, out_csv: Path, report: Path) -> dict:
    frame = pd.read_parquet(source)

    missing_columns = [c for c in FEATURES.values() if c not in frame.columns]
    if missing_columns:
        raise SystemExit(f"[aa_table] faltan columnas en la fuente: {missing_columns}")

    columns = [FEATURES[k] for k in FEATURES]
    counts = frame[columns].notna().sum(axis=1)
    keep = counts >= MIN_FEATURES

    table = frame.loc[keep].copy()
    table["n_features"] = counts[keep].astype(int)

    # Si dos features apuntan a la misma columna, no duplicar en la salida.
    ordered = [c for c in IDENTITY if c in table.columns]
    ordered += [c for c in dict.fromkeys(columns) if c in table.columns]
    ordered += ["n_features"]
    ordered += [c for c in EXTRA if c in table.columns and c not in ordered]

    table = table[ordered].sort_values(
        "intelligence_index", ascending=False, na_position="last"
    )
    table = table.reset_index(drop=True)

    dropped = frame.loc[~keep, ["aa_name"] + columns].copy()
    dropped["n_features"] = counts[~keep].astype(int)
    dropped["faltan"] = dropped[columns].isna().apply(
        lambda row: ", ".join(
            name for name, column in FEATURES.items() if pd.isna(row[column])
        ),
        axis=1,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out, index=False)
    table.to_csv(out_csv, index=False, encoding="utf-8")

    lines = [
        "# Tabla de analisis: solo Artificial Analysis",
        "",
        f"- Fuente de la tabla: `{source.name}`",
        f"- Filas en la fuente: {len(frame)}",
        f"- Criterio: al menos {MIN_FEATURES} de {len(FEATURES)} features de analisis",
        f"- Filas que quedan: **{len(table)}**",
        f"- Filas descartadas: {len(dropped)}",
        "",
        "## Features y su columna de origen",
        "",
        "La fuente no mide los mismos benchmarks que el pipeline principal. Cada",
        "feature usa el equivalente de la misma dimension, y el cambio queda",
        "declarado aca: promediar `scicode_pct` con `vibe_code_bench_pct` de Vals",
        "seria entreverar hosts.",
        "",
        "| Feature | Columna de la fuente | Benchmark | Con dato |",
        "|---|---|---|---:|",
    ]
    benchmarks = {
        "speed_tok_s": "medias propias de AA",
        "latency_ttft_s": "medias propias de AA",
        "reasoning": "GDPval-AA v2.1",
        "coding": "SciCode",
        "agentic": "Terminal-Bench 4.0",
        "professional": "GDP.pdf",
        "data": "AA-AnalystAgent",
    }
    for name, column in FEATURES.items():
        lines.append(
            f"| `{name}` | `{column}` | {benchmarks[name]} | "
            f"{int(table[column].notna().sum())}/{len(table)} |"
        )

    lines += [
        "",
        "## Distribucion de features por fila",
        "",
        "| Features presentes | Filas |",
        "|---|---:|",
    ]
    for value, count in table["n_features"].value_counts().sort_index().items():
        lines.append(f"| {value} | {int(count)} |")

    if not dropped.empty:
        lines += [
            "",
            "## Filas descartadas",
            "",
            "| Modelo | Features | Faltan |",
            "|---|---:|---|",
        ]
        for row in dropped.sort_values("n_features", ascending=False).itertuples():
            lines.append(f"| {row.aa_name} | {row.n_features} | {row.faltan} |")

    lines += [
        "",
        "## Cobertura por columna de la tabla",
        "",
        "| Columna | Con dato | % |",
        "|---|---:|---:|",
    ]
    for column in table.columns:
        count = int(table[column].notna().sum())
        lines.append(f"| `{column}` | {count} | {round(count / len(table) * 100, 1)}% |")
    lines.append("")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    return {
        "fuente": len(frame),
        "tabla": len(table),
        "descartadas": len(dropped),
        "out": str(out),
        "report": str(report),
        "descartadas_detalle": dropped[["aa_name", "n_features"]].to_dict("records"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="source", default="data/processed/aa_models_2026-10-19.parquet")
    parser.add_argument("--out", default="data/processed/aa_tabla_2026-10-19.parquet")
    parser.add_argument("--csv", default="data/interim/aa_tabla_2026-10-19.csv")
    parser.add_argument("--report", default="data/interim/aa_tabla_report_2026-10-19.md")
    args = parser.parse_args(argv)

    summary = build(
        Path(args.source), Path(args.out), Path(args.csv), Path(args.report)
    )
    print(f"[aa_table] filas en la fuente: {summary['fuente']}")
    print(f"[aa_table] tabla: {summary['tabla']} filas | descartadas: {summary['descartadas']}")
    for item in summary["descartadas_detalle"]:
        print(f"[aa_table]   fuera: {item['aa_name']} ({item['n_features']} features)")
    print(f"[aa_table] salida -> {summary['out']}")
    print(f"[aa_table] reporte -> {summary['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
