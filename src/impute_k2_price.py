"""Imputacion del precio de K2 Horizon por regresion multiple (MICE).

Antes de correr, dos precisiones sobre que se esta haciendo:

1. El precio de K2 Horizon **no esta nulo**: viene como 0.00 en entrada y salida,
   y sin tarifa de cache. Un cero publicado no es un faltante, es un precio que
   la fuente informa como cero porque el modelo no se vende por API. Para
   imputarlo hay que tratarlo como faltante a proposito, y eso es una decision
   editorial, no un dato.

2. MICE sobre una sola celda no itera: con un unico valor faltante, el algoritmo
   converge en el primer paso y equivale a **una regresion multiple**. Se usa
   `IterativeImputer` igual porque es el metodo pedido, pero el resultado es un
   punto estimado por BayesianRidge, sin intervalo.

La senal mas fuerte para predecir el precio no son los benchmarks: es el otro
precio. Entrada y salida se mueven juntas, asi que se ponen las tres tarifas en
la matriz y el imputador usa la correlacion entre ellas.

Se valida con leave-one-out sobre los 23 modelos que si tienen precio: a cada uno
se le tapa el precio, se imputa con los otros 22 y se compara contra el real. Si
el error de esa prediccion es grande, el numero que se le asigne a K2 no merece
mas confianza que la mediana del conjunto.

Uso:
    python -m src.impute_k2_price
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

SEED = 42
TARGET_SLUG = "k2-horizon-375b-a23b"

# Precios: se modelan en log porque van de 0.1 a 50 USD por millon.
PRICES = [
    "price_in_usd_per_mtok",
    "price_out_usd_per_mtok",
    "price_cache_hit_usd_per_mtok",
]
# Variables tecnicas como regresores.
TECH = [
    "speed_tok_s",
    "gdpval_normalized_pct",
    "scicode_pct",
    "terminal_bench_4_0_pct",
    "gdp_pdf_all_pass_pct",
    "context_window_tokens",
]


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    """Matriz de trabajo: precios en log1p y regresores en log1p donde aplica."""
    work = frame[["aa_slug", "aa_name"] + PRICES + TECH].copy()
    for column in PRICES:
        work[column] = np.log1p(pd.to_numeric(work[column], errors="coerce"))
    work["speed_tok_s"] = np.log1p(pd.to_numeric(work["speed_tok_s"], errors="coerce"))
    work["context_window_tokens"] = np.log1p(
        pd.to_numeric(work["context_window_tokens"], errors="coerce")
    )
    for column in TECH:
        if column not in {"speed_tok_s", "context_window_tokens"}:
            work[column] = pd.to_numeric(work[column], errors="coerce")
    return work


def impute(matrix: np.ndarray) -> np.ndarray:
    model = IterativeImputer(random_state=SEED, max_iter=20, sample_posterior=False)
    return model.fit_transform(matrix)


def build(source: Path, cluster_source: Path) -> dict:
    raw = pd.read_parquet(source)
    members = pd.read_parquet(cluster_source)[["aa_slug"]]
    frame = raw.merge(members, on="aa_slug", how="inner")
    work = prepare(frame)

    columns = PRICES + TECH
    values = work[columns].to_numpy(dtype=float)
    target = work.index[work["aa_slug"] == TARGET_SLUG]
    if len(target) == 0:
        raise SystemExit("[k2] el modelo no esta en el conjunto")
    row = int(target[0])

    cero_original = {
        c: float(frame.loc[frame["aa_slug"] == TARGET_SLUG, c].iloc[0]) for c in PRICES
    }

    # Se tratan los precios de K2 como faltantes y se imputan.
    values_imputed = values.copy()
    values_imputed[row, : len(PRICES)] = np.nan
    filled = impute(values_imputed)
    predicted = {
        column: float(np.expm1(filled[row, j])) for j, column in enumerate(PRICES)
    }

    # Validacion leave-one-out sobre los modelos con precio publicado.
    errors: dict[str, list[tuple[float, float]]] = {c: [] for c in PRICES}
    for i in range(len(values)):
        if i == row:
            continue
        masked = values.copy()
        truth = {}
        for j, column in enumerate(PRICES):
            if not np.isnan(masked[i, j]):
                truth[column] = masked[i, j]
                masked[i, j] = np.nan
        if not truth:
            continue
        loo = impute(masked)
        for column, real in truth.items():
            j = PRICES.index(column)
            guess = loo[i, j]
            if not np.isnan(guess):
                errors[column].append((real, guess))

    stats = {}
    for column, pairs in errors.items():
        if not pairs:
            continue
        real = np.array([p[0] for p in pairs])
        guess = np.array([p[1] for p in pairs])
        median = float(np.median(real))
        stats[column] = {
            "n": len(pairs),
            "mae": float(np.mean(np.abs(guess - real))),
            "mae_mediana": float(np.mean(np.abs(median - real))),
            "cociente": float(np.mean(np.abs(guess - real)) / np.mean(np.abs(median - real)))
            if np.mean(np.abs(median - real)) > 0
            else float("nan"),
        }

    return {
        "cero_original": cero_original,
        "previsto": predicted,
        "stats": stats,
        "cluster": (
            frame.loc[frame["aa_slug"] == TARGET_SLUG, "aa_name"].iloc[0]
        ),
    }


def apply_minimum(source: Path, clusters: Path, out: Path) -> dict:
    """Asigna a K2 el precio minimo observado del dataset.

    Se usa el minimo entre los precios positivos: el 0.00 de K2 no es un precio,
    es la ausencia de tarifa, y si entrara en el calculo el minimo seria cero y
    no se estaria imputando nada.

    Es una cota superior de baratura: asumir el menor precio del conjunto nunca
    hace que el modelo parezca mas caro de lo que podria ser. Queda marcado con
    `price_imputed` para que no se confunda con una tarifa publicada.
    """
    raw = pd.read_parquet(source)
    members = pd.read_parquet(clusters)[["aa_slug"]]
    frame = raw.merge(members, on="aa_slug", how="inner").copy()

    prices = [c for c in PRICES if c in frame.columns]
    minima: dict[str, float] = {}
    for column in prices:
        values = pd.to_numeric(frame[column], errors="coerce")
        positive = values[values > 0]
        minima[column] = float(positive.min())

    mask = frame["aa_slug"] == TARGET_SLUG
    frame["price_imputed"] = False
    frame["price_imputation_method"] = ""
    for column in prices:
        frame.loc[mask, column] = minima[column]
    frame.loc[mask, "price_imputed"] = True
    frame.loc[mask, "price_imputation_method"] = "minimo observado del dataset"

    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)

    positives = frame[~frame["price_imputed"]].copy()
    positives["blended"] = (
        positives["price_in_usd_per_mtok"] + positives["price_out_usd_per_mtok"]
    ) / 2
    cheapest = positives.nsmallest(3, "blended")[["aa_name", "blended"]]

    return {
        "minimos": minima,
        "filas": len(frame),
        "out": str(out),
        "mas_baratos_sin_k2": cheapest.to_dict("records"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="source", default="data/processed/aa_models_2026-10-19.parquet")
    parser.add_argument(
        "--clusters", dest="clusters", default="data/processed/aa_clusters_k4_2026-10-19.parquet"
    )
    parser.add_argument(
        "--apply-min",
        action="store_true",
        help="en vez de MICE, asignar a K2 el precio minimo observado del dataset",
    )
    parser.add_argument(
        "--out", default="data/processed/aa_models_priced_2026-10-19.parquet"
    )
    args = parser.parse_args(argv)

    if args.apply_min:
        result = apply_minimum(Path(args.source), Path(args.clusters), Path(args.out))
        print("[k2] minimos observados (USD/1M):")
        for column, value in result["minimos"].items():
            print(f"  {column:<34}{value}")
        print()
        print("[k2] los mas baratos sin contar a K2, con blended 1:1:")
        for item in result["mas_baratos_sin_k2"]:
            print(f"  {item['aa_name']:<38}{item['blended']:.3f}")
        print()
        print(f"[k2] salida -> {result['out']}")
        return 0

    result = build(Path(args.source), Path(args.clusters))
    print(f"[k2] modelo: {result['cluster']}")
    print(f"[k2] valores publicados: { {k: round(v, 2) for k, v in result['cero_original'].items()} }")
    print(f"[k2] imputados (USD/1M): { {k: round(v, 4) for k, v in result['previsto'].items()} }")
    print()
    print("[k2] validacion leave-one-out sobre los que si tienen precio:")
    for column, s in result["stats"].items():
        print(
            f"  {column:<32} n={s['n']:<3} MAE={s['mae']:.3f} "
            f"MAE mediana={s['mae_mediana']:.3f} cociente={s['cociente']:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
