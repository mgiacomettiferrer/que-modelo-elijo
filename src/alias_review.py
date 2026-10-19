"""Propone pares de alias para revisar a mano: fila del universo <-> nombre en la fuente.

Por que existe: `match_key` es conservadora a proposito y **no adivina**. Eso
deja nombres que existen en el leaderboard pero no se unen a ninguna fila.
Aflojar la clave no es opcion: haria colisionar `gemma-4-31b` con `gemma-4-12b`,
que es como se contaminan los datos en silencio. El camino honesto es proponer
candidatos con evidencia y que una persona decida.

Este modulo **no escribe el dataset**: solo arma la lista para revisar. La
decision se aplica despues con un mapa de alias explicito.

Los pares se agrupan en cinco niveles:

- `T1`  tokens identificadores identicos; difiere solo el formato
- `T1E` idem, pero ademas difiere una calificacion de esfuerzo (`high`, `low`)
- `T2`  el nombre de la fuente agrega o quita palabras, sin conflicto de identidad
- `T2S` la fuente omite el tamano o la version que la fila si declara
- `T3`  conflicto de version, tamano, escalon o designacion de letra

`T3` es la trampa que motivo todo esto: casi siempre son **modelos distintos**.

El comparador es deliberadamente mas estricto que `match_key`, porque su trabajo
no es unir sino **proponer**: un falso positivo aca se convierte en un puntaje
ajeno pegado a una fila. Sus dos trampas conocidas, ambas corregidas tras la
primera pasada, eran descartar el signo `+` (hacia pasar `Command A+` por
`Command A`) y no quitar el sufijo de temporada en nombres con espacios
(`Ministral 3 14B 2512`).

Uso:
    python -m src.alias_review --in data/processed/llm_features.parquet \
        --aa data/raw/benchmarks_aa_2026-10-16.json \
        --vals data/raw/benchmarks_vals_2026-10-16.json \
        --out data/interim/alias_candidates.md
"""

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from . import schema
from .aliases import BENCHMARK_ALIASES, REJECTED_ALIASES
from .sources import match_key

# Tokens que NO identifican un modelo. Es la union de lo que ya borra
# `match_key` y del ruido propio de los nombres de leaderboard.
#
# Deliberadamente **no** incluye `max`, `lite`, `turbo`, `preview`, `beta` ni
# `flash`: aunque `FAMILY_STOPWORDS` los trate como no distintivos de familia,
# para unir nombres entre fuentes si distinguen (`Qwen3.8 Max` != `Qwen3.8`).
COSMETIC = frozenset(schema.MATCH_STOPWORDS) | {
    "with", "fallback", "non", "none", "default", "model", "models",
    "provider", "providers", "via", "direct", "api", "the", "and", "llm",
}

# Calificaciones de esfuerzo. Si lo unico que difiere es esto, el par sigue
# siendo el mismo modelo: `merge_benchmarks` ya elige la variante de mayor
# esfuerzo de forma determinista.
EFFORTISH = frozenset(
    {
        "high", "low", "medium", "xhigh", "minimal", "effort", "default",
        "none", "non", "reasoning", "thinking",
    }
)

# Palabras que marcan un escalon distinto del modelo (`Mini`, `Pro`, `Flash`).
# Que aparezcan en un lado y no en el otro no es formato: es otro modelo.
# `preview`, `beta` y `exp` quedan afuera a proposito: son estado, no escalon.
VARIANT_QUALIFIERS = frozenset(
    {
        "mini", "nano", "micro", "pro", "flash", "lite", "air", "max",
        "ultra", "super", "omni", "vision", "vl", "codex", "coder",
        "plus", "turbo",
    }
)

# Palabras y numeros, en orden de aparicion, con el numero pegado a su sufijo
# (`31b`, `3.8`).
TOKEN_RE = re.compile(r"\d+(?:[.]\d+)?[a-z]*|[a-z]+")
# Sufijo de temporada (`2512` = 2025-12) en un nombre separado por espacios, que
# la regex de `match_key` no alcanza porque necesita un guion delante.
SEASON_TOKEN = re.compile(r"^(?:2[0-9])(?:0[1-9]|1[0-2])$")
TIER_ORDER = {"T1": 0, "T1E": 1, "T2": 2, "T2S": 3, "T3": 4}
TIER_TITLE = {
    "T1": "T1 - solo difiere el formato (casi seguro el mismo modelo)",
    "T1E": "T1E - solo difiere el esfuerzo (mismo modelo, otra variante)",
    "T2": "T2 - el nombre de la fuente agrega o quita palabras",
    "T2S": "T2S - la fuente omite el tamano o la version que la fila si declara",
    "T3": "T3 - conflicto de version, tamano o escalon (probablemente NO es el mismo)",
}


def _normalize_number(token: str) -> str:
    """`2.0` -> `2`, `3.10` -> `3.1`: la misma version escrita distinto."""
    match = re.match(r"^(\d+(?:[.]\d+)?)([a-z]*)$", token)
    if not match:
        return token
    number, suffix = match.groups()
    if "." in number:
        number = number.rstrip("0").rstrip(".") or "0"
    return number + suffix


def tokens(name: str) -> list[str]:
    """Tokens identificadores de un nombre, en orden de aparicion.

    `Qwen3.8 Max` -> `[qwen, 3.8, max]`. Los numeros se conservan: son lo que
    distingue una version de otra.
    """
    text = name.lower().split("/")[-1]
    text = re.sub(r"^\w+:\s+", " ", text)  # prefijo `Proveedor: `
    text = re.sub(r"\+", " plus ", text)  # `Command A+` != `Command A`
    text = re.sub(r"\([^)]*\)", " ", text)  # esfuerzo entre parentesis
    text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)  # fecha con guiones
    text = re.sub(r"20\d{6}", " ", text)  # fecha YYYYMMDD
    found: list[str] = []
    for token in TOKEN_RE.findall(text):
        if token in COSMETIC or SEASON_TOKEN.match(token):
            continue
        found.append(_normalize_number(token))
    return found


def numeric(items) -> frozenset[str]:
    """Subconjunto de tokens que contiene algun digito."""
    return frozenset(t for t in items if any(ch.isdigit() for ch in t))


def classify(candidate: str, row_form: str) -> tuple[str, float, list[str], list[str]] | None:
    """Clasifica el par (nombre de la fuente, nombre de la fila).

    Devuelve (nivel, puntaje, tokens de mas en la fuente, tokens de mas en la
    fila), o None si el parecido no alcanza para proponerlo.
    """
    left, right = tokens(candidate), tokens(row_form)
    left_set, right_set = set(left), set(right)
    shared = left_set & right_set
    if not shared:
        return None

    # Familias distintas: ni el primer token alfabetico de uno aparece en el
    # otro. `Gemini 3.7 Flash` contra `Step 3.7 Flash` comparte version y
    # modalidad pero no familia: proponerlo solo agrega ruido.
    left_family = next((t for t in left if t.isalpha()), None)
    right_family = next((t for t in right if t.isalpha()), None)
    if left_family and right_family and left_family != right_family:
        if left_family not in right_set and right_family not in left_set:
            return None

    extra = sorted(left_set - right_set)  # la fuente dice de mas
    missing = sorted(right_set - left_set)  # la fila dice de mas
    jaccard = len(shared) / len(left_set | right_set)
    ratio = SequenceMatcher(None, candidate.lower(), row_form.lower()).ratio()
    score = round((jaccard + ratio) / 2, 3)

    diff = set(extra) | set(missing)
    # Designaciones de una sola letra: `Command A+` contra `Command R+`, o el
    # bloque de expertos `A4B` contra `E4B`. Si cada lado aporta una letra
    # distinta, son modelos distintos aunque compartan todo lo demas.
    letters_left = {t for t in extra if len(t) == 1 and t.isalpha()}
    letters_right = {t for t in missing if len(t) == 1 and t.isalpha()}

    if not diff:
        tier = "T1"
    elif diff <= EFFORTISH:
        tier = "T1E"
    elif numeric(extra) or (diff & VARIANT_QUALIFIERS) or (letters_left and letters_right):
        # La fuente declara una version, un escalon o una letra que la fila no
        # tiene, o al reves: son modelos distintos, no dos formas de escribir
        # el mismo.
        tier = "T3"
    elif numeric(missing):
        # La fila declara un tamano o una version que la fuente no publica. No
        # hay conflicto, hay menos detalle: revisable, no descartable.
        tier = "T2S"
    else:
        tier = "T2"

    return tier, score, extra, missing


def best_form(candidate: str, forms: list[tuple[str, str]]):
    """Elige la mejor representacion de la fila (`canonical_slug` o `name`)."""
    best = None
    for label, value in forms:
        result = classify(candidate, value)
        if result is None:
            continue
        tier, score, extra, missing = result
        rank = (TIER_ORDER[tier], -score)
        if best is None or rank < (TIER_ORDER[best[0]], -best[1]):
            best = (tier, score, extra, missing, label, value)
    return best


def load_scores(paths: list[Path]) -> dict[str, dict[str, float]]:
    """Lee snapshots de benchmarks y los fusiona por columna.

    Las columnas no se pisan entre snapshots: si dos traen la misma, gana la
    primera por orden de argumento, para que el resultado sea determinista.
    """
    merged: dict[str, dict[str, float]] = {}
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for column, entries in (payload.get("scores") or {}).items():
            if not isinstance(entries, dict):
                continue
            merged.setdefault(column, {}).update(
                {k: v for k, v in entries.items() if k not in merged.get(column, {})}
            )
    return merged


def host_of(column: str) -> str:
    """Fuente de la que proviene una columna."""
    for slot in schema.BENCHMARK_SLOTS:
        if slot.column == column:
            return slot.host
    return "artificialanalysis.ai"


def build(frame: pd.DataFrame, scores: dict[str, dict[str, float]], features: list[str]):
    """Arma los pares propuestos, ordenados por nivel y puntaje."""
    index: set[str] = set()
    for row in frame.to_dict("records"):
        index.add(match_key(row["canonical_slug"]))
        index.add(match_key(row["name"]))

    # Nombre de la fuente -> columnas donde aparece, solo si no aparece ya: ni
    # por `match_key`, ni por alias confirmado, ni descartado en revision.
    pool: dict[str, set[str]] = {}
    for column, entries in scores.items():
        for source_name in entries:
            if source_name in BENCHMARK_ALIASES or source_name in REJECTED_ALIASES:
                continue
            if match_key(source_name) in index:
                continue
            pool.setdefault(source_name, set()).add(column)

    feature_set = set(features)
    proposals: list[dict] = []
    for row in frame.to_dict("records"):
        missing = [f for f in features if pd.isna(row.get(f))]
        if not missing:
            continue
        forms = [("canonical_slug", row["canonical_slug"]), ("name", row["name"])]
        for candidate, columns in pool.items():
            hit = best_form(candidate, forms)
            if hit is None:
                continue
            tier, score, extra, missing_tok, label, value = hit
            if tier == "T3" and score < 0.5:
                continue
            if tier != "T3" and score < 0.45:
                continue
            fills = sorted(c for c in columns if c in feature_set and c in missing)
            proposals.append(
                {
                    "tier": tier,
                    "score": score,
                    "provider": row["provider"],
                    "slug": row["canonical_slug"],
                    "row_name": row["name"],
                    "matched_on": label,
                    "candidate": candidate,
                    "candidate_columns": sorted(columns),
                    "fills_features": fills,
                    "extra_in_source": extra,
                    "extra_in_row": missing_tok,
                }
            )

    # Un solo candidato por fila: el mejor. Evita una lista de ruido.
    proposals.sort(key=lambda p: (p["slug"], TIER_ORDER[p["tier"]], -p["score"]))
    best_per_row: dict[str, dict] = {}
    for p in proposals:
        best_per_row.setdefault(p["slug"], p)
    chosen = list(best_per_row.values())

    # Colision: el mismo nombre de la fuente elegido por mas de una fila. A lo
    # sumo una puede ser correcta; el resto son falsos y hay que descartarlos.
    by_candidate: dict[str, list[dict]] = {}
    for p in chosen:
        by_candidate.setdefault(p["candidate"], []).append(p)
    for group in by_candidate.values():
        if len(group) < 2:
            continue
        for p in group:
            p["collision_with"] = [
                f"{r['row_name']} (`{r['slug']}`)" for r in group if r is not p
            ]

    chosen.sort(key=lambda p: (TIER_ORDER[p["tier"]], -p["score"], p["slug"]))
    for i, p in enumerate(chosen, start=1):
        p["n"] = i
    return chosen, pool


def render(proposals: list[dict], frame: pd.DataFrame, pool: dict, out: Path) -> str:
    """Escribe la lista de revision en Markdown."""
    lines: list[str] = []
    lines.append("# Candidatos de alias para revision manual")
    lines.append("")
    lines.append(
        "Generado por `python -m src.alias_review`. **No** se aplica nada al dataset: "
        "cada par necesita confirmacion humana."
    )
    lines.append("")
    lines.append(f"- Corte: 2026-10-16")
    lines.append(f"- Filas en el universo: {len(frame)}")
    lines.append(f"- Nombres de fuente sin aparear: {len(pool)}")
    lines.append(f"- Pares propuestos: {len(proposals)}")
    lines.append(f"- Alias confirmados y aplicados por `src/aliases.py`: {len(BENCHMARK_ALIASES)}")
    lines.append(f"- Pares descartados en revision: {len(REJECTED_ALIASES)}")
    lines.append("")
    lines.append("## Como leer los niveles")
    lines.append("")
    lines.append("| Nivel | Significado | Que se espera |")
    lines.append("|---|---|---|")
    lines.append("| `T1` | tokens identicos, difiere el formato | confirmar |")
    lines.append("| `T1E` | difiere solo el esfuerzo | confirmar |")
    lines.append("| `T2` | la fuente agrega o quita palabras | revisar |")
    lines.append("| `T2S` | la fuente omite el tamano o la version | revisar |")
    lines.append("| `T3` | conflicto de version, tamano o escalon | descartar salvo evidencia |")
    lines.append("")
    lines.append(
        "Un escalon es `Mini`, `Nano`, `Pro`, `Flash`, `Lite`, `Max`, `Ultra`, `Super`, "
        "`Omni`, `VL`, `Codex`, `Plus`. Que aparezca en un lado y no en el otro son "
        "modelos distintos, no formato. `Preview`, `Beta` y `Exp` no cuentan: son estado."
    )
    lines.append("")

    for tier in ("T1", "T1E", "T2", "T2S", "T3"):
        group = [p for p in proposals if p["tier"] == tier]
        if not group:
            continue
        lines.append(f"## {TIER_TITLE[tier]}")
        lines.append("")
        lines.append(
            "| # | Modelo del universo | Slug | Nombre en la fuente | Fuente | "
            "Rellena | Sobra en fuente | Sobra en fila | Sim | Aviso | Mismo? |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for p in group:
            host = host_of(p["candidate_columns"][0]) if p["candidate_columns"] else "?"
            fills = ", ".join(f"`{c}`" for c in p["fills_features"]) or "—"
            extra = ", ".join(p["extra_in_source"]) or "—"
            missing = ", ".join(p["extra_in_row"]) or "—"
            aviso = ""
            if p.get("collision_with"):
                aviso = "COLISION: el mismo nombre lo pide tambien " + "; ".join(
                    p["collision_with"]
                )
            lines.append(
                f"| {p['n']} | {p['row_name']} | `{p['slug']}` | {p['candidate']} | "
                f"{host} | {fills} | {extra} | {missing} | {p['score']} | {aviso} |  |"
            )
        lines.append("")

    collided = [p for p in proposals if p.get("collision_with")]
    if collided:
        lines.append("## Colisiones: revisar antes que nada")
        lines.append("")
        lines.append(
            "Estas filas proponen el **mismo** nombre de la fuente. A lo sumo una "
            "puede ser correcta; si se aplicaran todas, dos modelos distintos "
            "compartirian los mismos puntajes."
        )
        lines.append("")
        for p in collided:
            lines.append(
                f"- `{p['candidate']}` -> {p['row_name']} (`{p['slug']}`), "
                f"nivel {p['tier']}, sim {p['score']}"
            )
        lines.append("")

    lines.append("## Decisiones ya tomadas")
    lines.append("")
    lines.append(
        "Viven en `src/aliases.py` y `merge_benchmarks` las aplica antes de "
        "`match_key`. No hace falta revisarlas de nuevo; quedan aca como registro."
    )
    lines.append("")
    lines.append("### Confirmados")
    lines.append("")
    lines.append("| Nombre en la fuente | Fila |")
    lines.append("|---|---|")
    for name, slug in sorted(BENCHMARK_ALIASES.items()):
        lines.append(f"| {name} | `{slug}` |")
    lines.append("")
    lines.append("### Descartados")
    lines.append("")
    lines.append("| Nombre en la fuente | Motivo |")
    lines.append("|---|---|")
    for name, reason in sorted(REJECTED_ALIASES.items()):
        lines.append(f"| {name} | {reason} |")
    lines.append("")

    lines.append("## Para aplicar las decisiones")
    lines.append("")
    lines.append(
        "Marcar la columna **Mismo?** con `si` / `no`. Los pares confirmados se "
        "convierten en un mapa `nombre_en_la_fuente -> canonical_slug` que "
        "`merge_benchmarks` consulta **antes** de recurrir a `match_key`, de modo "
        "que la clave conservadora sigue siendo el default."
    )
    lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="source", required=True,
                        help="llm_features.parquet con el universo")
    parser.add_argument("--aa", default=None, help="snapshot de Artificial Analysis")
    parser.add_argument("--vals", default=None, help="snapshot de Vals AI")
    parser.add_argument("--selection", default="data/interim/dimension_selection.json")
    parser.add_argument("--out", default="data/interim/alias_candidates.md")
    args = parser.parse_args(argv)

    frame = pd.read_parquet(args.source)

    features: list[str] = []
    selection_path = Path(args.selection)
    if selection_path.exists():
        features = json.loads(selection_path.read_text(encoding="utf-8")).get("features", [])
    if not features:
        features = list(schema.BASE_FEATURES)

    paths = [Path(p) for p in (args.aa, args.vals) if p]
    scores = load_scores(paths)
    if not scores:
        print("[alias] sin snapshots de benchmarks: nada que proponer")
        return 1

    proposals, pool = build(frame, scores, features)
    out = render(proposals, frame, pool, Path(args.out))

    counts: dict[str, int] = {}
    for p in proposals:
        counts[p["tier"]] = counts.get(p["tier"], 0) + 1

    print(f"[alias] universo: {len(frame)} filas, {len(features)} features")
    print(f"[alias] nombres de fuente sin aparear: {len(pool)}")
    print(f"[alias] pares propuestos (1 por fila): {len(proposals)}")
    for tier in ("T1", "T1E", "T2", "T2S", "T3"):
        print(f"[alias]   {tier:<4} {counts.get(tier, 0)}")
    print(f"[alias] reporte -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
