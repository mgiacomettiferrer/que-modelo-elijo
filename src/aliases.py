"""Mapa de alias revisado a mano: nombre publicado por la fuente -> `canonical_slug`.

Por que es codigo y no algo derivado: `match_key` es conservadora a proposito y
no adivina. Unir por parecido pegaria el puntaje de un modelo a otro sin avisar,
que es el error mas caro de este pipeline. Cada union que la clave no puede
resolver se decide mirando el par, y la decision queda aca con su motivo,
versionada y revisable en un diff.

`merge_benchmarks` consulta este mapa **antes** de `match_key`. Un nombre que no
esta ni aca ni en el indice queda faltante: nunca se imputa.

Revisado el 2026-10-19 sobre `data/interim/alias_candidates.md`.
"""

from __future__ import annotations

# Confirmados: el nombre de la fuente y la fila son el mismo modelo.
#
# El motivo importa tanto como el par. Sin el, dentro de seis meses nadie sabe
# si la union se penso o se copio.
BENCHMARK_ALIASES: dict[str, str] = {
    # Amazon publica `2.0` y la fila dice `2`; `(low)` es calificacion de esfuerzo.
    "Nova 2.0 Lite (low)": "amazon/nova-2-lite-v1",
    # La fila es la variante `reasoning` del mismo modelo Omni.
    "Nemotron 3 Nano Omni 30B A3B": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning-20260428",
    # `Next` es un sufijo editorial de Artificial Analysis, no otro modelo.
    "Qwen3.8-Flash-Next": "qwen/qwen3.8-flash-20260826",
    # `(Reasoning)` nombra la misma variante que `Multi-Agent` en la fila.
    "Grok 4.20 (Reasoning)": "x-ai/grok-4.20-multi-agent-20260309",
    # Artificial Analysis omite el tamano; el resto del nombre coincide.
    "Muse Glimmer (high)": "meta/muse-glimmer-30b-20260810",
    # Artificial Analysis tampoco publica el bloque de parametros en esta fila.
    "Nemotron 3 Nano": "nvidia/nemotron-3-nano-30b-a3b",
}

# Descartados: el par parece razonable y no se confirmo. Se registran por dos
# motivos: el reporte no los vuelve a proponer, y queda constancia de que la
# ausencia del dato es una decision y no un olvido. No aflojar `match_key` para
# "resolverlos".
REJECTED_ALIASES: dict[str, str] = {
    "Ministral 3 14B": "no confirmado contra mistralai/ministral-14b-2512",
    "Mistral Large 4 Preview": "no confirmado contra mistralai/mistral-large-4-0-20261006",
    "Laguna XS.2": "no confirmado contra poolside/laguna-xs-2.1-20260625",
}
