"""PCA sobre las 6 features de clustering, quedando con 2 componentes.

Por que: las seis features tienen mucha redundancia. La correlacion entre las
cuatro de calidad va de 0.61 a 0.84, y la latencia correlaciona 0.77 con
`professional`. Clusterizar en 6 dimensiones cuando hay una o dos efectivas hace
que la distancia cuente la misma informacion varias veces, y ademas vuelve
imposible mostrar el resultado: no se puede dibujar un espacio de 6 ejes.

Quedarse con 2 componentes da un plano que se puede graficar y que conserva la
mayor parte de la estructura. Los componentes se calculan sobre las features ya
normalizadas, asi que equivalen al PCA de la matriz de correlacion.

Uso:
    python -m src.aa_pca --in data/processed/aa_tabla_zscore_2026-10-19.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

EXCLUDED_BASE = {"data_z"}
IDENTITY = ["aa_slug", "aa_name", "creator_name"]
N_COMPONENTS = 2


def build(
    source: Path,
    out: Path,
    out_csv: Path,
    report: Path,
    exclude: set[str] | None = None,
) -> dict:
    excluded = EXCLUDED_BASE | (exclude or set())
    frame = pd.read_parquet(source)
    features = [c for c in frame.columns if c.endswith("_z") and c not in excluded]
    matrix = frame[features].to_numpy(dtype=float)
    if np.isnan(matrix).any():
        raise SystemExit("[pca] hay faltantes en la matriz")

    # Se ajusta el PCA completo para poder informar todos los autovalores,
    # aunque la salida se quede con los dos primeros componentes.
    full = PCA().fit(matrix)
    pca = PCA(n_components=N_COMPONENTS)
    scores = pca.fit_transform(matrix)

    ratios = full.explained_variance_ratio_
    cumulative = np.cumsum(ratios)
    loadings = pd.DataFrame(
        pca.components_.T,
        index=[f.replace("_z", "") for f in features],
        columns=[f"PC{i + 1}" for i in range(N_COMPONENTS)],
    )

    result = frame[[c for c in IDENTITY if c in frame.columns]].copy()
    for i in range(N_COMPONENTS):
        result[f"pc{i + 1}"] = scores[:, i]
    result = result.sort_values("pc1", ascending=False).reset_index(drop=True)

    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out, index=False)
    result.to_csv(out_csv, index=False, encoding="utf-8")

    lines = [
        "# PCA de las features de clustering",
        "",
        f"- Entrada: `{source.name}`",
        f"- Filas: {len(frame)} | variables originales: {len(features)}",
        "- Variables: " + ", ".join(f"`{f}`" for f in features),
        "- Excluidas: " + ", ".join(f"`{e}`" for e in sorted(excluded)),
        f"- Componentes retenidos: {N_COMPONENTS}",
        "- Las features ya venian normalizadas, asi que esto equivale al PCA de la",
        "  matriz de correlacion.",
        "",
        "## Varianza por componente",
        "",
        "| Componente | Autovalor | Varianza | Acumulada |",
        "|---|---:|---:|---:|",
    ]
    for i, (value, share, acc) in enumerate(
        zip(full.explained_variance_, ratios, cumulative), start=1
    ):
        mark = " **" if i <= N_COMPONENTS else ""
        lines.append(f"| PC{i}{mark} | {value:.3f} | {share:.3f} | {acc:.3f} |")

    lines += [
        "",
        f"Los {N_COMPONENTS} componentes retenidos conservan "
        f"**{cumulative[N_COMPONENTS - 1]:.1%}** de la varianza. "
        f"El resto ({1 - cumulative[N_COMPONENTS - 1]:.1%}) se descarta.",
        "",
        "## Cargas (que mide cada componente)",
        "",
        "| Feature | PC1 | PC2 |",
        "|---|---:|---:|",
    ]
    for feature in loadings.index:
        lines.append(f"| {feature} | {loadings.loc[feature, 'PC1']:+.3f} | {loadings.loc[feature, 'PC2']:+.3f} |")

    lines += [
        "",
        "## Coordenadas de cada modelo",
        "",
        "| Modelo | Proveedor | PC1 | PC2 |",
        "|---|---|---:|---:|",
    ]
    for row in result.itertuples():
        lines.append(
            f"| {row.aa_name} | {row.creator_name} | {row.pc1:+.2f} | {row.pc2:+.2f} |"
        )
    lines.append("")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    return {
        "filas": len(frame),
        "features": len(features),
        "varianza": float(cumulative[N_COMPONENTS - 1]),
        "ratios": ratios,
        "loadings": loadings,
        "out": str(out),
        "report": str(report),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in", dest="source", default="data/processed/aa_tabla_zscore_2026-10-19.parquet"
    )
    parser.add_argument("--out", default="data/processed/aa_pca_2026-10-19.parquet")
    parser.add_argument("--csv", default="data/interim/aa_pca_scores_2026-10-19.csv")
    parser.add_argument("--report", default="data/interim/aa_pca_report_2026-10-19.md")
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="columna `_z` a excluir del PCA (repetible)",
    )
    args = parser.parse_args(argv)

    summary = build(
        Path(args.source),
        Path(args.out),
        Path(args.csv),
        Path(args.report),
        exclude=set(args.exclude or []),
    )
    print(f"[pca] filas: {summary['filas']} | variables: {summary['features']}")
    print(f"[pca] varianza explicada = {summary['varianza']:.3f} con 2 componentes")
    print("[pca] cargas:")
    print(summary["loadings"].round(3).to_string())
    print(f"[pca] salida -> {summary['out']}")
    print(f"[pca] reporte -> {summary['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
