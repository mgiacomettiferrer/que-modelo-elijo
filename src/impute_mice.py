"""Imputacion de las features de clustering por MICE (`IterativeImputer`).

MICE imputa cada celda faltante regresandola contra las demas features
observadas de esa fila. Dos consecuencias que hay que mirar de frente antes de
creerle al resultado:

1. **Una fila sin ningun dato observado no se puede imputar.** No hay variables
   explicativas, asi que el imputador devuelve la media de la columna. Eso no es
   imputar: es inventar. Esas filas quedan nulas y marcadas, no rellenadas.
2. **Con cobertura baja, las regresiones se ajustan sobre pocas filas.** Si una
   feature tiene 26 valores y otra 39, el par completo puede ser de 20 casos.
   La validacion de este modulo mide si, aun asi, MICE le gana a imputar la
   mediana. Si no le gana, el metodo no aporta y hay que decirlo.

La validacion tapa una celda observada por fila, imputa y compara contra el
valor real. Es la unica forma honesta de saber si la imputacion tiene
informacion o solo ruido.

Uso:
    python -m src.impute_mice --in data/interim/models_scaled.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

SEED = 42
MAX_ITER = 20


def imputable_mask(matrix: np.ndarray) -> np.ndarray:
    """Filas con al menos un valor observado: las unicas que MICE puede usar."""
    return (~np.isnan(matrix)).any(axis=1)


def fit_impute(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """Ajusta MICE sobre las filas utiles y devuelve la matriz imputada.

    Devuelve (matriz, filas_usadas, n_filas_excluidas). Las filas sin ningun
    dato quedan como estaban (todo NaN): rellenarlas seria fabricar.
    """
    usable = imputable_mask(matrix)
    result = matrix.copy()
    if usable.sum() == 0:
        return result, usable, int((~usable).sum())

    imputer = IterativeImputer(
        random_state=SEED,
        max_iter=MAX_ITER,
        sample_posterior=False,
    )
    filled = imputer.fit_transform(matrix[usable])
    result[usable] = filled
    return result, usable, int((~usable).sum())


def clip_to_observed(original: np.ndarray, imputed: np.ndarray) -> np.ndarray:
    """Recorta cada valor imputado al rango observado de su columna.

    Imputar fuera del rango visto es extrapolar; MICE puede hacerlo porque la
    regresion no conoce limites. Se recorta y se informa.
    """
    out = imputed.copy()
    for j in range(original.shape[1]):
        column = original[:, j]
        observed = column[~np.isnan(column)]
        if observed.size == 0:
            continue
        missing = np.isnan(column) & ~np.isnan(out[:, j])
        out[missing, j] = np.clip(out[missing, j], observed.min(), observed.max())
    return out


def validate(matrix: np.ndarray) -> tuple[pd.DataFrame, int]:
    """Tapa una celda observada por fila, imputa y mide el error.

    Compara MICE contra imputar la mediana, que es el piso que cualquier metodo
    tiene que superar para justificarse.
    """
    rng = np.random.default_rng(SEED)
    holes: list[tuple[int, int]] = []
    for i in range(matrix.shape[0]):
        observed = np.flatnonzero(~np.isnan(matrix[i]))
        if observed.size < 2:  # sin dos datos no hay nada que aprender de la fila
            continue
        holes.append((i, int(rng.choice(observed))))
    if not holes:
        return pd.DataFrame(), 0

    masked = matrix.copy()
    truth = {j: [] for j in range(matrix.shape[1])}
    for i, j in holes:
        truth[j].append(matrix[i, j])
        masked[i, j] = np.nan

    mice, usable, _ = fit_impute(masked)
    mice = clip_to_observed(masked, mice)

    median_filled = masked.copy()
    for j in range(matrix.shape[1]):
        column = masked[:, j]
        observed = column[~np.isnan(column)]
        if observed.size == 0:
            continue
        median_filled[np.isnan(column), j] = np.median(observed)

    rows = []
    for j in sorted(truth):
        if not truth[j]:
            continue
        idx = [i for i, jj in holes if jj == j]
        real = np.array(truth[j], dtype=float)
        guess = np.array([mice[i, j] for i in idx], dtype=float)
        baseline = np.array([median_filled[i, j] for i in idx], dtype=float)
        ok = ~np.isnan(guess)
        if ok.sum() == 0:
            continue
        mae_mice = float(np.mean(np.abs(guess[ok] - real[ok])))
        mae_med = float(np.mean(np.abs(baseline[ok] - real[ok])))
        rows.append(
            {
                "columna": j,
                "n": int(ok.sum()),
                "mae_mice": mae_mice,
                "mae_mediana": mae_med,
                "rmse_mice": float(np.sqrt(np.mean((guess[ok] - real[ok]) ** 2))),
                "rmse_mediana": float(np.sqrt(np.mean((baseline[ok] - real[ok]) ** 2))),
                "cociente": mae_mice / mae_med if mae_med > 0 else float("nan"),
            }
        )
    return pd.DataFrame(rows), len(holes)


def run(
    source: Path,
    selection: Path,
    out: Path,
    report: Path,
    scaled: bool = True,
) -> dict:
    frame = pd.read_parquet(source)
    features: list[str] = json.loads(selection.read_text(encoding="utf-8"))["features"]
    features = [f for f in features if f in frame.columns]

    # El clustering consume las columnas escaladas. Imputar sobre las crudas y
    # escalar despues obligaria a re-escalar con valores imputados dentro; al
    # reves es mas simple y no cambia el orden de las filas.
    columns = [
        f"{f}_scaled" if scaled and f"{f}_scaled" in frame.columns else f
        for f in features
    ]
    matrix = frame[columns].to_numpy(dtype=float)
    observed = ~np.isnan(matrix)

    # Diagnostico estructural antes de imputar.
    per_row = observed.sum(axis=1)
    imputable = imputable_mask(matrix)
    pairs = {}
    for a in range(len(features)):
        for b in range(a + 1, len(features)):
            pairs[(features[a], features[b])] = int(
                (observed[:, a] & observed[:, b]).sum()
            )

    imputed, usable, excluded = fit_impute(matrix)
    imputed = clip_to_observed(matrix, imputed)

    flags = np.isnan(matrix) & ~np.isnan(imputed)
    for j, feature in enumerate(features):
        frame[f"{feature}_imputed"] = flags[:, j]
    for j, column in enumerate(columns):
        frame[column] = imputed[:, j]

    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)

    validation, n_holes = validate(matrix)

    lines = [
        "# Imputacion MICE de las features de clustering",
        "",
        f"- Entrada: `{source.name}`",
        f"- Columnas imputadas: {', '.join('`' + c + '`' for c in columns[:3])}"
        + (" …" if len(columns) > 3 else ""),
        f"- Filas: {len(frame)}",
        f"- Features: {len(features)}",
        f"- Filas con al menos un dato (imputables): {int(usable.sum())}",
        f"- Filas sin ningun dato (excluidas): {excluded}",
        f"- Celdas imputadas: {int(flags.sum())}",
        "",
        "## Por que las filas vacias quedan nulas",
        "",
        "MICE regresiona cada faltante contra las otras features de la misma fila.",
        "Si la fila no tiene **ninguna** observacion, no hay regresores: el",
        "imputador devuelve la media de la columna. Eso no es una estimacion del",
        "modelo, es la media con otro nombre. Esas filas se dejan nulas y marcadas",
        f"en sus columnas `_imputed`, que quedan en `False`. Son {excluded} de",
        f"{len(frame)}.",
        "",
        "## Celdas imputadas por feature",
        "",
        "| Feature | Observadas | Imputadas | Cobertura final |",
        "|---|---:|---:|---:|",
    ]
    for j, feature in enumerate(features):
        n_obs = int(observed[:, j].sum())
        n_imp = int(flags[:, j].sum())
        total = len(frame)
        lines.append(
            f"| `{feature}` | {n_obs} | {n_imp} | {round((n_obs + n_imp) / total * 100, 1)}% |"
        )

    lines += [
        "",
        "## Validacion: MICE contra la mediana",
        "",
        f"Se tapo una celda observada por fila en {n_holes} filas con al menos dos",
        "datos, se imputo y se comparo contra el valor real. La mediana es el piso",
        "que cualquier metodo tiene que superar para justificarse.",
        "",
    ]
    if validation.empty:
        lines.append("Sin filas suficientes para validar.")
    else:
        lines += [
            "| Feature | n | MAE MICE | MAE mediana | Cociente | RMSE MICE | RMSE mediana |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in validation.itertuples():
            name = features[int(row.columna)]
            lines.append(
                f"| `{name}` | {row.n} | {row.mae_mice:.4f} | {row.mae_mediana:.4f} | "
                f"{row.cociente:.2f} | {row.rmse_mice:.4f} | {row.rmse_mediana:.4f} |"
            )
        better = int((validation["cociente"] < 1).sum())
        lines += [
            "",
            "El cociente es MAE MICE / MAE mediana: **menor que 1 significa que MICE",
            "gana**. Se usa el cociente y no el MAE absoluto porque este ultimo esta en",
            "unidades escaladas y no es comparable entre features.",
            "",
            f"MICE mejora a la mediana en **{better} de {len(validation)}** features.",
        ]

    lines += [
        "",
        "## Pares con menos casos completos",
        "",
        "Cada regresion de MICE se ajusta sobre las filas donde el par",
        "(feature a imputar, feature explicativa) tiene ambos valores. Estos son los",
        "pares mas flacos: con pocos casos, la estimacion es fragil aunque el",
        "algoritmo converja.",
        "",
        "| Par | Casos completos |",
        "|---|---:|",
    ]
    for (a, b), n in sorted(pairs.items(), key=lambda kv: kv[1])[:8]:
        lines.append(f"| `{a}` x `{b}` | {n} |")
    lines.append("")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    return {
        "filas": len(frame),
        "imputables": int(usable.sum()),
        "excluidas": excluded,
        "celdas": int(flags.sum()),
        "mice_gana": int((validation["cociente"] < 1).sum())
        if not validation.empty
        else 0,
        "features_validadas": len(validation),
        "reporte": str(report),
        "salida": str(out),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="source", default="data/interim/models_scaled.parquet")
    parser.add_argument("--selection", default="data/interim/dimension_selection.json")
    parser.add_argument("--out", default="data/processed/llm_features_imputed_2026-10-19.parquet")
    parser.add_argument("--report", default="data/interim/mice_report_2026-10-19.md")
    parser.add_argument(
        "--no-scaled",
        action="store_true",
        help="imputar sobre las columnas crudas en vez de las `_scaled`",
    )
    args = parser.parse_args(argv)

    summary = run(
        Path(args.source),
        Path(args.selection),
        Path(args.out),
        Path(args.report),
        scaled=not args.no_scaled,
    )
    print(f"[mice] filas: {summary['filas']}")
    print(f"[mice] imputables: {summary['imputables']} | excluidas sin datos: {summary['excluidas']}")
    print(f"[mice] celdas imputadas: {summary['celdas']}")
    print(f"[mice] MICE mejora a la mediana en {summary['mice_gana']} de {summary['features_validadas']}")
    print(f"[mice] salida -> {summary['salida']}")
    print(f"[mice] reporte -> {summary['reporte']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
