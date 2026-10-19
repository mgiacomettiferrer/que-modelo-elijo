"""Etapa 3 - normalize.

Limpio -> `data/interim/models_scaled.parquet` (features escaladas)
       -> `data/processed/llm_features.parquet` (contrato completo)

Escalado: **RobustScaler** (mediana / IQR) implementado con numpy, sin
dependencia de scikit-learn para esta etapa. Las features de clustering son
solo rendimiento + los ejes de calidad; el precio y la metadata nunca se
escalan para la distancia.

Uso:
    python -m src.normalize --in data/interim/models_clean.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import frame, schema

WINSOR_LIMITS = (0.01, 0.99)


def winsorize(series: pd.Series, limits: tuple[float, float] = WINSOR_LIMITS) -> pd.Series:
    """Recorta la cola a los cuantiles dados. Necesita al menos 5 valores."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() < 5:
        return numeric
    low, high = numeric.quantile(limits[0]), numeric.quantile(limits[1])
    return numeric.clip(lower=low, upper=high)


def robust_scale(series: pd.Series) -> pd.Series:
    """(x - mediana) / IQR. Si el IQR es 0 la senal es constante: devuelve 0."""
    numeric = pd.to_numeric(series, errors="coerce")
    median = numeric.median()
    q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return pd.Series(0.0, index=series.index, dtype="float64").where(numeric.notna())
    return (numeric - median) / iqr


def run(in_path: Path, interim_dir: Path, processed_dir: Path) -> dict:
    clean = pd.read_parquet(in_path)

    # Idempotente: si el limpio ya trae los ejes, no se recalculan.
    if "quality_general" not in clean.columns:
        clean = frame.add_axis_aggregates(clean)

    # Un benchmark por dimension: el de menos nulos. Los ejes agregados **no**
    # son features de clustering (ver `schema._axis_columns`).
    selection = frame.select_dimension_benchmarks(clean)
    features = frame.training_features(selection)

    scaled = pd.DataFrame(index=clean.index)
    for key in ("model_id", "canonical_slug", "name", "provider", "family"):
        if key in clean.columns:
            scaled[key] = clean[key]

    feature_report: dict[str, dict] = {}
    for feature in features:
        if feature not in clean.columns:
            continue
        raw = pd.to_numeric(clean[feature], errors="coerce")
        if feature in schema.BENCHMARK_COLUMNS:
            # Benchmark suelto: rank percentil antes de escalar, para que la
            # escala propia del leaderboard no entre en la distancia.
            prepared = raw.rank(pct=True)
            transform = "rank percentil -> RobustScaler"
        else:
            prepared = winsorize(raw)
            transform = f"winsor {WINSOR_LIMITS} -> RobustScaler"

        scaled[feature] = raw.astype("float64")
        scaled[f"{feature}_scaled"] = robust_scale(prepared)
        scaled[frame.missing_indicator_name(feature)] = raw.isna().astype("boolean")
        feature_report[feature] = {
            "n_validos": int(raw.notna().sum()),
            "pct_nulos": round(float(raw.isna().mean() * 100), 2),
            "transform": transform,
        }

    for axis in schema.QUALITY_AXES:
        column = f"quality_{axis}_n_sources"
        if column in clean.columns:
            scaled[column] = clean[column]

    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # La eleccion tiene que quedar registrada: cambia entre corridas si cambia
    # la cobertura, y sin registro el clustering dejaria de ser reproducible.
    selection_path = interim_dir / "dimension_selection.json"
    selection_path.write_text(
        json.dumps(
            {
                "criterio": "benchmark con menos nulos por dimension, medido sobre el universo",
                "n_rows": len(clean),
                "seleccion": selection,
                "features": list(features),
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )

    scaled_path = interim_dir / "models_scaled.parquet"
    frame.persist(scaled, scaled_path)

    # El contrato: columnas canonicas + ejes (reporte) + indicadores de faltante.
    features_path = processed_dir / "llm_features.parquet"
    frame.persist(clean, features_path)

    return {
        "scaled_path": str(scaled_path),
        "features_path": str(features_path),
        "selection_path": str(selection_path),
        "n_rows": int(len(clean)),
        "features": feature_report,
        "selection": selection,
        "feature_names": list(features),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Etapa 3: normalizacion.")
    parser.add_argument("--in", dest="in_path", type=Path, default=Path("data/interim/models_clean.parquet"))
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)

    result = run(args.in_path, args.interim_dir, args.processed_dir)
    print(f"[normalize] escalado -> {result['scaled_path']}")
    print(f"[normalize] contrato -> {result['features_path']}")
    print(f"[normalize] seleccion -> {result['selection_path']}")
    print(f"[normalize] {result['n_rows']} filas, {len(result['feature_names'])} features")
    for dimension, entry in result["selection"].items():
        state = f"{entry['n_valid']} validos" if entry["n_valid"] else "SIN DATOS (fuera)"
        print(
            f"[normalize]   {dimension:14s} <- {entry['benchmark']:26s} "
            f"({entry['source']}, de {entry['candidates']} candidatos) {state}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
