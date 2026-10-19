"""Exporta los 24 modelos de Artificial Analysis a JSON para la web.

Un navegador no lee parquet. Este paso junta la tabla final con precios
(`aa_models_priced`) y la asignacion de tramos (`aa_clusters_k4`) y escribe:

- `data/web/models.json`: el contrato de datos de la web.
- `outputs/web/que-modelo-elijo/data/models.js`: el mismo contenido envuelto en
  `window.MODELS_DATA = ...`, para que `index.html` funcione abierto desde disco
  (`file://` bloquea `fetch` de archivos locales).

Los nulos quedan como `null`: no se convierten en 0 ni en cadena vacia.

Uso:
    python -m src.web_export
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd

CORTE = "2026-10-19"

# Nombres de tramo y descripciones: seccion 5.2 de
# outputs/especificacion-datos-y-modelado.md. El parquet de clusters no trae
# `cluster_label`, asi que la fuente de verdad es el documento.
CLUSTERS: dict[int, tuple[str, str]] = {
    0: (
        "Velocistas",
        "El grupo más rápido (509 t/s) y el menos capaz: 1,4 puntos en Terminal-Bench "
        "y 10 en GDP.pdf, contra 25 y 18 del tramo siguiente. Responden en 1,4 s pero "
        "no completan tareas que requieran herramientas o varios pasos. Sirven para "
        "generar volumen, no para trabajo agéntico.",
    ),
    1: (
        "Equilibrados",
        "El centro de la distribución y el grupo más numeroso: 123 t/s, 41 s hasta el "
        "primer token, calidad intermedia. No es un arquetipo sino el promedio del "
        "mercado: diez proveedores distintos y el lugar donde cae cualquier modelo que "
        "no sobresalga en ninguna dirección.",
    ),
    2: (
        "Trabajo pesado",
        "Sacrifican velocidad por trabajo agéntico y documental: 40 en Terminal-Bench "
        "y 25 en GDP.pdf. Generan a 51 t/s, la mitad que el tramo de frontera, y por "
        "eso son los más lentos de punta a punta: 1.106 s por tarea, el doble que el "
        "resto. Único grupo que mezcla OpenAI, Alibaba, Kimi y Xiaomi.",
    ),
    3: (
        "Frontera reflexiva",
        "El techo de calidad: 65 de razonamiento, 57 de agéntico y 57 en datos. No es "
        "lento generando: escribe a 111 t/s, el segundo caudal más alto. Lo que lo hace "
        "tardar es el arranque (304 s hasta el primer token, porque razona antes de "
        "emitir) y salidas de 112.000 tokens por tarea, el doble que el resto. Tres de "
        "sus cuatro modelos son Claude y el cuarto es Muse Wonder: solo dos proveedores.",
    ),
}

# Versión en inglés para /en/ del sitio. Misma información, mismos números.
CLUSTERS_EN: dict[int, tuple[str, str]] = {
    0: (
        "Speedsters",
        "The fastest group (509 t/s) and the least capable: 1.4 points on Terminal-Bench "
        "and 10 on GDP.pdf, against 25 and 18 for the next tier. They respond in 1.4 s but "
        "do not complete tasks that need tools or several steps. Good for volume, not for "
        "agentic work.",
    ),
    1: (
        "Balanced",
        "The center of the distribution and the largest group: 123 t/s, 41 s to first "
        "token, mid-level quality. Not an archetype but the market average: ten different "
        "providers, and where any model lands if it does not stand out in any direction.",
    ),
    2: (
        "Heavy lifting",
        "They trade speed for agentic and document work: 40 on Terminal-Bench and 25 on "
        "GDP.pdf. They generate at 51 t/s, half the frontier tier, and so they are the "
        "slowest end to end: 1,106 s per task, twice the rest. The only group mixing "
        "OpenAI, Alibaba, Kimi and Xiaomi.",
    ),
    3: (
        "Reflective frontier",
        "The quality ceiling: 65 in reasoning, 57 agentic and 57 in data. It is not slow at "
        "generating: it writes at 111 t/s, the second highest throughput. What makes it "
        "take long is the start (304 s to first token, because it reasons before emitting) "
        "and outputs of 112,000 tokens per task, twice the rest. Three of its four models "
        "are Claude and the fourth is Muse Wonder: only two providers.",
    ),
}

# Tabla 3.2 del documento: tarea -> (columna, benchmark).
TAREAS: dict[str, tuple[str, str]] = {
    "general": ("intelligence_index", "AA Intelligence Index v4.3.2"),
    "reasoning": ("gdpval_normalized_pct", "GDPval-AA v2.1"),
    "coding": ("scicode_pct", "SciCode"),
    "agentic": ("terminal_bench_4_0_pct", "Terminal-Bench 4.0"),
    "professional": ("gdp_pdf_all_pass_pct", "GDP.pdf"),
    "long_context": ("aa_lcr_pct", "AA-LCR v1.1"),
    "data": ("analyst_agent_pct", "AA-AnalystAgent"),
    "multimodal": ("mmmu_pro_pct", "MMMU-Pro"),
    "instruction": ("ifbench_pct", "IFBench"),
}

CAMPOS: dict[str, str] = {
    "slug": "aa_slug",
    "precio_in": "price_in_usd_per_mtok",
    "precio_out": "price_out_usd_per_mtok",
    "precio_cache": "price_cache_hit_usd_per_mtok",
    "precio_imputado": "price_imputed",
    "precio_metodo_imputacion": "price_imputation_method",
    "contexto": "context_window_tokens",
    "velocidad": "speed_tok_s",
    "latencia": "latency_ttft_s",
    "tiempo_por_tarea": "ii_time_per_task_s",
    "tokens_por_tarea": "ii_output_tokens_per_task",
    "pesos_abiertos": "is_open_weights",
    "es_razonamiento": "is_reasoning",
    "fecha_lanzamiento": "release_date",
}


def short_name(name: str) -> str:
    """Saca el parentesis de esfuerzo/variante: 'Grok 4.7 (Xhigh)' -> 'Grok 4.7'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()


def clean(value):
    """Convierte tipos de numpy/pandas a JSON nativo; NaN y NA quedan como None."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, 6)
    return value


def build(priced: pd.DataFrame, clusters: pd.DataFrame) -> dict:
    merged = priced.merge(
        clusters[["aa_slug", "cluster", "pc1", "pc2"]], on="aa_slug", how="inner", validate="1:1"
    )
    if len(merged) != len(priced):
        raise ValueError(f"{len(priced) - len(merged)} modelos sin cluster asignado")

    modelos = []
    for _, row in merged.sort_values(["cluster", "pc1"]).iterrows():
        item = {
            "slug": clean(row["aa_slug"]),
            "nombre": short_name(row["aa_name"]),
            "nombre_aa": row["aa_name"],
            "proveedor": row["creator_name"],
            "cluster": int(row["cluster"]),
            "pc1": clean(row["pc1"]),
            "pc2": clean(row["pc2"]),
        }
        for key, col in CAMPOS.items():
            if key != "slug":
                item[key] = clean(row[col])
        for task, (col, _) in TAREAS.items():
            item[task] = clean(row[col])
        modelos.append(item)

    clusters_out = [
        {
            "id": cid,
            "nombre": name,
            "nombre_en": CLUSTERS_EN[cid][0],
            "n": int((merged["cluster"] == cid).sum()),
            "descripcion": desc,
            "descripcion_en": CLUSTERS_EN[cid][1],
        }
        for cid, (name, desc) in CLUSTERS.items()
    ]

    return {
        "meta": {
            "corte": CORTE,
            "fuente": "artificialanalysis.ai/models",
            "n_modelos": len(merged),
            "n_proveedores": int(merged["creator_name"].nunique()),
            "tareas": [
                {
                    "id": task,
                    "columna": col,
                    "benchmark": bench,
                    "cobertura": int(merged[col].notna().sum()),
                }
                for task, (col, bench) in TAREAS.items()
            ],
        },
        "clusters": clusters_out,
        "modelos": modelos,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--priced", default=f"data/processed/aa_models_priced_{CORTE}.parquet")
    parser.add_argument("--clusters", default=f"data/processed/aa_clusters_k4_{CORTE}.parquet")
    parser.add_argument("--out", default="data/web/models.json")
    parser.add_argument("--js", default="outputs/web/que-modelo-elijo/data/models.js")
    args = parser.parse_args()

    payload = build(pd.read_parquet(args.priced), pd.read_parquet(args.clusters))
    text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)

    for path, content in (
        (Path(args.out), text + "\n"),
        (Path(args.js), f"// Generado por src/web_export.py. No editar a mano.\nwindow.MODELS_DATA = {text};\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"escrito {path}")

    meta = payload["meta"]
    print(f"{meta['n_modelos']} modelos, {meta['n_proveedores']} proveedores")
    for t in meta["tareas"]:
        print(f"  {t['id']:<13} {t['cobertura']}/{meta['n_modelos']}")


if __name__ == "__main__":
    main()
