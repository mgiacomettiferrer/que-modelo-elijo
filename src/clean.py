"""Etapa 2 - clean.

Crudo -> `data/interim/models_clean.parquet` + `data/interim/universo_<fecha>.csv`
+ reporte del embudo en `data/interim/clean_report.md`.

Aplica, en orden:
    dedupe de variantes -> exclusiones -> solo texto -> ventana de 12 meses
    -> una familia por proveedor -> filtro de frescura -> cota 41-100

Uso:
    python -m src.clean --in data/raw/models_2026-10-16.json
"""

from __future__ import annotations

import argparse
import glob
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from . import frame, schema, sources

# Tiers de servicio que NO son una familia aparte: son la misma linea servida
# distinto. Si existen `x` y `x-<tier>` para el mismo proveedor, gana `x`.
# Lista deliberadamente corta: `max`, `plus`, `flash`, `flashx` y `omni`
# distinguen productos reales y se conservan.
TIER_SUFFIXES: tuple[str, ...] = (
    "pro",
    "prime",
    "contributor",
    "customtools",
    "ultraspeed",
    "ultra",
)


def _read_raw(path: Path) -> dict:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):  # snapshot sin bloque _meta
        return {"data": payload}
    return payload


def _dedupe_variants(rows: list[dict]) -> list[dict]:
    """Colapsa las variantes de proveedor al modelo canonico.

    Se prefiere la fila cuyo `model_id` coincide con el `canonical_slug`;
    si no existe, la primera.
    """
    best: dict[str, dict] = {}
    for row in rows:
        key = row["canonical_slug"]
        current = best.get(key)
        if current is None:
            best[key] = row
            continue
        row_is_canonical = row["model_id"] == row["canonical_slug"]
        current_is_canonical = current["model_id"] == current["canonical_slug"]
        if row_is_canonical and not current_is_canonical:
            best[key] = row
    return list(best.values())


def _select_universe(
    rows: list[dict], today: date, fresh_limit: date
) -> tuple[list[dict], dict]:
    """Aplica los filtros de universo y devuelve (filas, embudo)."""
    funnel: dict[str, int | list] = {}
    funnel["crudas"] = len(rows)

    rows = _dedupe_variants(rows)
    funnel["tras_dedupe_variantes"] = len(rows)

    excluded: dict[str, int] = {}
    kept: list[dict] = []
    for row in rows:
        pattern = sources.is_excluded(row["canonical_slug"])
        if pattern:
            excluded[pattern] = excluded.get(pattern, 0) + 1
            continue
        kept.append(row)
    rows = kept
    funnel["tras_exclusiones"] = len(rows)
    funnel["exclusiones_por_patron"] = excluded

    rows = [r for r in rows if r.get("_output_modalities", {"text"}) & {"text"}]
    funnel["tras_solo_texto"] = len(rows)

    window_start = today - timedelta(days=schema.WINDOW_DAYS)
    rows = [
        r
        for r in rows
        if r.get("release_date") is not None and r["release_date"] >= window_start
    ]
    funnel["tras_ventana_12m"] = len(rows)

    # Una familia por proveedor. Dentro de la familia se ordena por fecha desc;
    # si el mas nuevo es demasiado fresco (pocas pruebas cargadas) se cae al
    # siguiente de la misma familia en vez de dejar la familia sin representar.
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["provider"], row["family"]), []).append(row)

    universe: list[dict] = []
    dropped_fresh: list[dict] = []
    for members in grouped.values():
        members = sorted(members, key=lambda r: r["release_date"], reverse=True)
        chosen = None
        for member in members:
            if member["release_date"] < fresh_limit:
                chosen = member
                break
            dropped_fresh.append(member)
        if chosen is not None:
            universe.append(chosen)

    funnel["familias_con_representante"] = len(universe)
    funnel["descartados_por_frescura"] = len(dropped_fresh)
    funnel["sin_representante_por_frescura"] = len(grouped) - len(universe)

    universe, n_collapsed = _collapse_service_tiers(universe)
    funnel["familias_colapsadas_por_tier"] = n_collapsed

    universe.sort(key=lambda r: r["canonical_slug"])
    funnel["universo"] = len(universe)

    labs = {r["provider"] for r in universe}
    funnel["laboratorios_obligatorios_ausentes"] = sorted(
        set(schema.MUST_INCLUDE_LABS) - labs
    )
    return universe, funnel


def _collapse_service_tiers(rows: list[dict]) -> tuple[list[dict], int]:
    """Colapsa `familia-<tier>` cuando existe `familia` para el mismo proveedor.

    Evita que el tier de servicio infle el universo: `gpt-astra` y
    `gpt-astra-pro` son la misma linea, no dos modelos comparables.
    """
    families: dict[str, set[str]] = {}
    for row in rows:
        families.setdefault(row["provider"], set()).add(row["family"])

    drop: set[tuple[str, str]] = set()
    for provider, provider_families in families.items():
        for family in provider_families:
            stem, _, suffix = family.rpartition("-")
            if stem and suffix in TIER_SUFFIXES and stem in provider_families:
                drop.add((provider, family))

    if not drop:
        return rows, 0
    return [r for r in rows if (r["provider"], r["family"]) not in drop], len(drop)


def run(
    in_path: Path,
    out_dir: Path,
    benchmark_paths: list[Path] | None = None,
    today: date | None = None,
) -> dict:
    today = today or datetime.now(timezone.utc).date()
    fresh_limit = today - timedelta(days=schema.FRESHNESS_DAYS)

    payload = _read_raw(in_path)
    rows = sources.normalize_openrouter(payload, today)

    # Un snapshot por fuente; se unen todos contra las mismas filas.
    benchmark_summary: dict[str, dict] = {}
    benchmark_meta: list[dict] = []
    for path in benchmark_paths or []:
        if not path.exists():
            continue
        scores, meta = sources.load_benchmark_snapshot(path)
        benchmark_meta.append({**meta, "file": path.name})
        for column, stats in sources.merge_benchmarks(rows, scores).items():
            if column in benchmark_summary:
                acc = benchmark_summary[column]
                acc["declared"] += stats["declared"]
                acc["matched"] += stats["matched"]
                acc["aliased"] += stats["aliased"]
                acc["unmatched"] += stats["unmatched"]
                acc["collapsed_variants"] += stats["collapsed_variants"]
            else:
                benchmark_summary[column] = dict(stats)

    universe, funnel = _select_universe(rows, today, fresh_limit)

    assembled = frame.assemble(universe)
    assembled = frame.add_axis_aggregates(assembled)

    # Cobertura real: cuantos modelos del universo quedaron con dato. El
    # "matched" del join cuenta contra el catalogo completo, asi que sobreestima.
    coverage = {
        column: int(assembled[column].notna().sum())
        for column in schema.SNAPSHOT_COLUMNS
        if column in assembled.columns
    }

    src_flags = (
        "src_openrouter",
        "src_artificial_analysis",
        "src_lmarena",
        "src_hf",
        "src_vals",
        "src_livebench",
    )
    src_counts = {
        flag: int(assembled[flag].fillna(False).sum())
        for flag in src_flags
        if flag in assembled.columns
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    clean_path = out_dir / "models_clean.parquet"
    frame.persist(assembled, clean_path)

    universo_path = out_dir / f"universo_{today.isoformat()}.csv"
    audit = assembled[
        ["canonical_slug", "name", "provider", "family", "release_date"]
    ].copy()
    audit["n_benchmarks_presentes"] = (
        assembled[[c for c in schema.BENCHMARK_COLUMNS if c in assembled.columns]]
        .notna()
        .sum(axis=1)
        .astype("Int64")
    )
    audit.to_csv(universo_path, index=False, encoding="utf-8")

    report_path = out_dir / "clean_report.md"
    report_path.write_text(
        _render_report(
            funnel,
            benchmark_summary,
            benchmark_meta,
            universe,
            today,
            coverage,
            src_counts,
        ),
        encoding="utf-8",
    )

    return {
        "clean_path": str(clean_path),
        "universo_path": str(universo_path),
        "report_path": str(report_path),
        "funnel": funnel,
        "n_rows": len(assembled),
        "benchmark_summary": benchmark_summary,
        "coverage": coverage,
    }


def _render_report(
    funnel: dict,
    benchmark_summary: dict,
    benchmark_meta: list[dict],
    universe: list[dict],
    today: date,
    coverage: dict[str, int] | None = None,
    src_counts: dict[str, int] | None = None,
) -> str:
    n = int(funnel["universo"])
    in_range = schema.UNIVERSE_MIN <= n <= schema.UNIVERSE_MAX
    lines = [
        "# Reporte de limpieza",
        "",
        f"- Corte: **{today.isoformat()}**",
        f"- Crudo de entrada: `{funnel['crudas']}` modelos",
        f"- Universo resultante: **{n}** modelos",
        f"- Cota declarada: {schema.UNIVERSE_MIN}-{schema.UNIVERSE_MAX} "
        f"-> {'OK' if in_range else '**FUERA DE RANGO**'}",
        "",
        "## Embudo",
        "",
        "| Paso | Filas |",
        "|---|---|",
        f"| Crudas (catalogo completo) | {funnel['crudas']} |",
        f"| Tras dedupe de variantes | {funnel['tras_dedupe_variantes']} |",
        f"| Tras exclusiones | {funnel['tras_exclusiones']} |",
        f"| Tras filtro de solo texto | {funnel['tras_solo_texto']} |",
        f"| Tras ventana de 12 meses | {funnel['tras_ventana_12m']} |",
        f"| Familias con representante | {funnel['familias_con_representante']} |",
        f"| Tras colapsar tiers de servicio | "
        f"{funnel['familias_con_representante'] - funnel['familias_colapsadas_por_tier']} |",
        f"| **Universo final** | **{funnel['universo']}** |",
        "",
        "Descartados por frescura (publicados hace menos de "
        f"{schema.FRESHNESS_DAYS} dias): {funnel['descartados_por_frescura']}.",
        f"Familias que quedaron sin representante por eso: "
        f"{funnel['sin_representante_por_frescura']}.",
        "",
        "## Exclusiones aplicadas",
        "",
        "| Patron | Modelos descartados |",
        "|---|---|",
    ]
    for pattern, count in sorted(
        funnel["exclusiones_por_patron"].items(), key=lambda kv: -kv[1]
    ):
        lines.append(f"| `{pattern}` | {count} |")
    if not funnel["exclusiones_por_patron"]:
        lines.append("| (ninguna) | 0 |")

    lines += ["", "## Benchmarks", ""]
    if not benchmark_summary:
        lines += [
            "**Sin snapshot de benchmarks.** Ninguna columna de calidad tiene datos, "
            "asi que los 10 ejes `quality_*` quedan 100% nulos.",
            "",
            "Vals, Arena y Artificial Analysis bloquean el acceso programatico "
            "(403 / 404 sin navegador y 401 sin API key). LiveBench publica CSV en "
            "GitHub pero su ultima tabla es del 2026-06-25 y no cubre los modelos de "
            "septiembre/octubre del universo.",
            "",
            "Los puntajes entran por snapshot manual: ver `load_benchmark_snapshot` "
            "en `src/sources.py`.",
        ]
    else:
        lines += ["Fuentes de benchmark:", ""]
        for meta in benchmark_meta:
            lines.append(
                f"- `{meta.get('file', '?')}` -> source `{meta.get('source', '?')}` "
                f"({meta.get('fetched_at', '?')}), {meta.get('n_rows', '?')} filas"
            )
        lines += [
            "",
            "`declaradas` son los nombres que publica la fuente; `unidas` los que "
            "encontraron fila en el catalogo; `en el universo` los que sobrevivieron "
            "a la seleccion. La ultima es la cobertura que importa.",
            "",
            f"| Columna | Declaradas | Unidas | Por alias | En el universo ({n}) | Cobertura |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for column, stats in sorted(benchmark_summary.items()):
            count = (coverage or {}).get(column, 0)
            pct = round(count / n * 100, 1) if n else 0.0
            lines.append(
                f"| `{column}` | {stats['declared']} | {stats['matched']} | "
                f"{stats.get('aliased', 0)} | {count} | {pct}% |"
            )

        collapsed = [
            entry
            for stats in benchmark_summary.values()
            for entry in stats.get("collapsed_variants", [])
            if "esfuerzo" in entry
        ]
        if collapsed:
            lines += [
                "",
                "### Variante de esfuerzo elegida",
                "",
                "La fuente publica el mismo modelo en varios niveles de esfuerzo, que "
                "dan numeros distintos. Se elige de forma determinista el de mayor "
                "rango; nunca se promedian.",
                "",
                f"Modelos con mas de una variante: {len(collapsed)}",
                "",
                "| Clave | Variante elegida |",
                "|---|---|",
            ]
            for entry in collapsed[:25]:
                key, _, rest = entry.partition(": ")
                lines.append(f"| `{key}` | {rest} |")

    providers = sorted({r["provider"] for r in universe if r.get("provider")})
    lines += [
        "",
        "## Cobertura de fuentes",
        "",
        f"- `src_openrouter`: {funnel['universo']} / {n}",
        f"- `src_artificial_analysis`: {(src_counts or {}).get('src_artificial_analysis', 0)} / {n}",
        f"- `src_lmarena`: {(src_counts or {}).get('src_lmarena', 0)} / {n}",
        f"- `src_vals`: {(src_counts or {}).get('src_vals', 0)} / {n}",
        f"- `src_livebench`: {(src_counts or {}).get('src_livebench', 0)} / {n}",
        f"- Laboratorios obligatorios ausentes: "
        f"{', '.join(funnel['laboratorios_obligatorios_ausentes']) or 'ninguno'}",
        "",
        f"Proveedores en el universo ({len(providers)}): {', '.join(providers)}",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    parser = argparse.ArgumentParser(description="Etapa 2: limpieza y universo.")
    parser.add_argument("--in", dest="in_path", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("data/interim"))
    parser.add_argument(
        "--benchmarks",
        type=Path,
        nargs="*",
        default=None,
        help="Snapshots de benchmark, uno por fuente. Sin el, la calidad queda vacia.",
    )
    args = parser.parse_args(argv)

    bench = args.benchmarks
    if not bench:
        bench = [Path(p) for p in sorted(glob.glob("data/raw/benchmarks_*.json"))]

    result = run(args.in_path, args.out_dir, bench)
    print(f"[clean] limpio  -> {result['clean_path']}")
    print(f"[clean] universo -> {result['universo_path']}")
    print(f"[clean] reporte -> {result['report_path']}")
    print(f"[clean] universo: {result['n_rows']} modelos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
