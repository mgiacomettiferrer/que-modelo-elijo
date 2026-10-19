"""Fuente de verdad del esquema del dataset.

Cada columna canonica se declara una sola vez, con su **rol**:

    training   entra en la matriz de distancia del clustering
    metadata   filtra o etiqueta; nunca entra en la distancia
    visual     canal grafico del scatter (tamano del punto)
    report     se publica en el articulo, no es feature
    audit      procedencia y confiabilidad del match entre fuentes
    output     lo produce la etapa de clustering

Regla dura (AGENTS.md): **las features de clustering son solo rendimiento + los
ejes de calidad**. Capacidad, precio, modalidades, mercado, procedencia,
parametros y descargas son metadata o canales visuales.

Si cambia este archivo hay que actualizar `AGENTS.md` y el skill
`cluster-llm-pipeline` en el mismo cambio.
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Roles
# --------------------------------------------------------------------------

TRAINING = "training"
INPUT = "input"
INDICATOR = "indicator"
METADATA = "metadata"
VISUAL = "visual"
REPORT = "report"
AUDIT = "audit"
OUTPUT = "output"

ROLE_ORDER = (TRAINING, INPUT, INDICATOR, METADATA, VISUAL, REPORT, AUDIT, OUTPUT)

ROLE_LABEL: dict[str, str] = {
    TRAINING: "Entrenamiento (features de clustering)",
    INPUT: "Insumo (alimenta los ejes de calidad)",
    INDICATOR: "Faltantes (indicadores de imputacion)",
    METADATA: "Metadata (filtra / etiqueta)",
    VISUAL: "Visualizacion (canal grafico)",
    REPORT: "Reporte (se publica, no es feature)",
    AUDIT: "Auditoria (procedencia y confiabilidad)",
    OUTPUT: "Salida del clustering",
}

# --------------------------------------------------------------------------
# Columnas
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Column:
    name: str
    role: str
    dtype: str
    group: str
    description: str


COLUMNS_STATIC: tuple[Column, ...] = (
    # --- identidad (metadata) ---------------------------------------------
    Column("model_id", METADATA, "str", "identidad", "Clave interna: id de OpenRouter."),
    Column("canonical_slug", METADATA, "str", "identidad", "Clave de negocio, sin variantes :free / :nitro / snapshots."),
    Column("name", METADATA, "str", "identidad", "Nombre para mostrar."),
    Column("provider", METADATA, "str", "identidad", "Laboratorio normalizado (prefijo del slug)."),
    Column("family", METADATA, "str", "identidad", "Linea de familia sin version ni esfuerzo. Base de la deduplicacion."),
    Column("release_date", METADATA, "datetime64[ns]", "identidad", "Fecha de lanzamiento. Define la ventana de 12 meses."),
    Column("hugging_face_id", METADATA, "str", "identidad", "Repo de HuggingFace."),
    # --- capacidad (metadata) ---------------------------------------------
    Column("context_length", METADATA, "float64", "capacidad", "Ventana de entrada en tokens."),
    Column("max_output_tokens", METADATA, "float64", "capacidad", "Tope de tokens de salida."),
    Column("is_open_weights", METADATA, "bool", "capacidad", "Pesos descargables. Inferido: hugging_face_id presente."),
    # --- precio (visual) --------------------------------------------------
    Column("price_in_usd_per_mtok", VISUAL, "float64", "precio", "Entrada sin cache."),
    Column("price_out_usd_per_mtok", VISUAL, "float64", "precio", "Salida."),
    Column("price_cache_read_usd_per_mtok", VISUAL, "float64", "precio", "Lectura de cache. Nulo != 0: si falta, el costo es No disponible."),
    Column("price_cache_write_usd_per_mtok", VISUAL, "float64", "precio", "Escritura de cache. Se informa aparte."),
    Column("price_reasoning_usd_per_mtok", VISUAL, "float64", "precio", "Razonamiento facturable. Nulo = comparte tarifa con la salida."),
    Column("price_web_search_usd_per_call", VISUAL, "float64", "precio", "Busqueda web, USD por llamada. Se informa aparte."),
    Column("weighted_cost_usd_per_mtok", VISUAL, "float64", "costo", "Costo ponderado 60/20/20. TAMANO DEL PUNTO en el scatter."),
    Column("weighted_cost_profile", VISUAL, "str", "costo", "Pesos usados: 60/20/20 u 80/20."),
    # --- modalidades (metadata) -------------------------------------------
    Column("supports_tools", METADATA, "bool", "modalidades", "Inferido: 'tools' en supported_parameters."),
    Column("supports_reasoning", METADATA, "bool", "modalidades", "Inferido: 'reasoning' en supported_parameters."),
    Column("supports_vision", METADATA, "bool", "modalidades", "Inferido: 'image' en architecture.input_modalities."),
    Column("supports_audio", METADATA, "bool", "modalidades", "Inferido: 'audio' en architecture.input_modalities."),
    # --- rendimiento (training) -------------------------------------------
    Column("speed_tok_s", TRAINING, "float64", "rendimiento", "Tokens de salida por segundo. Feature."),
    Column("latency_ttft_s", TRAINING, "float64", "rendimiento", "Tiempo hasta el primer token. Feature."),
    # --- calidad: reporte -------------------------------------------------
    Column("intelligence_index", REPORT, "float64", "calidad-reporte", "Compuesto de AA. NO es feature: se solapa con los ejes."),
    Column("coding_index", REPORT, "float64", "calidad-reporte", "Indice de codigo de AA."),
    Column("math_index", REPORT, "float64", "calidad-reporte", "Indice de matematica de AA."),
    # --- mercado (metadata) -----------------------------------------------
    Column("n_providers", METADATA, "float64", "mercado", "Proveedores que sirven el modelo."),
    # --- procedencia (audit) ----------------------------------------------
    Column("src_openrouter", AUDIT, "bool", "procedencia", "La fila tiene datos de OpenRouter."),
    Column("src_artificial_analysis", AUDIT, "bool", "procedencia", "La fila tiene datos de Artificial Analysis."),
    Column("src_lmarena", AUDIT, "bool", "procedencia", "La fila tiene datos de Arena."),
    Column("src_hf", AUDIT, "bool", "procedencia", "La fila tiene datos de HuggingFace."),
    Column("src_vals", AUDIT, "bool", "procedencia", "La fila tiene datos de Vals AI."),
    Column("src_livebench", AUDIT, "bool", "procedencia", "La fila tiene datos de LiveBench."),
    Column("row_confidence", AUDIT, "float64", "procedencia", "Confiabilidad del match entre fuentes (0-1)."),
    # --- salida del clustering -------------------------------------------
    Column("cluster_id", OUTPUT, "int64", "clustering", "Asignacion de cluster. Lo agrega la etapa cluster."),
    Column("cluster_label", OUTPUT, "str", "clustering", "Nombre legible del centroide. Lo agrega la etapa cluster."),
)

# --------------------------------------------------------------------------
# Benchmarks crudos y ejes de calidad
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchmarkSlot:
    """Un benchmark en una version y un host concretos.

    Regla dura: un slot = una version + un host. Los puntajes de dos versiones
    (o de dos hosts) del mismo benchmark nunca se mezclan.
    """

    column: str
    axis: str
    benchmark: str
    host: str
    version: str
    models_seen: int | None
    at_cutoff: str


BENCHMARK_SLOTS: tuple[BenchmarkSlot, ...] = (
    # general - preferencia humana
    BenchmarkSlot("arena_elo", "general", "Arena Text", "arena.ai", "-", 416, "2026-10-15"),
    # reasoning
    BenchmarkSlot("proof_bench_pct", "reasoning", "ProofBench", "vals.ai", "v1.1", 52, "2026-10-12"),
    BenchmarkSlot("terminal_bench_science_pct", "reasoning", "Terminal-Bench Science", "vals.ai", "-", 41, "2026-10-14"),
    BenchmarkSlot("livebench_2_0_reasoning", "reasoning", "LiveBench", "livebench.ai", "2.0", 40, "2026-10-14"),
    BenchmarkSlot("gpqa_diamond_pct", "reasoning", "GPQA Diamond", "artificialanalysis.ai", "-", None, "2026-10"),
    BenchmarkSlot("hle_pct", "reasoning", "HLE", "artificialanalysis.ai", "-", None, "2026-10"),
    # coding
    BenchmarkSlot("vibe_code_bench_pct", "coding", "Vibe Code Bench", "vals.ai", "v1.1", 112, "2026-10-12"),
    BenchmarkSlot("code_migration_pct", "coding", "Code Migration", "vals.ai", "-", 77, "2026-10-12"),
    BenchmarkSlot("programbench_pct", "coding", "ProgramBench", "vals.ai", "-", 64, "2026-10-12"),
    BenchmarkSlot("swe_bench_verified_pct", "coding", "SWE-bench Verified", "swebench.com", "Verified", 47, "2026-02-17"),
    BenchmarkSlot("ioi_pct", "coding", "IOI", "vals.ai", "-", 44, "2026-10-14"),
    BenchmarkSlot("livebench_2_0_coding", "coding", "LiveBench", "livebench.ai", "2.0", 40, "2026-10-14"),
    # agentic
    BenchmarkSlot("bfcl_pct", "agentic", "BFCL", "gorilla.cs.berkeley.edu", "V4", 109, "2026-04-12"),
    BenchmarkSlot("terminal_bench_4_0_pct", "agentic", "Terminal-Bench", "vals.ai", "4.0", 48, "2026-10-13"),
    BenchmarkSlot("cyberbench_pct", "agentic", "CyberBench", "vals.ai", "v1.1", 47, "2026-10-12"),
    BenchmarkSlot("livebench_2_0_agentic", "agentic", "LiveBench", "livebench.ai", "2.0", 40, "2026-10-14"),
    BenchmarkSlot("skillsbench_pct", "agentic", "SkillsBench", "vals.ai", "-", 35, "2026-09-27"),
    BenchmarkSlot("sre_bench_pct", "agentic", "SRE Bench", "vals.ai", "-", 35, "2026-10-14"),
    # professional
    BenchmarkSlot("legal_bench_pct", "professional", "LegalBench", "vals.ai", "-", 151, "2026-10-13"),
    BenchmarkSlot("medscribe_pct", "professional", "MedScribe", "vals.ai", "-", 109, "2026-10-13"),
    BenchmarkSlot("medcode_pct", "professional", "MedCode", "vals.ai", "-", 107, "2026-10-13"),
    BenchmarkSlot("sage_pct", "professional", "SAGE", "vals.ai", "-", 91, "2026-10-08"),
    BenchmarkSlot("harvey_lab_pct", "professional", "Harvey LAB", "vals.ai", "-", 79, "2026-10-12"),
    BenchmarkSlot("legal_research_pct", "professional", "Legal Research Bench", "vals.ai", "-", 78, "2026-10-12"),
    BenchmarkSlot("finance_agent_v2_pct", "professional", "Finance Agent", "vals.ai", "v2", 78, "2026-10-12"),
    BenchmarkSlot("tax_agent_bench_pct", "professional", "Tax Agent Bench", "vals.ai", "-", 69, "2026-10-12"),
    BenchmarkSlot("public_benefits_bench_pct", "professional", "Public Benefits Bench", "vals.ai", "v1.1", 50, "2026-10-12"),
    BenchmarkSlot("vals_index_pct", "professional", "Vals Index", "vals.ai", "-", 48, "2026-10-13"),
    # data
    BenchmarkSlot("excel_modeling_pct", "data", "Excel Modeling Benchmark", "vals.ai", "-", 74, "2026-10-12"),
    BenchmarkSlot("livebench_2_0_data_analysis", "data", "LiveBench", "livebench.ai", "2.0", 40, "2026-10-14"),
    BenchmarkSlot("aa_analyst_agent_pct", "data", "AA-AnalystAgent", "artificialanalysis.ai", "-", None, "2026-10"),
    # browser
    BenchmarkSlot("arena_agent_score", "browser", "Arena Agent", "arena.ai", "-", 52, "2026-10-15"),
    BenchmarkSlot("livebench_2_0_browser_use", "browser", "LiveBench", "livebench.ai", "2.0", 40, "2026-10-14"),
    # multimodal
    BenchmarkSlot("mmmu_pro_pct", "multimodal", "MMMU-Pro", "artificialanalysis.ai", "-", 19, "2026-10"),
    BenchmarkSlot("arena_vision_elo", "multimodal", "Arena Vision", "arena.ai", "-", None, "2026-10-15"),
    # long_context
    BenchmarkSlot("aa_lcr_v1_1_pct", "long_context", "AA-LCR", "artificialanalysis.ai", "v1.1", None, "2026-10"),
    BenchmarkSlot("livebench_2_0_research", "long_context", "LiveBench", "livebench.ai", "2.0", 40, "2026-10-14"),
    # instruction
    BenchmarkSlot("ifbench_pct", "instruction", "IFBench", "artificialanalysis.ai", "-", None, "2026-10"),
)

QUALITY_AXES: tuple[str, ...] = tuple(
    dict.fromkeys(s.axis for s in BENCHMARK_SLOTS)
)

AXIS_LABEL: dict[str, str] = {
    "general": "preferencia humana",
    "reasoning": "razonamiento, matematica y ciencia",
    "coding": "programacion",
    "agentic": "herramientas y agentes",
    "professional": "tareas profesionales reales",
    "data": "planillas y analisis de datos",
    "browser": "navegador",
    "multimodal": "imagen y documento",
    "long_context": "contexto largo",
    "instruction": "cumplimiento de instrucciones",
}

BENCHMARK_COLUMNS: tuple[str, ...] = tuple(s.column for s in BENCHMARK_SLOTS)

# Columnas que no son benchmarks pero tampoco se derivan de otro campo: vienen
# directo de una fuente externa. Artificial Analysis las publica en la misma
# tabla que sus evaluaciones, asi que entran por el mismo snapshot.
DIRECT_METRIC_COLUMNS: tuple[str, ...] = (
    "speed_tok_s",
    "latency_ttft_s",
    "intelligence_index",
    "coding_index",
    "math_index",
)

# Toda columna que puede llegar por snapshot.
SNAPSHOT_COLUMNS: tuple[str, ...] = BENCHMARK_COLUMNS + DIRECT_METRIC_COLUMNS

AXIS_COLUMNS: tuple[str, ...] = tuple(f"quality_{a}" for a in QUALITY_AXES)
AXIS_N_COLUMNS: tuple[str, ...] = tuple(f"{c}_n_sources" for c in AXIS_COLUMNS)


def _axis_columns() -> tuple[Column, ...]:
    """Columnas derivadas de agrupar benchmarks por dimension.

    **No son features de clustering.** Un eje promedio ranks de benchmarks que
    no cubren a los mismos modelos, asi que dos filas con el mismo valor no son
    la misma medicion. Quedan como reporte; la feature es el benchmark suelto
    que elige `frame.select_dimension_benchmarks`.
    """
    generated: list[Column] = []
    for axis in QUALITY_AXES:
        generated.append(
            Column(
                f"quality_{axis}",
                REPORT,
                "float64",
                "calidad-ejes",
                f"Rank percentil promedio de la dimension {axis}: {AXIS_LABEL.get(axis, axis)}.",
            )
        )
        generated.append(
            Column(
                f"quality_{axis}_n_sources",
                INPUT,
                "Int64",
                "calidad-ejes",
                f"Cuantos benchmarks aportaron a la dimension {axis} en ese modelo.",
            )
        )
    return tuple(generated)


# Contrato completo: columnas estaticas + generadas por dimension.
COLUMNS: tuple[Column, ...] = COLUMNS_STATIC + _axis_columns()

COLUMN_BY_NAME: dict[str, Column] = {c.name: c for c in COLUMNS}

# Alias: el autor llama "dimension" a lo que el codigo llamo "axis".
DIMENSIONS: tuple[str, ...] = QUALITY_AXES

# Features que no dependen de ningun benchmark.
BASE_FEATURES: tuple[str, ...] = ("speed_tok_s", "latency_ttft_s")

# Las features completas dependen de la seleccion por dimension, que se calcula
# sobre los datos (`frame.training_features`). No son una constante.

# --------------------------------------------------------------------------
# Universo de modelos
# --------------------------------------------------------------------------

UNIVERSE_MIN = 41
UNIVERSE_MAX = 100
WINDOW_DAYS = 365
FRESHNESS_DAYS = 7

# Entrada curada por el autor: laboratorio -> modelo mejor posicionado.
# Orden segun Artificial Analysis Intelligence Index al corte.
# No se deriva del dataset ("tamano y presencia en las noticias" no es medible).
MUST_INCLUDE_LABS: dict[str, str] = {
    "anthropic": "Claude Opus 5.5",
    "meta": "Muse Wonder Full",
    "openai": "GPT-6 Astra",
    "google": "Gemini 4 Argon",
    "spacexai": "Grok 4.7",
    "xiaomi": "MiMo-V2.6-Pro",
    "alibaba": "Qwen3.8 Max",
    "z-ai": "GLM-5.3",
    "stepfun": "Step 5 Preview",
    "moonshot": "Kimi K3",
    "inclusionai": "Ling 3.1 Flash",
    "deepseek": "DeepSeek V4.1 Flash",
    "mistral": "Mistral Large 4 Preview",
    "sapiens-ai": "Agnes 2.5 Pro Beta",
    "china-mobile": "JT-4.1 Flash 236B A21B",
    "motif-technologies": "Motif 3",
    "institute-of-foundation-models": "K2 Horizon 375B A23B",
    "reflection": "Beam 1.0",
    "minimax": "MiniMax-M3",
    "nex-agi": "Nex-N2-Pro",
}

# --------------------------------------------------------------------------
# Exclusiones del universo
# --------------------------------------------------------------------------

# Routers y aliases: no son modelos.
EXCLUDE_ROUTER = (
    r"^openrouter/",
    r"^~",
    r"auto$",
    r"fusion",
    r"pareto",
    r"switchyard",
    r"jev-router",
    r"-latest$",
)

# Guardrails y clasificadores.
EXCLUDE_GUARD = (
    r"content-safety",
    r"llama-guard",
    r"safeguard",
    r"guardrails",
)

# Modelos de una sola tarea.
EXCLUDE_SINGLE_TASK = (
    r"morph-v3",
    r"relace",
    r"schematron",
    r"summarize",
    r"hy-mt2",
    r"-embed",
    r"embedding",
    r"rerank",
)

# Imagen / audio / musica puros.
EXCLUDE_MEDIA = (
    r"nano-banana",
    r"-image",
    r"^.*image$",
    r"gpt-image",
    r"gpt-audio",
    r"lyria",
    r"whisper",
    r"tts",
    r"voice-",
)

# Roleplay y narrativa.
EXCLUDE_ROLEPLAY = (
    r"^aion-",
    r"cydonia",
    r"skyfall",
    r"euryale",
    r"magnum",
    r"unslopnemo",
    r"mythomax",
    r"uncensored",
)

EXCLUDE_ALL: tuple[str, ...] = (
    EXCLUDE_ROUTER + EXCLUDE_GUARD + EXCLUDE_SINGLE_TASK + EXCLUDE_MEDIA + EXCLUDE_ROLEPLAY
)

# Variantes que colapsan al modelo canonico.
VARIANT_SUFFIX = (":free", ":batch", ":nitro", ":thinking", ":extended", ":online")

# Tokens que no distinguen familia (version, esfuerzo, estado).
FAMILY_STOPWORDS = frozenset(
    {
        "high", "low", "medium", "max", "min", "minimal", "effort", "thinking",
        "reasoning", "xhigh", "preview", "exp", "experimental", "latest", "beta",
        "alpha", "chat", "instruct", "base", "it", "turbo", "air", "lite",
        "v", "rev", "version", "stable", "edge", "online", "free", "nitro",
        # Ruido de los nombres de leaderboard (no distinguen familia).
        "with", "fallback", "non", "none", "default", "model", "models",
        "provider", "providers", "via", "direct", "api", "the", "and", "llm",
    }
)

# Palabras que se ignoran al unir nombres **entre fuentes**. A diferencia de
# FAMILY_STOPWORDS, aca NO se borran numeros: la version y el tamano son lo que
# distingue `gemma-4-31b` de `gemma-4-12b`, y borrarlos produce matches falsos.
MATCH_STOPWORDS = frozenset({"it", "instruct", "base", "latest", "exp", "experimental", "hf"})

# Variantes de esfuerzo de un mismo modelo, de mayor a menor. Cuando la fuente
# publica varias, se elige siempre la de mayor rango para que el resultado sea
# determinista; la eleccion queda registrada en el snapshot.
EFFORT_RANK: dict[str, int] = {
    "max": 8,
    "xhigh": 7,
    "high": 6,
    "medium": 5,
    "default": 4,
    "low": 3,
    "minimal": 2,
    "non-reasoning": 1,
    "thinking": 1,
}

