# Dimensiones de evaluación de LLM

Mapa de los ejes que miden los benchmarks públicos, para decidir cuáles entran como features del clustering y cuáles se declaran como limitación del artículo.

## Dos familias

- **Capacidad / calidad**: qué tan bien hace una tarea ("¿sabe hacer X?").
- **Operativas / económicas**: cuánto cuesta, cuán rápido, cuán disponible, cuánto contexto soporta.

Una tercera familia, **comportamiento** (seguridad, sesgo, sycophancy), rara vez cambia el clustering pero sí puede descartar un modelo para un caso de uso.

## Advertencias metodológicas (aplican a todo el mapa)

- **Los scores no son comparables entre harnesses.** Cambian con el prompt template, los few-shots, la temperatura, `pass@1` vs `pass@k` y si el número lo reporta el vendor o un tercero.
- **Contaminación y saturación.** MMLU, GSM8K y HumanEval están saturados y contaminados. Usar MMLU-Pro, GPQA Diamond, LiveCodeBench, HLE, ARC-AGI-2.
- **"Agente" no es una dimensión, son tres:** tool-call de un turno ≠ loop multi-turno con estado ≠ horizonte largo tipo SWE-bench. No promediar.
- **Siempre con fecha de corte.** Un benchmark de 2024 no dice nada de un modelo de 2026.

## Conocimiento y razonamiento

| Dimensión | Benchmarks | Qué mide |
|---|---|---|
| Conocimiento general | MMLU, MMLU-Pro, SuperGPQA | conocimiento académico y multidisciplinario |
| Conocimiento experto | GPQA Diamond, HLE | techo de dificultad, PhD-level |
| Razonamiento abstracto | ARC-AGI-1/2, BBH, ZebraLogic, MuSR | lógica novedosa, no memorizada |
| Matemática | GSM8K, MATH, AIME, HMMT, FrontierMath, MathArena | aritmética → olimpiada → investigación |
| Verdad factual | SimpleQA, FreshQA, FACTS Grounding, HaluEval | alucinación y grounding |
| Calibración | HELM (calibration) | ¿sabe cuándo no sabe? |
| Instrucciones | IFEval, IFBench, Multi-IF, Arena-Hard | cumplimiento de restricciones |
| Salida estructurada | JSONSchemaBench, IFEval (format), structured-output de BFCL | JSON/schema compliance |

## Código y desarrollo

| Dimensión | Benchmarks |
|---|---|
| Generación de funciones | HumanEval, MBPP, BigCodeBench, LiveCodeBench |
| Repo-level / reparación real | SWE-bench Verified, SWE-bench Pro, RepoBench, Commit0 |
| Terminal / CLI agéntico | Terminal-Bench, Aider Polyglot, SWE-bench Multimodal |
| Código competitivo | Codeforces (Elo), LiveCodeBench |
| Código científico | SciCode |
| Web dev (visual) | WebDev Arena |
| Seguridad de código | CyberSecEval, evals de código seguro |

## Agentes: herramientas, MCP y APIs

| Dimensión | Benchmarks |
|---|---|
| Function calling / tools | BFCL, ToolBench, API-Bank, Nexus, τ-bench, τ²-bench |
| **Uso de MCP** | MCP-Universe, MCPMark, MCPEval, MCP-Bench, Toolathlon (todos 2025 — verificar vigencia y cobertura) |
| Procesos de negocio con usuario simulado | τ-bench (retail/airline), τ²-bench (telecom) |
| Multi-agente / orquestación | AgentBench, GAIA (niveles 1-3) |
| Inyección de prompt en agentes | AgentDojo |

## Agentes: computadora y navegador

| Dimensión | Benchmarks |
|---|---|
| Uso de navegador | WebArena, VisualWebArena, Mind2Web, WebVoyager, Online-Mind2Web, BrowseComp |
| Uso de PC / sistema operativo | OSWorld, WindowsAgentArena, AndroidWorld |
| Grounding visual de UI | ScreenSpot, ScreenSpot-Pro |

## Productividad de oficina y documentos

| Dimensión | Benchmarks |
|---|---|
| **Excel / planillas** | SpreadsheetBench, OfficeBench, SheetCopilot, TableBench, WikiTableQuestions |
| Word / PPT | OfficeBench, GDPval |
| Entregables profesionales reales | GDPval (44 ocupaciones, entregables de oficina) |
| PDF / OCR / tablas | DocVQA, OCRBench, ChartQA, TableVQA, InfographicVQA |

## Research e información

| Dimensión | Benchmarks |
|---|---|
| Búsqueda profunda en web | BrowseComp, GAIA, Search Arena (LMArena), DeepResearch Bench |
| Síntesis con fuentes | FACTS Grounding, LFRQA, evals de grounding |
| Research científico | LAB-Bench, CORE-Bench, SciCode, ResearchBench |
| Contexto largo (insumo del research) | RULER, NIAH, LongBench v2, ∞Bench, AA-LCR |
| RAG | evals de RetrievalQA, LongBench, NIAH multi-doc |

## Uso profesional por dominio

| Dominio | Benchmarks |
|---|---|
| Medicina | MedQA, MedMCQA, HealthBench |
| Derecho | LegalBench, CaseHOLD |
| Finanzas | FinanceBench, FinQA, TAT-QA |
| Ciberseguridad | Cybench, CyberSecEval |
| Exámenes profesionales | GPQA, AGIEval, USMLE, BAR |
| Trabajo de conocimiento genérico | GDPval |

## Multimodal

| Modalidad | Benchmarks |
|---|---|
| Imagen | MMMU / MMMU-Pro, MMBench, RealWorldQA, MathVista |
| Documento | DocVQA, ChartQA, OCRBench |
| Video | Video-MME, MVBench, LongVideoBench |
| Audio / voz | MMAU, AudioBench, VoiceBench |
| Generación de imagen | GenEval, ImagenHub, LMArena image arena |

## Lenguaje: escritura y preferencia

| Dimensión | Benchmarks |
|---|---|
| Preferencia humana | LMArena (Chatbot Arena): ELO global + por categoría (hard prompts, coding, math, creative writing, instrucciones, consultas largas, multi-turno) |
| Escritura creativa | LMArena creative writing, EQ-Bench creative writing |
| Traducción | FLORES-200, WMT24, Belebele |
| Multilingüe | Global-MMLU, Multi-IF, MMLU multilingual |
| Resumen y QA largo | LongBench, NarrativeQA |

## Seguridad y comportamiento

| Dimensión | Benchmarks |
|---|---|
| Rechazo seguro | HarmBench, StrongREJECT, JailbreakBench, AdvBench |
| Sesgo y toxicidad | HELM (bias), BOLD, BBQ, RealToxicityPrompts |
| Robustez | HELM (robustness), AgentDojo |
| Sycophancy / adulación | SycophancyEval, EQ-Bench |

## Dimensiones operativas (las que ya tenemos en el contrato)

| Dimensión | Fuente |
|---|---|
| Precio in/out | OpenRouter, Artificial Analysis |
| Velocidad (output tok/s) | Artificial Analysis |
| Latencia (TTFT) | Artificial Analysis |
| Contexto y max output | OpenRouter |
| Disponibilidad | `n_providers`, uptime y rate limits de OpenRouter |
| Caching | `pricing.input_cache_read` / `input_cache_write` |
| Eficiencia de tokens | tokenizer + overhead de tokens de razonamiento (lo que no ves en el precio) |

## Cómo usar esto en el clustering

Son ~40 ejes y muchos correlacionan: un índice de "inteligencia" ya es un compuesto de conocimiento + razonamiento + matemática. **No metas un benchmark por dimensión.**

El clustering usa **solo rendimiento y los ejes de calidad**. El mapa completo eje → benchmark → fuente está en *Mapa eje → benchmarks y fuentes*, más abajo.

**No son features de clustering**: `context_length`, `max_output_tokens`, `is_open_weights`, `supports_*`, `n_providers`, `params_total`, `hf_downloads`, `src_*` y los precios. Se usan para filtrar, etiquetar, auditar o graficar.

## Mapeo caso de uso → ejes

| Caso de uso | Ejes que importan |
|---|---|
| Desarrollo de software (IDE, PRs) | código, contexto, precio out, latencia |
| Uso de MCP / agentes con herramientas | agentic/tools, contexto, latencia, precio |
| Uso profesional / entregables | GDPval-style, razonamiento, multimodal documento |
| Research / búsqueda profunda | búsqueda, contexto largo, síntesis con fuentes, costo |
| Conocimiento general y chat | preferencia humana, conocimiento, precio in |
| Excel / planillas | tabla+razonamiento, salida estructurada, costo |
| PC y navegador (automatización) | agentic OS/browser, grounding visual |
| Alto volumen / clasificación | precio in, velocidad, contexto |
| Datos sensibles / on-prem | open-weights, licencia, params |

El precio aparece en este mapeo porque es un **criterio de decisión del lector**, no un eje de clustering: no entra en la distancia, se comunica con el tamaño del punto.

## Gaps frente a nuestras fuentes

**No** tenemos medición directa de MCP, PC/navegador ni Excel en OpenRouter, Artificial Analysis ni LMArena. Opciones:

1. Declararlo como **limitación** y aproximar por proximidad en el espacio de features (un modelo bueno en agentic/tools probablemente lo sea en MCP).
2. Incorporar una **fuente específica** cuando exista (p. ej. leaderboards de MCP o de agentes) y tratarla como `src_*` adicional.
3. Usar `supports_tools` como proxy binario — es lo más honesto si no hay score: **capacidad declarada ≠ desempeño medido**, y el artículo debe decir explícitamente cuál de las dos está usando.

## Cobertura medida (corte 2026-10-16)

Cantidad de modelos evaluados por cada benchmark, leída directamente de su leaderboard. Es el criterio para elegir **con qué fuente medir cada dimensión**: gana la que más modelos cubre.

| Benchmark | Modelos | Denominador que publica | Fuente / corte |
|---|---|---|---|
| Arena Text | 416 | 416 | arena.ai/leaderboard/text, 2026-10-15 |
| BFCL V4 (tool use) | 109 | — | gorilla.cs.berkeley.edu/leaderboard, 2026-04-12 |
| Arena Agent | 52 | 52 | arena.ai/leaderboard/agent, 2026-10-15 |
| SWE-bench Verified (bash-only) | 47 | — | swebench.com, 2026-02-17 |
| AA Intelligence Index v4.3.2 | 32 | de 694 | artificialanalysis.ai, 2026-10 |
| AA Terminal-Bench 4.0 | 32 | de 222 | idem |
| AA MMMU-Pro | 19 | de 288 | idem |
| AA τ²-Bench Telecom | 6 | de 440 | idem |
| SpreadsheetBench V2 | ~6 | — | spreadsheetbench.github.io, 2026-09 |
| OSWorld | sin conteo público | — | 361 tareas, 2026-06 |
| MCP-Universe | sin conteo público | — | Salesforce AI Research, 2025 |
| OpenRouter (catálogo, **no** eval) | 465 | — | `/api/v1/models`, 2026-10-16 |

**Hallazgo**: la cobertura cae un orden de magnitud entre las dimensiones de texto (100-400 modelos) y las agénticas (6-52). Elegir "el benchmark con más cobertura" para MCP, OS/navegador o Excel implica aceptar menos de 30 modelos medidos, y en Excel/MCP menos de 10.

**Efecto del filtro de selección de modelos** (últimos 12 meses, uno por proveedor+familia, descartar lo publicado hace <1 semana): reduce el universo de ~465 a unas pocas decenas y **penaliza a los benchmarks que no se actualizan**. Los evals nuevos de AA son justamente los de denominador más chico (6-32), así que después del filtro quedan aún más chicos.

**Pendiente**: el conteo exacto *post-filtro* sale del cruce `modelos del leaderboard ∩ universo filtrado`. Eso es lo que tienen que calcular `src/research.py` y `src/clean.py`; los números de arriba son el denominador bruto.

## Benchmarks de calidad incorporables (corte 2026-10-16)

Catálogo ampliado. La columna *Eje* indica a qué feature agregada alimenta cada benchmark (ver *Agregación por eje* en `metodologia-clustering.md`).

| Benchmark | Modelos | Eje | Fuente / corte |
|---|---|---|---|
| LegalBench | 151 | professional | vals.ai, 2026-10-13 |
| Vibe Code Bench v1.1 | 112 | coding | vals.ai, 2026-10-12 |
| MedScribe | 109 | professional | vals.ai, 2026-10-13 |
| BFCL V4 | 109 | agentic | Berkeley, 2026-04-12 |
| MedCode | 107 | professional | vals.ai, 2026-10-13 |
| SAGE | 91 | professional | vals.ai, 2026-10-08 |
| Harvey LAB | 79 | professional | vals.ai, 2026-10-12 |
| Legal Research Bench | 78 | professional | vals.ai, 2026-10-12 |
| Finance Agent v2 | 78 | professional | vals.ai, 2026-10-12 |
| Code Migration | 77 | coding | vals.ai, 2026-10-12 |
| Excel Modeling Benchmark | 74 | data | vals.ai, 2026-10-12 |
| Tax Agent Bench | 69 | professional | vals.ai, 2026-10-12 |
| ProgramBench | 64 | coding | vals.ai, 2026-10-12 |
| ProofBench v1.1 | 52 | reasoning | vals.ai, 2026-10-12 |
| Arena Agent | 52 | browser | arena.ai, 2026-10-15 |
| Public Benefits Bench | 50 | professional | vals.ai, 2026-10-12 |
| Vals Index | 48 | professional | vals.ai, 2026-10-13 |
| Terminal-Bench 4.0 | 48 | agentic | vals.ai, 2026-10-13 |
| CyberBench | 47 | agentic | vals.ai, 2026-10-12 |
| SWE-bench Verified | 47 | coding | swebench.com, 2026-02-17 |
| IOI | 44 | coding | vals.ai, 2026-10-14 |
| Terminal-Bench Science | 41 | reasoning | vals.ai, 2026-10-14 |
| LiveBench 2.0 (7 suites) | ~40 | una suite por eje | livebench.ai, 2026-10-14 |
| SRE Bench | 35 | agentic | vals.ai, 2026-10-14 |
| SkillsBench | 35 | agentic | vals.ai, 2026-09-27 |
| Arena Vision | sin conteo | multimodal | arena.ai |
| MMMU-Pro | 19 | multimodal | AA, 2026-10 |
| SpreadsheetBench V2 | ~6 | data | spreadsheetbench, 2026-09 |
| Aider polyglot | sin conteo | coding | aider.chat, **2025-11-20** |

### Mapa eje → benchmarks y fuentes

De qué se compone cada feature `quality_*`. La columna *Modelos* es la cobertura medida de esa combinación versión + host, al 2026-10-16.

| Eje | Benchmark | Host | Modelos |
|---|---|---|---|
| **general** | Arena Text (ELO) | arena.ai | 416 |
| **reasoning** | ProofBench v1.1 | vals.ai | 52 |
| | Terminal-Bench Science | vals.ai | 41 |
| | LiveBench 2.0 · Reasoning | livebench.ai | ~40 |
| | GPQA Diamond | AA | ~32 |
| | HLE | AA | ~32 |
| **coding** | Vibe Code Bench v1.1 | vals.ai | 112 |
| | Code Migration | vals.ai | 77 |
| | ProgramBench | vals.ai | 64 |
| | SWE-bench Verified | swebench.com | 47 |
| | IOI | vals.ai | 44 |
| | LiveBench 2.0 · Coding | livebench.ai | ~40 |
| **agentic** | BFCL V4 | Berkeley | 109 |
| | Terminal-Bench 4.0 | vals.ai **o** AA | 48 / 32 |
| | CyberBench v1.1 | vals.ai | 47 |
| | LiveBench 2.0 · Agentic | livebench.ai | ~40 |
| | SkillsBench | vals.ai | 35 |
| | SRE Bench | vals.ai | 35 |
| **professional** | LegalBench | vals.ai | 151 |
| | MedScribe | vals.ai | 109 |
| | MedCode | vals.ai | 107 |
| | SAGE | vals.ai | 91 |
| | Harvey LAB | vals.ai | 79 |
| | Legal Research Bench | vals.ai | 78 |
| | Finance Agent v2 | vals.ai | 78 |
| | Tax Agent Bench | vals.ai | 69 |
| | Public Benefits Bench v1.1 | vals.ai | 50 |
| | Vals Index | vals.ai | 48 |
| **data** | Excel Modeling Benchmark | vals.ai | 74 |
| | LiveBench 2.0 · Data Analysis | livebench.ai | ~40 |
| | AA-AnalystAgent | AA | sin conteo |
| **browser** | Arena Agent | arena.ai | 52 |
| | LiveBench 2.0 · Browser Use | livebench.ai | ~40 |
| **multimodal** | MMMU-Pro | AA | 19 |
| | Arena Vision | arena.ai | sin conteo |
| **long_context** | AA-LCR v1.1 | AA | sin conteo |
| | LiveBench 2.0 · Research | livebench.ai | ~40 |
| **instruction** | IFBench | AA | sin conteo |

Tres cosas a revisar antes de dar por bueno el bloque de calidad:

- **LiveBench sostiene 5 de los 10 ejes.** Un solo proveedor alimenta la mitad del bloque: si rearma las suites, cinco ejes se mueven juntos.
- **Cinco ejes dependen de una sola fuente** (`general`, `instruction`, `multimodal`, `long_context`, `browser`). El eje más frágil es `instruction`: una sola fuente y sin conteo público.
- **Descartados por cobertura**: `τ²-Bench Telecom` (6 modelos) y `SWE-bench Multimodal` (18). No sostienen un eje.

**LiveBench 2.0 es la mejor incorporación individual.** Sus 7 suites —Agentic, Reasoning, Coding, Browser Use, Data Analysis, Research, Design— son casi ortogonales entre sí y cubren de una sola vez tres dimensiones que no teníamos con ninguna fuente: **navegador**, **análisis de datos** y **diseño**. Se usa el score de cada suite, no el overall, para que no cuente doble en los ejes.

**Aider polyglot quedó sin actualizar desde el 20-nov-2025.** Un dato de hace 11 meses no cubre los modelos nuevos del universo: descartado.

**HELM (Stanford) no se pudo relevar**: la página no devolvió contenido parseable. Queda como fuente a revisar manualmente si hace falta otra medición académica amplia.

### Familias con varias versiones vivas

Cada fila exige elegir **una** versión y **un** host. Detectadas al 2026-10-16:

| Familia | Versiones conviviendo | Qué las separa |
|---|---|---|
| Terminal-Bench | 2.0 · 2.1 · 4.0 · Hard · Science | 4.0 son 66 tareas difíciles; AA publica 4.0 con 32 modelos y Vals con 48 → protocolos distintos |
| LiveBench | 1.0 · 2.0 | 2.0 rearmó las suites: agrega Browser Use, Data Analysis y Design |
| SWE-bench | original · Verified · Multimodal | Verified son 47 modelos (swebench.com); Multimodal 18 (Vals) |
| MMLU | MMLU · MMLU-Pro · Global-MMLU-Lite | Pro son 12.000 preguntas con 10 opciones; Global-MMLU-Lite es multilingüe |
| GPQA | GPQA · GPQA Diamond | Diamond son las 198 más difíciles |
| OSWorld | 1.0 · 2.0 · Verified | 369 tareas vs 361 verificadas; 2.0 es un entorno nuevo |
| AIME | 2024 · 2025 | Cambia el examen cada año |
| τ-Bench | τ²-Bench Telecom · τ³-Banking | Dominios, tareas y conocimiento distintos |
| SpreadsheetBench | V1 Full · V2 | V2 es otro conjunto con otro leaderboard |
| Public Benefits Bench | v1 (archivada) · v1.1 | Vals archiva la v1: usar la v1.1 |
| Terminal-Bench (Vals) | 2.0 · 2.1 activas · 4.0 · Science | Vals dejó 2.0 y 2.1 en archivadas |

Regla: si dos versiones miden lo mismo para el eje, se elige la de **mayor cobertura dentro del universo filtrado**, no la más nueva. Una versión nueva con 6 modelos no sirve como feature.
