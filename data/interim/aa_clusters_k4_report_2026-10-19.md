# Clusters con k=4 en el plano PC1 x PC2

- Entrada: `aa_pca_nolat_2026-10-19.parquet` y `aa_models_2026-10-19.parquet`
- Filas: 24 | k = 4 | `random_state=42`, `n_init=10`
- Los clusters se renumeran por PC1 ascendente: 0 es el de menor capacidad.
- Las variables crudas se promedian en sus unidades originales, sin `log1p`.

## Centroides en el plano de componentes

| Cluster | n | PC1 | PC2 |
|---|---:|---:|---:|
| 0 | 4 | -3.44 | +0.42 |
| 1 | 11 | -0.20 | -0.08 |
| 2 | 5 | +1.26 | -0.77 |
| 3 | 4 | +2.41 | +0.76 |

## Promedios de las variables crudas

| Variable | C0 | C1 | C2 | C3 | Global |
|---|---:|---:|---:|---:|---:|
| Velocidad (t/s) | 508.64 | 122.74 | 51.23 | 110.75 | 170.16 |
| Razonamiento (GDPval) | 34.70 | 52.57 | 55.49 | 65.36 | 52.33 |
| Codigo (SciCode) | 46.56 | 55.30 | 56.62 | 62.82 | 55.37 |
| Agentico (TB 4.0) | 1.39 | 24.84 | 40.30 | 56.82 | 29.48 |
| Documentos (GDP.pdf) | 9.95 | 17.89 | 25.20 | 27.20 | 19.64 |
| Latencia 1er chunk (s) | 1.42 | 41.18 | 113.99 | 304.08 | 93.54 |
| Datos (AnalystAgent) | 23.75 | 42.14 | 44.50 | 57.08 | 44.53 |
| Precio entrada (USD/1M tok) | 0.48 | 0.81 | 3.49 | 5.00 | 2.01 |

## Velocidad, latencia y tiempo por tarea no son lo mismo

Tres medidas distintas que suelen llamarse 'velocidad': el caudal una vez
que el modelo arranca a escribir, el tiempo hasta el primer token (que incluye
razonar) y el tiempo total por tarea, que combina las dos anteriores con
cuantos tokens produce la tarea.

| Medida | C0 | C1 | C2 | C3 |
|---|---:|---:|---:|---:|
| Velocidad de salida (t/s) | 508.6 | 122.7 | 51.2 | 110.7 |
| Latencia primer token (s) | 1.4 | 41.2 | 114.0 | 304.1 |
| Primer token de respuesta (s) | 6.9 | 56.1 | 141.8 | 307.5 |
| Fin a fin de una respuesta (s) | 8.2 | 61.2 | 152.0 | 312.5 |
| Tiempo por tarea (s) | 80.2 | 597.7 | 1,106.1 | 702.8 |
| Tokens por tarea | 40,415.6 | 75,796.6 | 57,159.0 | 112,234.7 |

El grupo de trabajo pesado no es el de menor caudal por casualidad: genera a
la mitad de velocidad que el de frontera y eso lo vuelve el mas caro en tiempo
por tarea. El de frontera tiene caudal alto pero arranca tarde y escribe
mucho, asi que queda en un punto medio. Un modelo puede ser rapido
escribiendo y lento respondiendo: son ejes distintos.


## Nombres y descripcion

### 0. Velocistas - 4 modelos

El grupo mas rapido del conjunto (509 t/s) y el menos capaz: 1,4 puntos en Terminal-Bench y 10 en GDP.pdf, contra 25 y 18 del grupo siguiente. Responden en 1,4 s pero no completan tareas que requieran herramientas o varios pasos. Sirven para generar volumen, no para trabajo agentico.

| Modelo | Proveedor | PC1 | PC2 |
|---|---|---:|---:|
| Beam 1.0 | Reflection | -3.03 | +0.11 |
| Inkling (Xhigh) | Thinking Machines | -3.20 | -0.54 |
| Nemotron 3.5 Super VL | NVIDIA | -3.59 | +0.47 |
| K2 Horizon 375B A23B | Institute of Foundation Models | -3.94 | +1.63 |

### 1. Equilibrados - 11 modelos

El centro de la distribucion y el grupo mas numeroso: once modelos, 123 t/s, 41 s hasta el primer token y calidad intermedia (53 de razonamiento, 25 de agentico). No es un arquetipo sino el promedio del mercado: contiene modelos de diez proveedores distintos y es donde cae cualquier modelo que no sobresalga en ninguna direccion.

| Modelo | Proveedor | PC1 | PC2 |
|---|---|---:|---:|
| Grok 4.7 (Xhigh) | SpaceXAI | +0.59 | -0.01 |
| GLM-5.3 (Max) | Z AI | +0.35 | +0.44 |
| Step 5 Preview | StepFun | +0.24 | +0.11 |
| DeepSeek V4.1 Flash 1017 (Max) | DeepSeek | +0.14 | +1.18 |
| Claude Haiku 5.5 (Max) | Anthropic | -0.02 | +0.88 |
| GLM-5.3-Flash | Z AI | -0.11 | -0.28 |
| Mistral Large 4 Preview | Mistral | -0.30 | -0.78 |
| Gemini 3.8 Flash (High) | Google | -0.41 | -0.01 |
| GPT-6 Luna (Max) | OpenAI | -0.55 | -0.42 |
| Muse Spark Open (Xhigh) | Meta | -0.76 | -0.15 |
| Qwen3.8 27B (Xhigh) | Alibaba | -1.35 | -1.83 |

### 2. Trabajo pesado - 5 modelos

Sacrifican velocidad por trabajo agentico y documental: 40 puntos en Terminal-Bench y 25 en GDP.pdf. Generan a 51 t/s, la mitad que el grupo de frontera, y por eso son **los mas lentos de punta a punta**: 1.106 s por tarea, el doble que el resto. El unico grupo que mezcla OpenAI, Alibaba, Kimi y Xiaomi.

| Modelo | Proveedor | PC1 | PC2 |
|---|---|---:|---:|
| GPT-6 Astra (Max) | OpenAI | +1.87 | -0.37 |
| GPT-6.1 Sol (Max) | OpenAI | +1.74 | -0.67 |
| MiMo-V2.6-Pro | Xiaomi | +1.23 | -0.42 |
| Qwen3.8 Max (0902) | Alibaba | +0.95 | -1.11 |
| Kimi K3 (Max) | Kimi | +0.52 | -1.28 |

### 3. Frontera reflexiva - 4 modelos

El techo de calidad del conjunto: 65 de razonamiento, 57 de agentico y 57 en datos. **No es lento generando**: escribe a 111 t/s, el segundo caudal mas alto. Lo que lo hace tardar es el arranque: 304 s hasta el primer token, porque razona antes de emitir, y salidas de 112.000 tokens por tarea, el doble que el resto. Queda en 703 s por tarea, menos que el grupo de trabajo pesado. Tres de sus cuatro modelos son Claude y el cuarto es Muse Wonder.

| Modelo | Proveedor | PC1 | PC2 |
|---|---|---:|---:|
| Claude Opus 5.5 (Max, Default Fallback) | Anthropic | +2.92 | +0.94 |
| Claude Fable 5.1 (Max, Default Fallback) | Anthropic | +2.32 | +0.16 |
| Claude Sonnet 5.5 (Max, Default Fallback) | Anthropic | +2.29 | +1.14 |
| Muse Wonder (Max) | Meta | +2.09 | +0.82 |
