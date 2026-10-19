"""k=4 sobre PC1/PC2: promedios crudos por cluster, nombres y figura.

Dos cosas que este paso agrega sobre el clustering anterior:

1. **Promedios de las variables crudas.** Los centroides en PC1/PC2 no se
   interpretan solos. Volver a las unidades originales (tokens por segundo,
   puntos de benchmark, segundos) permite decir "este grupo promedia 149 t/s y
   52 puntos de razonamiento" en vez de "PC1 = +0.8".
2. **La figura.** El plano PC1 x PC2 con un color por cluster es la pieza que va
   al articulo: es la unica forma de mostrar la particion sin pedirle al lector
   que imagine seis dimensiones.

Los clusters se renumeran por PC1 ascendente para que el orden sea estable entre
corridas: 0 es el de menor capacidad promedio y 3 el de mayor.

Uso:
    python -m src.aa_cluster_k4
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin ventana: solo escribe el archivo
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402

SEED = 42
N_INIT = 10
K = 4

# Variables crudas que se promedian por cluster. Las cinco primeras son las que
# entran en la distancia; `latency_ttft_s` y `analyst_agent_pct` estan afuera del
# modelo pero son columnas del dataset y conviene verlas.
RAW = [
    "speed_tok_s",
    "gdpval_normalized_pct",
    "scicode_pct",
    "terminal_bench_4_0_pct",
    "gdp_pdf_all_pass_pct",
    "latency_ttft_s",
    "analyst_agent_pct",
]

ETIQUETAS = {
    "speed_tok_s": "Velocidad (t/s)",
    "gdpval_normalized_pct": "Razonamiento (GDPval)",
    "scicode_pct": "Codigo (SciCode)",
    "terminal_bench_4_0_pct": "Agentico (TB 4.0)",
    "gdp_pdf_all_pass_pct": "Documentos (GDP.pdf)",
    "latency_ttft_s": "Latencia 1er chunk (s)",
    "analyst_agent_pct": "Datos (AnalystAgent)",
}

# Tres medidas de "rapidez" que NO son lo mismo y conviene no confundir:
#   speed_tok_s          caudal una vez que arranca a escribir
#   latency_ttft_s       cuanto tarda en emitir el primer token (incluye razonar)
#   ii_time_per_task_s   tiempo total por tarea del indice de AA, que combina
#                        caudal, latencia y cuantos tokens produce la tarea
TIMING = [
    "speed_tok_s",
    "latency_ttft_s",
    "time_to_first_answer_token_s",
    "end_to_end_response_time_s",
    "ii_time_per_task_s",
    "ii_output_tokens_per_task",
]
TIMING_LABELS = {
    "speed_tok_s": "Velocidad de salida (t/s)",
    "latency_ttft_s": "Latencia primer token (s)",
    "time_to_first_answer_token_s": "Primer token de respuesta (s)",
    "end_to_end_response_time_s": "Fin a fin de una respuesta (s)",
    "ii_time_per_task_s": "Tiempo por tarea (s)",
    "ii_output_tokens_per_task": "Tokens por tarea",
}

# Nombres y descripciones. Se completan mirando los promedios; el orden de
# cluster es estable porque se renumera por PC1 ascendente.
NOMBRES: dict[int, tuple[str, str]] = {
    0: ("Velocistas", "maxima velocidad, minima capacidad"),
    1: ("Equilibrados", "el centro de la distribucion"),
    2: ("Trabajo pesado", "generacion lenta, el mas costoso por tarea"),
    3: ("Frontera reflexiva", "razona antes de responder, salidas largas"),
}
DESCRIPCIONES: dict[int, str] = {
    0: (
        "El grupo mas rapido del conjunto (509 t/s) y el menos capaz: 1,4 puntos en "
        "Terminal-Bench y 10 en GDP.pdf, contra 25 y 18 del grupo siguiente. "
        "Responden en 1,4 s pero no completan tareas que requieran herramientas o "
        "varios pasos. Sirven para generar volumen, no para trabajo agentico."
    ),
    1: (
        "El centro de la distribucion y el grupo mas numeroso: once modelos, 123 t/s, "
        "41 s hasta el primer token y calidad intermedia (53 de razonamiento, 25 de "
        "agentico). No es un arquetipo sino el promedio del mercado: contiene modelos "
        "de diez proveedores distintos y es donde cae cualquier modelo que no "
        "sobresalga en ninguna direccion."
    ),
    2: (
        "Sacrifican velocidad por trabajo agentico y documental: 40 puntos en "
        "Terminal-Bench y 25 en GDP.pdf. Generan a 51 t/s, la mitad que el grupo de "
        "frontera, y por eso son **los mas lentos de punta a punta**: 1.106 s por tarea, "
        "el doble que el resto. El unico grupo que mezcla OpenAI, Alibaba, Kimi y Xiaomi."
    ),
    3: (
        "El techo de calidad del conjunto: 65 de razonamiento, 57 de agentico y 57 en "
        "datos. **No es lento generando**: escribe a 111 t/s, el segundo caudal mas alto. "
        "Lo que lo hace tardar es el arranque: 304 s hasta el primer token, porque razona "
        "antes de emitir, y salidas de 112.000 tokens por tarea, el doble que el resto. "
        "Queda en 703 s por tarea, menos que el grupo de trabajo pesado. Tres de sus "
        "cuatro modelos son Claude y el cuarto es Muse Wonder."
    ),
}


def build(pca_path: Path, raw_path: Path, out: Path, figure: Path, report: Path) -> dict:
    pca = pd.read_parquet(pca_path)
    raw = pd.read_parquet(raw_path)

    matrix = pca[["pc1", "pc2"]].to_numpy(dtype=float)
    model = KMeans(n_clusters=K, random_state=SEED, n_init=N_INIT)
    labels = model.fit_predict(matrix)

    # Renumeracion estable: el cluster 0 es el de menor PC1 promedio.
    order = np.argsort(model.cluster_centers_[:, 0])
    remap = {int(old): int(new) for new, old in enumerate(order)}
    labels = np.array([remap[int(v)] for v in labels])
    centers = model.cluster_centers_[order]

    work = pca.copy()
    work["cluster"] = labels
    needed = list(
        dict.fromkeys(
            [c for c in RAW if c in raw.columns] + [c for c in TIMING if c in raw.columns]
        )
    )
    merged = work.merge(
        raw[["aa_slug"] + needed],
        on="aa_slug",
        how="left",
        validate="one_to_one",
    )
    if "price_in_usd_per_mtok" in raw.columns:
        merged = merged.merge(
            raw[["aa_slug", "price_in_usd_per_mtok"]], on="aa_slug", how="left"
        )

    present = [c for c in RAW if c in merged.columns]
    means = merged.groupby("cluster")[present].mean().round(2)
    overall = merged[present].mean().round(2)
    sizes = merged.groupby("cluster").size()

    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(out, index=False)

    # ---------------- figura ----------------
    palette = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    fig, ax = plt.subplots(figsize=(10, 7.2), dpi=160)
    for cluster in range(K):
        subset = merged[merged["cluster"] == cluster]
        name = NOMBRES.get(cluster, (f"Cluster {cluster}", ""))[0]
        ax.scatter(
            subset["pc1"],
            subset["pc2"],
            s=120,
            alpha=0.85,
            color=palette[cluster % len(palette)],
            edgecolor="white",
            linewidth=1.2,
            label=f"{cluster}. {name} (n={len(subset)})",
            zorder=3,
        )
    for row in merged.itertuples():
        ax.annotate(
            row.aa_name.split(" (")[0],
            (row.pc1, row.pc2),
            fontsize=7.5,
            xytext=(5, 4),
            textcoords="offset points",
            color="#333333",
        )
    ax.axhline(0, color="#bbbbbb", lw=0.8, zorder=1)
    ax.axvline(0, color="#bbbbbb", lw=0.8, zorder=1)
    ax.set_xlabel("PC1 - capacidad (calidad agregada, velocidad en contra)", fontsize=10)
    ax.set_ylabel("PC2 - velocidad de salida", fontsize=10)
    ax.set_title(
        "Clusters de modelos LLM en el plano de los dos primeros componentes",
        fontsize=12.5,
        pad=12,
    )
    ax.legend(loc="lower right", fontsize=8.5, frameon=True)
    ax.grid(alpha=0.18, linestyle="--")
    ax.margins(x=0.14, y=0.08)  # deja aire para las etiquetas de los extremos
    fig.tight_layout()
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure)
    plt.close(fig)

    # ---------------- reporte ----------------
    lines = [
        "# Clusters con k=4 en el plano PC1 x PC2",
        "",
        f"- Entrada: `{pca_path.name}` y `{raw_path.name}`",
        f"- Filas: {len(merged)} | k = {K} | `random_state={SEED}`, `n_init={N_INIT}`",
        "- Los clusters se renumeran por PC1 ascendente: 0 es el de menor capacidad.",
        "- Las variables crudas se promedian en sus unidades originales, sin `log1p`.",
        "",
        "## Centroides en el plano de componentes",
        "",
        "| Cluster | n | PC1 | PC2 |",
        "|---|---:|---:|---:|",
    ]
    for cluster in range(K):
        lines.append(
            f"| {cluster} | {int(sizes.loc[cluster])} | "
            f"{centers[cluster][0]:+.2f} | {centers[cluster][1]:+.2f} |"
        )

    lines += [
        "",
        "## Promedios de las variables crudas",
        "",
        "| Variable | " + " | ".join(f"C{i}" for i in range(K)) + " | Global |",
        "|---|" + "---:|" * (K + 1),
    ]
    for column in present:
        cells = " | ".join(f"{means.loc[c, column]:.2f}" for c in range(K))
        lines.append(f"| {ETIQUETAS.get(column, column)} | {cells} | {overall[column]:.2f} |")
    if "price_in_usd_per_mtok" in merged.columns:
        price = merged.groupby("cluster")["price_in_usd_per_mtok"].mean().round(2)
        cells = " | ".join(f"{price.loc[c]:.2f}" for c in range(K))
        lines.append(
            f"| Precio entrada (USD/1M tok) | {cells} | "
            f"{merged['price_in_usd_per_mtok'].mean():.2f} |"
        )

    lines += ["", "## Velocidad, latencia y tiempo por tarea no son lo mismo", ""]
    timing_present = [c for c in TIMING if c in merged.columns]
    if timing_present:
        timing = merged.groupby("cluster")[timing_present].mean().round(1)
        lines += [
            "Tres medidas distintas que suelen llamarse 'velocidad': el caudal una vez",
            "que el modelo arranca a escribir, el tiempo hasta el primer token (que incluye",
            "razonar) y el tiempo total por tarea, que combina las dos anteriores con",
            "cuantos tokens produce la tarea.",
            "",
            "| Medida | " + " | ".join(f"C{i}" for i in range(K)) + " |",
            "|---|" + "---:|" * K,
        ]
        for column in timing_present:
            cells = " | ".join(f"{timing.loc[c, column]:,.1f}" for c in range(K))
            lines.append(f"| {TIMING_LABELS.get(column, column)} | {cells} |")
        lines += [
            "",
            "El grupo de trabajo pesado no es el de menor caudal por casualidad: genera a",
            "la mitad de velocidad que el de frontera y eso lo vuelve el mas caro en tiempo",
            "por tarea. El de frontera tiene caudal alto pero arranca tarde y escribe",
            "mucho, asi que queda en un punto medio. Un modelo puede ser rapido",
            "escribiendo y lento respondiendo: son ejes distintos.",
            "",
        ]

    lines += ["", "## Nombres y descripcion", ""]
    for cluster in range(K):
        name, short = NOMBRES.get(cluster, (f"Cluster {cluster}", "sin nombre"))
        lines += [
            f"### {cluster}. {name} - {int(sizes.loc[cluster])} modelos",
            "",
            f"{DESCRIPCIONES.get(cluster, short)}",
            "",
            "| Modelo | Proveedor | PC1 | PC2 |",
            "|---|---|---:|---:|",
        ]
        subset = merged[merged["cluster"] == cluster].sort_values("pc1", ascending=False)
        for row in subset.itertuples():
            lines.append(
                f"| {row.aa_name} | {row.creator_name} | {row.pc1:+.2f} | {row.pc2:+.2f} |"
            )
        lines.append("")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    return {
        "filas": len(merged),
        "k": K,
        "sizes": sizes.to_dict(),
        "means": means,
        "centers": centers,
        "out": str(out),
        "figure": str(figure),
        "report": str(report),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pca", default="data/processed/aa_pca_nolat_2026-10-19.parquet"
    )
    parser.add_argument("--raw", default="data/processed/aa_models_2026-10-19.parquet")
    parser.add_argument("--out", default="data/processed/aa_clusters_k4_2026-10-19.parquet")
    parser.add_argument("--figure", default="outputs/figures/aa_clusters_pc1_pc2.png")
    parser.add_argument("--report", default="data/interim/aa_clusters_k4_report_2026-10-19.md")
    args = parser.parse_args(argv)

    summary = build(
        Path(args.pca), Path(args.raw), Path(args.out), Path(args.figure), Path(args.report)
    )
    print(f"[k4] filas: {summary['filas']} | tamanos: {summary['sizes']}")
    print()
    print("promedios crudos por cluster:")
    print(summary["means"].to_string())
    print()
    print(f"[k4] salida -> {summary['out']}")
    print(f"[k4] figura -> {summary['figure']}")
    print(f"[k4] reporte -> {summary['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
