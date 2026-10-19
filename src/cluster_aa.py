"""KMeans sobre la tabla de Artificial Analysis sin la feature `data`.

Entrada: `aa_tabla_zscore_2026-10-19.parquet`, que ya trae las features
normalizadas. Se usan 6 de las 7: `data` queda afuera porque solo tiene 16 de 24
valores y entrenar con ella obligaria a descartar 8 modelos y 6 proveedores.

Transformaciones aplicadas (vienen del paso de normalizacion, no se repiten aca):
`log1p` antes del z-score en `speed_tok_s` y `latency_ttft_s`, que tienen cola
pesada; z-score puro en las cuatro de calidad. Todas quedaron con IQR de z entre
1,13 y 1,77, asi que pesan parecido en la distancia euclidiana.

Se prueban k = 3, 4, 5 y 6. La eleccion final no se hace por un solo numero: la
metodologia del repo pide silueta razonable **y** cluster minimo de 5 miembros
con N=24. Un k con mejor silueta pero un cluster de 2 modelos no sirve para
describir nada.

Uso:
    python -m src.cluster_aa --in data/processed/aa_tabla_zscore_2026-10-19.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

SEED = 42
N_INIT = 10
K_VALUES = (3, 4, 5, 6)
MIN_CLUSTER = 5

# Features de entrenamiento: las 7 menos `data`.
EXCLUDED = {"data_z"}
IDENTITY = ["aa_slug", "aa_name", "creator_name"]


def evaluate(matrix: np.ndarray) -> pd.DataFrame:
    """Ajusta KMeans para cada k y devuelve una fila de indicadores por k."""
    total_ss = float(((matrix - matrix.mean(axis=0)) ** 2).sum())
    rows = []
    for k in K_VALUES:
        model = KMeans(n_clusters=k, random_state=SEED, n_init=N_INIT)
        labels = model.fit_predict(matrix)

        within = float(model.inertia_)  # WCSS: suma de cuadrados intra-cluster
        between = total_ss - within  # BCSS: suma de cuadrados entre clusters
        sizes = np.bincount(labels, minlength=k)
        rows.append(
            {
                "k": k,
                "inercia_wcss": within,
                "entre_bcss": between,
                "total_tss": total_ss,
                "ratio_entre_dentro": between / within if within else float("nan"),
                "varianza_explicada": between / total_ss if total_ss else float("nan"),
                "calinski_harabasz": float(calinski_harabasz_score(matrix, labels)),
                "davies_bouldin": float(davies_bouldin_score(matrix, labels)),
                "silueta": float(silhouette_score(matrix, labels)),
                "cluster_min": int(sizes.min()),
                "cluster_max": int(sizes.max()),
                "tamanos": "/".join(str(int(s)) for s in sorted(sizes)),
                "cumple_min_5": bool(sizes.min() >= MIN_CLUSTER),
            }
        )
    return pd.DataFrame(rows)


def profile(
    frame: pd.DataFrame, features: list[str], labels: np.ndarray
) -> pd.DataFrame:
    """Perfil de cada cluster: media de z por feature y sus miembros."""
    work = frame[[c for c in IDENTITY if c in frame.columns]].copy()
    work["cluster"] = labels
    means = work.assign(**{f: frame[f].to_numpy() for f in features}).groupby("cluster")[
        features
    ].mean()
    members = work.groupby("cluster")["aa_name"].agg(lambda s: " | ".join(sorted(s)))
    means["n"] = work.groupby("cluster").size()
    means["modelos"] = members
    return means


def build(source: Path, out: Path, metrics_csv: Path, metrics_md: Path, pca: bool = False) -> dict:
    frame = pd.read_parquet(source)
    if pca:
        features = [c for c in ("pc1", "pc2") if c in frame.columns]
        if len(features) < 2:
            raise SystemExit("[cluster] la entrada no trae pc1 y pc2")
    else:
        features = [c for c in frame.columns if c.endswith("_z") and c not in EXCLUDED]
    if not features:
        raise SystemExit("[cluster] no quedaron features para entrenar")

    matrix = frame[features].to_numpy(dtype=float)
    if np.isnan(matrix).any():
        raise SystemExit("[cluster] hay faltantes en la matriz de entrenamiento")

    metrics = evaluate(matrix)

    # Eleccion: entre los k que respetan el minimo por cluster, el de mejor silueta.
    valid = metrics[metrics["cumple_min_5"]].sort_values("silueta", ascending=False)
    if valid.empty:
        chosen = int(metrics.sort_values("silueta", ascending=False).iloc[0]["k"])
        reason = "ningun k cumple el minimo por cluster; se toma la mejor silueta"
    else:
        chosen = int(valid.iloc[0]["k"])
        reason = "mejor silueta entre los k que respetan el minimo de 5 por cluster"

    model = KMeans(n_clusters=chosen, random_state=SEED, n_init=N_INIT)
    labels = model.fit_predict(matrix)
    clusters = profile(frame, features, labels)

    # Etiqueta legible: la dimension donde el cluster mas se despega de la media.
    names: dict[int, str] = {}
    for cluster, row in clusters.iterrows():
        values = row[features].astype(float)
        top = values.abs().sort_values(ascending=False).index[:2]
        names[int(cluster)] = " + ".join(
            f"{f.replace('_z', '')} {'alto' if values[f] > 0 else 'bajo'}" for f in top
        )

    result = frame.copy()
    result["cluster"] = labels
    result["cluster_label"] = result["cluster"].map(names)

    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out, index=False)
    metrics.to_csv(metrics_csv, index=False, encoding="utf-8")

    lines = [
        "# KMeans sobre la tabla de Artificial Analysis",
        "",
        f"- Entrada: `{source.name}`",
        f"- Filas: {len(frame)} | features: {len(features)}",
        "- Features: " + ", ".join(f"`{f}`" for f in features),
        "- Excluida: `data_z` (16 de 24 valores; entrenar con ella costaba 8 modelos)",
        f"- KMeans: `random_state={SEED}`, `n_init={N_INIT}`",
        "",
        "## Indicadores por k",
        "",
        "| k | Inercia (WCSS) | Entre (BCSS) | Entre/Dentro | Var. explicada | "
        "Calinski-Harabasz | Davies-Bouldin | Silueta | Tamanos | Min | Cumple min 5 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in metrics.itertuples():
        lines.append(
            f"| {row.k} | {row.inercia_wcss:.3f} | {row.entre_bcss:.3f} | "
            f"{row.ratio_entre_dentro:.3f} | {row.varianza_explicada:.3f} | "
            f"{row.calinski_harabasz:.2f} | {row.davies_bouldin:.3f} | "
            f"{row.silueta:.3f} | {row.tamanos} | {row.cluster_min} | "
            f"{'si' if row.cumple_min_5 else 'no'} |"
        )

    lines += [
        "",
        "### Como leer el ratio entre/dentro",
        "",
        "`BCSS / WCSS` mide cuanto de la dispersion total quedó entre clusters en vez",
        "de dentro de ellos: mas alto es mejor. Pero **crece con k por construccion**",
        "—cada cluster nuevo siempre explica algo mas—, asi que no sirve para elegir",
        "k comparando valores crudos. Para eso esta Calinski-Harabasz, que es el mismo",
        "cociente normalizado por los grados de libertad:",
        "",
        "```",
        "CH = (BCSS / (k - 1)) / (WCSS / (n - k))",
        "```",
        "",
        "Davies-Bouldin y la silueta van en la dirección contraria: mas bajo el",
        "primero, mas alta la segunda.",
        "",
        f"## k elegido: **{chosen}**",
        "",
        f"Criterio: {reason}.",
        "",
        "| Cluster | n | Etiqueta | Modelos |",
        "|---|---:|---|---|",
    ]
    for cluster in sorted(clusters.index):
        row = clusters.loc[cluster]
        label = names[int(cluster)]
        lines.append(
            f"| {int(cluster)} | {int(row['n'])} | {label} | {row['modelos']} |"
        )

    lines += [
        "",
        "## Perfil de los centroides (media de z por feature)",
        "",
        "| Cluster | " + " | ".join(f.replace("_z", "") for f in features) + " |",
        "|---|" + "---:|" * len(features),
    ]
    for cluster in sorted(clusters.index):
        row = clusters.loc[cluster]
        cells = " | ".join(f"{row[f]:+.2f}" for f in features)
        lines.append(f"| {int(cluster)} | {cells} |")
    lines.append("")

    metrics_md.parent.mkdir(parents=True, exist_ok=True)
    metrics_md.write_text("\n".join(lines), encoding="utf-8")

    return {
        "filas": len(frame),
        "features": len(features),
        "elegido": chosen,
        "out": str(out),
        "metrics_csv": str(metrics_csv),
        "metrics_md": str(metrics_md),
        "metrics": metrics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in", dest="source", default="data/processed/aa_tabla_zscore_2026-10-19.parquet"
    )
    parser.add_argument("--out", default="data/processed/aa_clusters_2026-10-19.parquet")
    parser.add_argument("--csv", default="data/interim/aa_kmeans_metrics_2026-10-19.csv")
    parser.add_argument("--report", default="data/interim/aa_kmeans_report_2026-10-19.md")
    parser.add_argument(
        "--pca",
        action="store_true",
        help="clusterizar sobre pc1 y pc2 en vez de las features normalizadas",
    )
    args = parser.parse_args(argv)

    summary = build(
        Path(args.source),
        Path(args.out),
        Path(args.csv),
        Path(args.report),
        pca=args.pca,
    )
    print(f"[cluster] filas: {summary['filas']} | features: {summary['features']}")
    print()
    header = f"{'k':>2} {'WCSS':>8} {'BCSS':>8} {'E/D':>6} {'CH':>7} {'DB':>6} {'Sil':>6} {'tamanos':>12} {'min':>4}"
    print(header)
    for row in summary["metrics"].itertuples():
        print(
            f"{row.k:>2} {row.inercia_wcss:>8.2f} {row.entre_bcss:>8.2f} "
            f"{row.ratio_entre_dentro:>6.2f} {row.calinski_harabasz:>7.1f} "
            f"{row.davies_bouldin:>6.2f} {row.silueta:>6.3f} {row.tamanos:>12} "
            f"{row.cluster_min:>4}"
        )
    print()
    print(f"[cluster] k elegido: {summary['elegido']}")
    print(f"[cluster] salida -> {summary['out']}")
    print(f"[cluster] metricas -> {summary['metrics_csv']}")
    print(f"[cluster] reporte -> {summary['metrics_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
