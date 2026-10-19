"""Convierte un snapshot de accesibilidad de una pagina en un snapshot de datos.

Motivo: los leaderboards bloquean `requests` (403 / 404 / 401 sin key), pero si
cargan en el navegador integrado. `read_page` devuelve el arbol de accesibilidad
como texto, y ese texto se puede **parsear con codigo** en vez de transcribir a
mano. Transcribir 250 filas x 8 columnas a ojo seria una fuente silenciosa de
errores; esto no.

Uso:
    python -m src.page_parse --page data/interim/_aa_page.txt --source aa \
        --url https://artificialanalysis.ai/leaderboards/models \
        --out data/raw/benchmarks_2026-10-16.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import schema

# Una fila del arbol de accesibilidad; las celdas vienen indentadas debajo.
ROW_START = re.compile(r'^\s*- row ')
# Valor de celda. Greedy hasta el ultimo `" [ref=` para tolerar comillas internas.
CELL_VALUE = re.compile(r'^\s*- cell "(?P<value>.*)" \[ref=')


class TableSpec:
    """Que columna del contrato sale de que celda de la tabla."""

    def __init__(self, name: str, cells: int, mapping: dict[int, str], key_cell: int = 0):
        self.name = name
        self.cells = cells
        self.mapping = mapping
        self.key_cell = key_cell


# Artificial Analysis - leaderboard de modelos.
# Orden de columnas del encabezado de la pagina:
# Model | Context Window | Creator | AA Intelligence Index | Cost per Task (USD)
# | Median Tokens/s | Latency First Chunk (s) | Total Response (s) | Further Analysis
AA_MODELS = TableSpec(
    name="artificial_analysis_models",
    cells=9,
    key_cell=0,
    mapping={
        3: "intelligence_index",
        5: "speed_tok_s",
        6: "latency_ttft_s",
    },
)

SPECS: dict[str, TableSpec] = {"aa": AA_MODELS}

# Vals AI: un leaderboard por benchmark, cada uno en su URL.
# `slugs` es lo que se pidio al navegador; `column` es la columna del contrato.
VALS_SLUG_TO_COLUMN: dict[str, str] = {
    "legal_bench": "legal_bench_pct",
    "medscribe": "medscribe_pct",
    "medcode": "medcode_pct",
    "sage": "sage_pct",
    "hlab": "harvey_lab_pct",
    "legal_research": "legal_research_pct",
    "fabv2": "finance_agent_v2_pct",
    "tax_agent_bench": "tax_agent_bench_pct",
    "public-benefits-bench": "public_benefits_bench_pct",
    "vals_index": "vals_index_pct",
    "proof_bench": "proof_bench_pct",
    "terminal-bench-science": "terminal_bench_science_pct",
    "vibe-code": "vibe_code_bench_pct",
    "code-migration": "code_migration_pct",
    "programbench": "programbench_pct",
    "ioi": "ioi_pct",
    "cyber": "cyberbench_pct",
    "skillsbench": "skillsbench_pct",
    "srebench": "sre_bench_pct",
    "emb": "excel_modeling_pct",
    "terminal-bench-4": "terminal_bench_4_0_pct",
}


def parse_vals_raw(path: Path) -> tuple[dict[str, dict[str, float]], list[str], list[str]]:
    """Crudo de Vals -> {columna: {modelo: valor}}.

    El archivo puede venir doblemente codificado (un string JSON que contiene
    JSON), porque es lo que devuelve `page.evaluate` al volcarlo a disco.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, str):
        payload = json.loads(payload)

    scores: dict[str, dict[str, float]] = {}
    warnings: list[str] = []
    mapped: list[str] = []

    for slug, block in payload.items():
        column = VALS_SLUG_TO_COLUMN.get(slug)
        if column is None:
            warnings.append(f"slug sin columna declarada: {slug!r}")
            continue
        values: dict[str, float] = {}
        for row in block.get("rows", []):
            if not isinstance(row, list) or len(row) < 2:
                continue
            name, raw = row[0], row[1]
            number = to_number(raw)
            if number is None or not name:
                continue
            values[name] = number
        scores[column] = values
        mapped.append(f"{column} <- {slug} ({block.get('valueColumn')}), {len(values)} modelos")

    return scores, warnings, mapped


def run_vals(page: Path, out: Path) -> dict:
    scores, warnings, mapped = parse_vals_raw(page)
    payload = {
        "_meta": {
            "source": "vals",
            "url": "https://www.vals.ai/benchmarks/<slug>",
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "table": "vals_leaderboards",
            "n_rows": sum(len(v) for v in scores.values()),
            "benchmarks": len(scores),
            "errors": warnings[:20],
        },
        "scores": {c: v for c, v in scores.items() if v},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"out": str(out), "benchmarks": len(scores), "mapped": mapped, "warnings": warnings}


def parse_table(path: Path, spec: TableSpec) -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Extrae las filas de la tabla: [(nombre, celdas), ...].

    Devuelve tambien los avisos (filas descartadas por tener otro numero de
    celdas, que suele indicar un cambio de layout en la pagina).
    """
    rows: list[tuple[str, list[str]]] = []
    warnings: list[str] = []
    current: list[str] = []
    in_row = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if ROW_START.match(line):
            if in_row:
                _append(rows, current, spec, warnings)
            current = []
            in_row = True
            continue
        if not in_row:
            continue
        match = CELL_VALUE.match(line)
        if match:
            current.append(match.group("value").strip())
        elif line.strip() and not line.startswith(" " * 14):
            # Se sale del bloque de la fila.
            _append(rows, current, spec, warnings)
            current = []
            in_row = False

    if in_row:
        _append(rows, current, spec, warnings)
    return rows, warnings


def _append(
    rows: list[tuple[str, list[str]]],
    cells: list[str],
    spec: TableSpec,
    warnings: list[str],
) -> None:
    if not cells:
        return
    if len(cells) != spec.cells:
        # La fila de encabezado usa columnheader, no cell: no llega aca.
        warnings.append(f"fila con {len(cells)} celdas (esperadas {spec.cells}): {cells[0][:50]!r}")
        return
    rows.append((cells[spec.key_cell], cells))


def to_number(raw: str) -> float | None:
    """Texto de celda -> numero. `N/A`, `< 1`, `1M` y vacios no son numeros."""
    text = raw.strip().replace("$", "").replace(",", "").replace("%", "")
    if not text or text.upper() in {"N/A", "NA", "-", "—"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def build_snapshot(
    rows: list[tuple[str, list[str]]],
    spec: TableSpec,
    source: str,
    url: str,
) -> tuple[dict, list[str]]:
    """Filas parseadas -> payload del snapshot (columnas -> {nombre: valor})."""
    scores: dict[str, dict[str, float]] = {column: {} for column in spec.mapping.values()}
    skipped: list[str] = []

    for name, cells in rows:
        for index, column in spec.mapping.items():
            value = to_number(cells[index])
            if value is None:
                skipped.append(f"{name}: {column} sin valor ({cells[index]!r})")
                continue
            scores[column][name] = value

    payload = {
        "_meta": {
            "source": source,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "table": spec.name,
            "n_rows": len(rows),
            "errors": [],
        },
        "scores": {
            column: values for column, values in scores.items() if values
        },
    }
    return payload, skipped


def run(page: Path, source: str, url: str, out: Path) -> dict:
    spec = SPECS[source]
    rows, warnings = parse_table(page, spec)
    payload, skipped = build_snapshot(rows, spec, source, url)
    payload["_meta"]["errors"] = warnings[:20]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    return {
        "out": str(out),
        "n_rows": len(rows),
        "warnings": warnings,
        "skipped": skipped,
        "columns": {c: len(v) for c, v in payload["scores"].items()},
    }


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    parser = argparse.ArgumentParser(description="Snapshot de pagina -> snapshot de datos.")
    parser.add_argument("--page", type=Path, required=True)
    parser.add_argument("--source", choices=["aa", "vals"], required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--out", type=Path, default=Path(f"data/raw/benchmarks_{today}.json"))
    args = parser.parse_args(argv)

    if args.source == "vals":
        result = run_vals(args.page, args.out)
        print(f"[page_parse] benchmarks mapeados: {result['benchmarks']}")
        for line in result["mapped"]:
            print(f"[page_parse]   {line}")
        if result["warnings"]:
            print(f"[page_parse] avisos: {result['warnings'][:5]}")
        print(f"[page_parse] -> {result['out']}")
        return 0

    result = run(args.page, args.source, args.url, args.out)
    print(f"[page_parse] filas parseadas: {result['n_rows']}")
    for column, count in result["columns"].items():
        print(f"[page_parse]   {column:22s} {count} valores")
    if result["warnings"]:
        print(f"[page_parse] avisos de layout: {len(result['warnings'])}")
        for warning in result["warnings"][:5]:
            print(f"[page_parse]   {warning}")
    print(f"[page_parse] -> {result['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
