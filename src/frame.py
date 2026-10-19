"""Armado del DataFrame canonico.

Centraliza dos cosas que no deben duplicarse entre etapas:

1. **Tipos y faltantes**: todas las columnas del contrato existen siempre, con
   el dtype declarado en `schema.COLUMNS`, y toda feature con nulos lleva su
   indicador `<feature>_missing` (convencion: un ausente no es 0).
2. **Agregacion por eje**: los benchmarks crudos se convierten a rank percentil
   y se promedian por eje. Cada eje entra al clustering como **una sola**
   feature, para que la calidad no pese una vez por benchmark.
"""

from __future__ import annotations

import pandas as pd

from . import schema

# dtype declarado -> dtype de pandas (nullable donde tiene sentido).
PANDAS_DTYPE: dict[str, str] = {
    "str": "string",
    "float64": "float64",
    "bool": "boolean",
    "int64": "Int64",
    "datetime64[ns]": "datetime64[ns]",
}

# Columnas que llevan indicador de faltante: rendimiento + todos los benchmarks
# crudos (superconjunto de cualquier seleccion por dimension).
MISSING_INDICATOR_FOR: tuple[str, ...] = tuple(schema.BASE_FEATURES) + tuple(
    schema.BENCHMARK_COLUMNS
)


def missing_indicator_name(column: str) -> str:
    return f"{column}_missing"


def _cast(series: pd.Series, dtype: str) -> pd.Series:
    """Casteo defensivo: un dtype inesperado no debe romper la etapa.

    `Series.astype(..., errors="ignore")` fue removido en pandas 3.0. Ademas,
    una columna creada con `pd.NA` queda como `object` y su `astype("float64")`
    puede fallar, por eso los numericos pasan por `to_numeric`.
    """
    try:
        if dtype == "float64":
            return pd.to_numeric(series, errors="coerce").astype("float64")
        if dtype == "datetime64[ns]":
            return pd.to_datetime(series, errors="coerce")
        target = PANDAS_DTYPE.get(dtype, dtype)
        return series.astype(target)
    except (TypeError, ValueError):
        return series


def assemble(rows: list[dict]) -> pd.DataFrame:
    """Filas canonicas -> DataFrame completo con dtypes y faltantes."""
    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame(columns=[c.name for c in schema.COLUMNS])

    # Descarta claves internas y columnas fuera del contrato.
    internal = [c for c in frame.columns if c.startswith("_")]
    if internal:
        frame = frame.drop(columns=internal)

    ordered: list[str] = []
    for column in schema.COLUMNS:
        if column.name not in frame.columns:
            frame[column.name] = pd.NA
        frame[column.name] = _cast(frame[column.name], column.dtype)
        ordered.append(column.name)

    # Benchmarks crudos: un slot = una version + un host.
    for name in schema.BENCHMARK_COLUMNS:
        if name not in frame.columns:
            frame[name] = pd.NA
        frame[name] = _cast(frame[name], "float64")
        ordered.append(name)

    # Indicadores de faltante antes de cualquier imputacion.
    for name in MISSING_INDICATOR_FOR:
        if name in frame.columns:
            indicator = missing_indicator_name(name)
            frame[indicator] = frame[name].isna().astype("boolean")
            ordered.append(indicator)

    return frame.loc[:, ordered]


def add_axis_aggregates(frame: pd.DataFrame) -> pd.DataFrame:
    """Agrega `quality_<eje>` y `quality_<eje>_n_sources`.

    Cada benchmark crudo pasa a rank percentil sobre el universo y luego se
    promedia dentro del eje. Un modelo sin ningun benchmark de un eje queda
    nulo en ese eje, con `n_sources = 0`: nunca se completa con la mediana.
    """
    out = frame.copy()
    by_axis: dict[str, list[str]] = {axis: [] for axis in schema.QUALITY_AXES}
    for slot in schema.BENCHMARK_SLOTS:
        by_axis[slot.axis].append(slot.column)

    for axis, columns in by_axis.items():
        present = [c for c in columns if c in out.columns]
        if not present:
            out[f"quality_{axis}"] = pd.Series(pd.NA, index=out.index, dtype="float64")
            out[f"quality_{axis}_n_sources"] = pd.Series(0, index=out.index, dtype="Int64")
            out[f"quality_{axis}_missing"] = pd.Series(True, index=out.index, dtype="boolean")
            continue

        ranks = pd.DataFrame(index=out.index)
        for column in present:
            numeric = pd.to_numeric(out[column], errors="coerce")
            ranks[column] = numeric.rank(pct=True)

        source_count = ranks.notna().sum(axis=1)
        mean_rank = ranks.mean(axis=1, skipna=True).where(source_count > 0)

        out[f"quality_{axis}"] = mean_rank.astype("float64")
        out[f"quality_{axis}_n_sources"] = source_count.astype("Int64")
        indicator = f"quality_{axis}_missing"
        out[indicator] = (source_count == 0).astype("boolean")
    return out


def column_order(frame: pd.DataFrame) -> list[str]:
    """Orden estable: contrato primero, indicadores al final."""
    contract = [c.name for c in schema.COLUMNS]
    extras = [c for c in frame.columns if c not in contract]
    return [c for c in contract if c in frame.columns] + sorted(extras)


def persist(frame: pd.DataFrame, path) -> None:
    """Escribe Parquet en UTF-8 sin BOM, con dtypes ya casteados."""
    from pathlib import Path

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.loc[:, column_order(frame)].to_parquet(out, engine="pyarrow", index=False)


# --------------------------------------------------------------------------
# Seleccion de la feature por dimension
# --------------------------------------------------------------------------


def benchmark_columns_by_dimension() -> dict[str, list[str]]:
    """Dimension -> benchmarks crudos declarados en el esquema."""
    by_dimension: dict[str, list[str]] = {d: [] for d in schema.DIMENSIONS}
    for slot in schema.BENCHMARK_SLOTS:
        by_dimension[slot.axis].append(slot.column)
    return by_dimension


def select_dimension_benchmarks(frame: pd.DataFrame) -> dict[str, dict]:
    """Para cada dimension, el benchmark con **menos nulos**.

    Motivo: promediar ranks de benchmarks que no cubren a los mismos modelos
    hace que dos filas con el mismo valor de eje no sean la misma medicion. Con
    cobertura parcial ese promedio no es interpretable; un benchmark unico si.

    Desempate determinista (nombre de columna ascendente) para que la eleccion
    sea reproducible entre corridas.
    """
    selection: dict[str, dict] = {}
    n_rows = len(frame)
    for dimension, columns in benchmark_columns_by_dimension().items():
        present = [c for c in columns if c in frame.columns]
        if not present:
            continue
        ranked = [
            (int(pd.to_numeric(frame[c], errors="coerce").notna().sum()), c)
            for c in present
        ]
        # Mas valores validos primero; a igualdad, nombre alfabeticamente menor.
        n_valid, column = min(ranked, key=lambda pair: (-pair[0], pair[1]))
        selection[dimension] = {
            "benchmark": column,
            "n_valid": n_valid,
            "pct_null": round((1 - n_valid / n_rows) * 100, 2) if n_rows else 100.0,
            "candidates": len(present),
            "source": next(
                (s.host for s in schema.BENCHMARK_SLOTS if s.column == column), "?"
            ),
        }
    return selection


def training_features(selection: dict[str, dict]) -> tuple[str, ...]:
    """Features de clustering: rendimiento + un benchmark por dimension.

    Una dimension sin ningun dato queda fuera: seria una columna vacia en la
    matriz de distancia.
    """
    selected = sorted(
        entry["benchmark"] for entry in selection.values() if entry["n_valid"] > 0
    )
    return tuple(schema.BASE_FEATURES) + tuple(selected)
