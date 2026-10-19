"""Reporte de nulos por atributo.

Lee el contrato (`data/processed/llm_features.parquet`) y devuelve, para cada
columna: cuantos nulos tiene, que porcentaje representan y de que grupo es.
Separa **entrenamiento** de **metadata** y de los **secundarios de
visualizacion**, y marca como bloqueante toda feature de entrenamiento que
quede 100% nula.

Uso:
    python -m src.report_nulls --in data/processed/llm_features.parquet
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import schema


def role_of(column: str, selected: frozenset[str] = frozenset()) -> str:
    """Rol de una columna del frame, incluidas las que no estan en el contrato."""
    if column in selected:
        # El benchmark elegido para su dimension ES una feature de clustering.
        return schema.TRAINING
    if column in schema.COLUMN_BY_NAME:
        return schema.COLUMN_BY_NAME[column].role
    if column in schema.BENCHMARK_COLUMNS:
        return schema.INPUT
    if column.endswith("_n_sources"):
        return schema.INPUT
    if column.endswith("_scaled"):
        return schema.TRAINING
    if column.endswith("_missing"):
        # Indicador de faltante: documenta la imputacion, no entra en la distancia.
        return schema.INDICATOR
    return schema.METADATA


def group_of(column: str) -> str:
    if column in schema.COLUMN_BY_NAME:
        return schema.COLUMN_BY_NAME[column].group
    if column in schema.BENCHMARK_COLUMNS:
        slot = next(s for s in schema.BENCHMARK_SLOTS if s.column == column)
        return f"benchmark:{slot.axis}"
    if column.endswith("_n_sources"):
        return "calidad-ejes"
    if column.endswith("_missing"):
        return "faltantes"
    if column.endswith("_scaled"):
        return "escalado"
    return "otro"


def profile(frame: pd.DataFrame, selected: frozenset[str] = frozenset()) -> pd.DataFrame:
    """Un registro por columna con su perfil de nulos."""
    records: list[dict] = []
    n_rows = len(frame)
    for column in frame.columns:
        series = frame[column]
        n_null = int(series.isna().sum())
        try:
            n_unique = int(series.nunique(dropna=True))
        except TypeError:  # columnas con listas u objetos no hashables
            n_unique = -1
        non_null = series.dropna()
        example = "" if non_null.empty else str(non_null.iloc[0])[:40]
        records.append(
            {
                "column": column,
                "role": role_of(column, selected),
                "group": group_of(column),
                "dtype": str(series.dtype),
                "n_null": n_null,
                "pct_null": round(n_null / n_rows * 100, 2) if n_rows else 100.0,
                "n_unique": n_unique,
                "example": example,
            }
        )
    return pd.DataFrame.from_records(records)


def _table(rows: pd.DataFrame) -> list[str]:
    lines = [
        "| Atributo | Grupo | Tipo | Nulos | % nulos | Unicos | Ejemplo |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for _, row in rows.iterrows():
        flag = " **!!**" if row["pct_null"] >= 100 else ""
        lines.append(
            f"| `{row['column']}`{flag} | {row['group']} | {row['dtype']} | "
            f"{row['n_null']} | {row['pct_null']:.2f} | {row['n_unique']} | "
            f"{row['example']} |"
        )
    return lines


def render(
    df: pd.DataFrame,
    n_rows: int,
    cutoff: str | None = None,
    source_note: str = "",
    selection: dict | None = None,
) -> str:
    cutoff = cutoff or datetime.now(timezone.utc).date().isoformat()
    total = len(df)

    lines = [
        "# Reporte de nulos por atributo",
        "",
        f"- Corte: **{cutoff}**",
        f"- Filas (universo): **{n_rows}**",
        f"- Atributos: **{total}**",
        f"- Cota de universo declarada: {schema.UNIVERSE_MIN}-{schema.UNIVERSE_MAX}"
        f" -> {'OK' if schema.UNIVERSE_MIN <= n_rows <= schema.UNIVERSE_MAX else '**FUERA DE RANGO**'}",
    ]
    if source_note:
        lines.append(f"- Fuentes: {source_note}")
    lines.append("")

    # --- que benchmark representa a cada dimension -----------------------
    if selection:
        lines += [
            "## Feature elegida por dimension",
            "",
            "Los ejes agregados **no** entran en la matriz de distancia: promedian "
            "ranks de benchmarks que no cubren a los mismos modelos, asi que dos "
            "filas con el mismo valor no son la misma medicion. Cada dimension se "
            "representa con **un solo** benchmark, el de menos nulos.",
            "",
            "| Dimension | Benchmark | Fuente | Valid | % nulos | Candidatos |",
            "|---|---|---|---:|---:|---:|",
        ]
        for dimension, entry in selection.items():
            mark = "" if entry["n_valid"] else " **(fuera)**"
            lines.append(
                f"| {dimension}{mark} | `{entry['benchmark']}` | {entry['source']} | "
                f"{entry['n_valid']} | {entry['pct_null']:.2f} | {entry['candidates']} |"
            )
        lines.append("")

    # --- resumen por rol ---------------------------------------------------
    lines += ["## Resumen por rol", "", "| Rol | Atributos | Con datos | 100% nulos |", "|---|---:|---:|---:|"]
    for role in schema.ROLE_ORDER:
        subset = df[df["role"] == role]
        if subset.empty:
            continue
        with_data = int((subset["pct_null"] < 100).sum())
        empty = int((subset["pct_null"] >= 100).sum())
        lines.append(
            f"| {schema.ROLE_LABEL[role]} | {len(subset)} | {with_data} | {empty} |"
        )
    lines.append("")

    # --- detalle por rol ---------------------------------------------------
    for role in schema.ROLE_ORDER:
        subset = df[df["role"] == role].sort_values(
            by=["pct_null", "column"], ascending=[False, True]
        )
        if subset.empty:
            continue
        empty = int((subset["pct_null"] >= 100).sum())
        lines += [
            f"## {schema.ROLE_LABEL[role]}",
            "",
            f"{len(subset)} atributos, {empty} sin ningun dato.",
            "",
            *_table(subset),
            "",
        ]

    # --- bloqueantes -------------------------------------------------------
    blockers = df[(df["role"] == schema.TRAINING) & (df["pct_null"] >= 100)]
    lines += ["## Bloqueantes para clusterizar", ""]
    if blockers.empty:
        lines.append("Ninguno: todas las features de entrenamiento tienen datos.")
    else:
        lines += [
            f"{len(blockers)} features de entrenamiento estan 100% nulas. "
            "Sin ellas la matriz de distancia queda vacia y el clustering no corre.",
            "",
            "| Atributo | Grupo |",
            "|---|---|",
        ]
        for _, row in blockers.sort_values("column").iterrows():
            lines.append(f"| `{row['column']}` | {row['group']} |")
    lines.append("")

    # --- insumos de la calidad -------------------------------------------
    inputs = df[df["role"] == schema.INPUT]
    n_inputs = len(inputs)
    inputs_null = int((inputs["pct_null"] >= 100).sum())
    lines += [
        "## Insumos de los ejes de calidad",
        "",
        f"{n_inputs} columnas de insumo, {inputs_null} de ellas sin ningun dato.",
        "",
    ]

    # --- columnas utiles que igual entran ---------------------------------
    training_ok = df[
        (df["role"] == schema.TRAINING) & (df["pct_null"] < 100) & (~df["column"].str.endswith("_missing"))
    ]
    lines += ["## Features de entrenamiento utilizables hoy", ""]
    if training_ok.empty:
        lines.append(
            "Ninguna. Las dos features de rendimiento (`speed_tok_s`, `latency_ttft_s`) "
            "y los 10 ejes de calidad dependen de fuentes que todavia no estan conectadas."
        )
    else:
        lines += ["| Atributo | Cobertura |", "|---|---:|"]
        for _, row in training_ok.sort_values("column").iterrows():
            lines.append(f"| `{row['column']}` | {100 - row['pct_null']:.2f}% |")
    lines.append("")

    return "\n".join(lines)


def run(
    in_path: Path,
    out_path: Path | None = None,
    source_note: str = "",
    selection_path: Path | None = None,
) -> dict:
    frame = pd.read_parquet(in_path)

    selection: dict = {}
    if selection_path and selection_path.exists():
        selection = json.loads(selection_path.read_text(encoding="utf-8")).get(
            "seleccion", {}
        )
    selected = frozenset(
        entry["benchmark"] for entry in selection.values() if entry.get("n_valid", 0) > 0
    )

    df = profile(frame, selected)
    text = render(df, len(frame), source_note=source_note, selection=selection)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")

    summary = {
        role: {
            "atributos": int((df["role"] == role).sum()),
            "con_datos": int(((df["role"] == role) & (df["pct_null"] < 100)).sum()),
        }
        for role in schema.ROLE_ORDER
    }
    return {
        "table": df,
        "text": text,
        "out_path": None if out_path is None else str(out_path),
        "n_rows": len(frame),
        "summary": summary,
        "blockers": df[(df["role"] == schema.TRAINING) & (df["pct_null"] >= 100)][
            "column"
        ].tolist(),
    }


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    parser = argparse.ArgumentParser(description="Reporte de nulos por atributo.")
    parser.add_argument("--in", dest="in_path", type=Path, default=Path("data/processed/llm_features.parquet"))
    parser.add_argument("--out", type=Path, default=Path(f"data/interim/nulls_report_{today}.md"))
    parser.add_argument("--csv", type=Path, default=None, help="Opcional: volcar la tabla a CSV.")
    parser.add_argument("--source-note", default="OpenRouter (catalogo en vivo)")
    parser.add_argument(
        "--selection",
        type=Path,
        default=Path("data/interim/dimension_selection.json"),
        help="Seleccion de benchmark por dimension, escrita por normalize.",
    )
    args = parser.parse_args(argv)

    result = run(args.in_path, args.out, args.source_note, args.selection)
    if args.csv:
        result["table"].to_csv(args.csv, index=False, encoding="utf-8")

    print(f"[nulls] filas: {result['n_rows']}")
    for role, stats in result["summary"].items():
        if stats["atributos"]:
            print(
                f"[nulls]   {schema.ROLE_LABEL[role]:42s} "
                f"{stats['atributos']:3d} attrs, {stats['con_datos']:3d} con datos"
            )
    print(f"[nulls] bloqueantes: {len(result['blockers'])}")
    print(f"[nulls] reporte -> {result['out_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
