"""Etapa 1 - research.

Trae el catalogo crudo y lo deja inmutable en `data/raw/models_<fecha>.json`,
con su bloque `_meta` (source, url, fetched_at, n_rows, errors).

Uso:
    python -m src.research --out data/raw/models_2026-10-16.json
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from . import sources


def run(out_path: Path) -> dict:
    errors: list[str] = []
    try:
        payload = sources.fetch_openrouter()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"No se pudo traer el catalogo de OpenRouter: {exc}") from exc

    n_rows = len(payload.get("data", []))
    if n_rows == 0:
        errors.append("El payload no trae modelos.")

    sources.write_raw_snapshot(payload, out_path, sources.OPENROUTER_MODELS_URL, errors)
    return {"out_path": str(out_path), "n_rows": n_rows, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    parser = argparse.ArgumentParser(description="Etapa 1: ingesta cruda.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(f"data/raw/models_{today}.json"),
        help="Ruta del snapshot crudo (inmutable).",
    )
    args = parser.parse_args(argv)

    result = run(args.out)
    print(f"[research] crudo -> {result['out_path']}")
    print(f"[research] filas crudas: {result['n_rows']}")
    if result["errors"]:
        for err in result["errors"]:
            print(f"[research] aviso: {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
