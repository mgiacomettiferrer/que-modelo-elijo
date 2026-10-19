"""Normalizacion z-score de la tabla de analisis de Artificial Analysis.

z = (x - media) / desvio, con desvio poblacional (ddof=0), que es el criterio de
`StandardScaler`. Los faltantes se conservan: la media y el desvio se calculan
solo con los valores observados y no se imputa nada.

Advertencia que el reporte mide: dos de las siete features tienen cola muy
pesada (`latency_ttft_s` llega a 615 s y `speed_tok_s` a 1061 t/s). Un z-score
no las corrige, las empeora: el extremo infla el desvio y el resto de los
modelos queda comprimido en una banda angosta de z, donde diferencias reales se
vuelven indistinguibles. El reporte muestra el rango intercuartilico de z y
cuantas filas quedan dentro de +-1 para que se vea el efecto.

Uso:
    python -m src.aa_normalize --in data/processed/aa_tabla_2026-10-19.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .aa_table import FEATURES

IDENTITY = ["aa_slug", "aa_name", "creator_name", "n_features"]

# Features de cola pesada: se les aplica `log1p` antes del z-score.
#
# `speed_tok_s` va de 38 a 1061 t/s y `latency_ttft_s` de 0.78 a 615 s. El
# extremo infla el desvio, y sin la transformacion la mitad central de los
# modelos queda con un IQR de z de medio desvio o menos: diferencias de casi 6x
# se vuelven indistinguibles. `log1p` comprime la cola y el z-score vuelve a
# discriminar. Es la convencion de `AGENTS.md` para escalas sesgadas.
LOG1P_FEATURES = frozenset({"speed_tok_s", "latency_ttft_s"})


def build(source: Path, out: Path, out_csv: Path, report: Path) -> dict:
    table = pd.read_parquet(source)
    columns = {name: column for name, column in FEATURES.items() if column in table.columns}

    scores = pd.DataFrame(index=table.index)
    diagnostics: list[dict] = []

    for name, column in columns.items():
        values = pd.to_numeric(table[column], errors="coerce")
        uses_log = name in LOG1P_FEATURES
        work = np.log1p(values) if uses_log else values
        mean = float(work.mean())
        std = float(work.std(ddof=0))
        transform = "log1p + z" if uses_log else "z"
        if std == 0 or pd.isna(std):
            scores[f"{name}_z"] = pd.NA
            diagnostics.append(
                {
                    "feature": name,
                    "column": column,
                    "transform": transform,
                    "n": int(values.notna().sum()),
                    "mean": mean,
                    "std": std,
                    "z_min": None,
                    "z_max": None,
                    "iqr_z": None,
                    "iqr_sin_log": None,
                    "dentro_1": 0,
                    "fuera_3": 0,
                }
            )
            continue

        z = (work - mean) / std
        scores[f"{name}_z"] = z
        observed = z.dropna()

        # Para las de cola: que IQR habria tenido sin la transformacion.
        iqr_sin_log = None
        if uses_log:
            plain = (values - float(values.mean())) / float(values.std(ddof=0))
            plain = plain.dropna()
            if not plain.empty:
                iqr_sin_log = float(plain.quantile(0.75) - plain.quantile(0.25))

        diagnostics.append(
            {
                "feature": name,
                "column": column,
                "transform": transform,
                "n": int(values.notna().sum()),
                "mean": mean,
                "std": std,
                "z_min": float(observed.min()) if not observed.empty else None,
                "z_max": float(observed.max()) if not observed.empty else None,
                "iqr_z": float(observed.quantile(0.75) - observed.quantile(0.25))
                if not observed.empty
                else None,
                "iqr_sin_log": iqr_sin_log,
                "dentro_1": int((observed.abs() <= 1).sum()),
                "fuera_3": int((observed.abs() > 3).sum()),
            }
        )

    result = pd.concat(
        [table[[c for c in IDENTITY if c in table.columns]], table[list(columns.values())], scores],
        axis=1,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out, index=False)
    result.to_csv(out_csv, index=False, encoding="utf-8")

    total = len(result)
    lines = [
        "# Normalizacion z-score: tabla de Artificial Analysis",
        "",
        f"- Entrada: `{source.name}`",
        f"- Filas: {total}",
        f"- Features normalizadas: {len(columns)}",
        "- Formula: `z = (x - media) / desvio`, desvio poblacional (ddof=0)",
        "- Faltantes: se conservan. Media y desvio se calculan solo con lo observado.",
        "",
        "## Diagnostico por feature",
        "",
        "| Feature | Transformacion | n | media | desvio | z min | z max | IQR de z | dentro de \\|z\\|<=1 | fuera de \\|z\\|>3 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for d in diagnostics:
        if d["z_min"] is None:
            lines.append(
                f"| `{d['feature']}` | {d['transform']} | {d['n']} | {d['mean']:.4f} | 0 | - | - | - | 0 | 0 |"
            )
            continue
        lines.append(
            f"| `{d['feature']}` | {d['transform']} | {d['n']} | {d['mean']:.4f} | {d['std']:.4f} | "
            f"{d['z_min']:.2f} | {d['z_max']:.2f} | {d['iqr_z']:.2f} | "
            f"{d['dentro_1']} | {d['fuera_3']} |"
        )

    logged = [d for d in diagnostics if d["iqr_sin_log"] is not None]
    if logged:
        lines += [
            "",
            "## Efecto del log1p en las features de cola",
            "",
            "| Feature | IQR de z sin log1p | IQR de z con log1p | Ganancia |",
            "|---|---:|---:|---:|",
        ]
        for d in logged:
            gain = d["iqr_z"] / d["iqr_sin_log"] if d["iqr_sin_log"] else float("nan")
            lines.append(
                f"| `{d['feature']}` | {d['iqr_sin_log']:.2f} | {d['iqr_z']:.2f} | x{gain:.2f} |"
            )
        lines += [
            "",
            "El IQR de z es el rango donde cae la mitad central de los modelos. Si se",
            "duplica o mas, la transformacion devolvio poder de discriminacion que el",
            "extremo se estaba comiendo.",
            "",
        ]

    lines += [
        "",
        "## Que dice el IQR de z",
        "",
        "Si el rango intercuartilico de `z` es chico, la mitad central de los modelos",
        "ocupa una banda angosta y el z-score no los separa: el extremo se llevo el",
        "desvio. Un IQR cercano a 1 o mas significa que la escala sigue discriminando.",
        "",
    ]

    heavy = [d for d in diagnostics if d["iqr_z"] is not None and d["iqr_z"] < 0.6]
    if heavy:
        lines.append("Features donde la mitad central quedo comprimida (IQR de z < 0.6):")
        lines.append("")
        for d in heavy:
            lines.append(
                f"- `{d['feature']}`: la mitad central de los modelos cae en un rango de "
                f"{d['iqr_z']:.2f} desvios, con un maximo de {d['z_max']:.2f}. "
                f"{d['dentro_1']} de {d['n']} filas quedan dentro de +-1."
            )
        lines.append("")
        lines += [
            "Esto no es un error de calculo: es lo que un z-score hace con una cola",
            "pesada. El pipeline documenta `log1p` antes de escalar justamente por",
            "esto, y el metodo robusto (mediana e IQR) evita el problema porque no",
            "depende del extremo.",
        ]
        lines.append("")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    return {
        "filas": total,
        "features": len(columns),
        "out": str(out),
        "report": str(report),
        "comprimidas": [d["feature"] for d in heavy],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="source", default="data/processed/aa_tabla_2026-10-19.parquet")
    parser.add_argument("--out", default="data/processed/aa_tabla_zscore_2026-10-19.parquet")
    parser.add_argument("--csv", default="data/interim/aa_tabla_zscore_2026-10-19.csv")
    parser.add_argument("--report", default="data/interim/aa_zscore_report_2026-10-19.md")
    args = parser.parse_args(argv)

    summary = build(
        Path(args.source), Path(args.out), Path(args.csv), Path(args.report)
    )
    print(f"[zscore] filas: {summary['filas']} | features: {summary['features']}")
    if summary["comprimidas"]:
        print(f"[zscore] comprimidas por la cola: {', '.join(summary['comprimidas'])}")
    print(f"[zscore] salida -> {summary['out']}")
    print(f"[zscore] reporte -> {summary['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
