# Modelos LLM: datos, decisiones y resultados

Documento de traspaso para construir una web interactiva y su texto de acompañamiento.

**Para quién**: lectores con conocimiento técnico medio. Saben qué es un benchmark, un z-score y un PCA, pero no conocen este dataset ni las decisiones que se tomaron.

**Cómo usarlo**: cada afirmación de este documento está respaldada por un número que aparece acá. Si algo no figura, no se puede afirmar. Los archivos citados existen y son los únicos datos que deben usarse.

**Fecha de corte**: 2026-10-19.

---

## 1. Objetivo

Dos entregables sobre el mismo trabajo:

1. **Una herramienta web** que permita elegir el mejor modelo para una tarea concreta.
2. **Un artículo de no más de 12 páginas** que explique los datos, la metodología, las decisiones y los resultados.

La herramienta **no es un clusterizador**. Recomendar un modelo es *rankear* por la métrica de la tarea y después filtrar por presupuesto, contexto y latencia. El agrupamiento cumple otro papel: explicar que el mercado se ordena en cuatro tramos de capacidad. Confundir las dos cosas produce una herramienta que responde "sos del grupo Frontera reflexiva" cuando el usuario preguntó qué modelo usar para escribir código.

---

## 2. Fuente de datos

**Origen único**: `https://artificialanalysis.ai/models`. No entra OpenRouter ni Vals. Esto es deliberado: los benchmarks del mismo nombre dan números distintos según el host, así que mezclarlos impediría comparar filas.

**Cómo se obtuvieron los datos**: la página no tiene endpoint público de datos. Su API v2 responde `401 API key is required` sin credenciales. Las métricas vienen embebidas en el stream RSC de Next.js que sirve la página, dentro de dos estructuras:

- `releases` (512): catálogo de modelos con creador y fecha de lanzamiento.
- `initialModels` (27): los modelos del gráfico por defecto, con ~90 campos de métricas cada uno.

El payload crudo quedó en `data/raw/aa_payload_2026-10-19.txt` (504 KB) y es inmutable. La extracción **fue manual desde el navegador**: no hay todavía un pipeline automatizado. Es una debilidad declarada en la sección 9.

**El límite más importante**: la página ofrece 706 entradas en su selector, pero solo publica métricas para 27 modelos. Los otros 679 tienen identidad y fecha y nada más. Sin una API key, el conjunto de modelos con puntajes no puede crecer.

---

## 3. Decisiones en datos

### 3.1 Universo: 24 modelos

De los 27 con métricas se conservaron 24, con el criterio de tener al menos 6 de 7 features de análisis. Los tres excluidos:

| Modelo | Features | Faltan |
|---|---:|---|
| Muse Wonder Full | 4 | velocidad, latencia, datos |
| Gemini 4 Argon | 5 | velocidad, latencia |
| MiniMax-M3.1 Flash | 4 | velocidad, latencia, datos |

No están incompletos por un error de matching: el campo `performanceByPromptType` viene nulo en el payload para esos tres. No hay de dónde obtener sus tiempos.

**Composición**: 24 modelos de 16 proveedores. Siete son de Anthropic y OpenAI (3 Claude, 4 GPT). Google aporta uno. Esto es una propiedad del dataset, no un sesgo corregible, y condiciona cualquier lectura: los grupos describen en parte la cartera de dos empresas.

### 3.2 Las siete features de análisis y su benchmark

La fuente no mide los mismos benchmarks que un pipeline de Vals. Cada dimensión usa su equivalente de Artificial Analysis, y el cambio queda declarado:

| Dimensión | Columna | Benchmark | Cobertura |
|---|---|---|---:|
| general | `intelligence_index` | AA Intelligence Index v4.3.2 | 24/24 |
| reasoning | `gdpval_normalized_pct` | GDPval-AA v2.1 | 24/24 |
| coding | `scicode_pct` | SciCode | 24/24 |
| agentic | `terminal_bench_4_0_pct` | Terminal-Bench 4.0 | 24/24 |
| professional | `gdp_pdf_all_pass_pct` | GDP.pdf | 24/24 |
| long_context | `aa_lcr_pct` | AA-LCR v1.1 | 24/24 |
| data | `analyst_agent_pct` | AA-AnalystAgent | 16/24 |
| multimodal | `mmmu_pro_pct` | MMMU-Pro | 13/24 |
| instruction | `ifbench_pct` | IFBench | **0/24** |

**No comparar estas columnas con las de Vals.** `scicode_pct` no es `vibe_code_bench_pct`: miden cosas parecidas con metodologías distintas.

### 3.3 Transformaciones

Dos features de rendimiento tienen cola muy pesada y se transforman con `log1p` antes de escalar:

| Feature | Rango crudo | IQR de z sin `log1p` | IQR de z con `log1p` |
|---|---|---:|---:|
| `speed_tok_s` | 38 – 1.061 t/s | 0,48 | **1,13** |
| `latency_ttft_s` | 0,78 – 615 s | 0,73 | **1,77** |

El IQR de z es el rango donde cae la mitad central de los modelos. Sin la transformación, el extremo infla el desvío y casi todos los modelos quedan en medio desvío: diferencias de 6× en velocidad se vuelven indistinguibles.

Después del `log1p`, las siete features quedaron con IQR de z entre 1,13 y 1,77, o sea que pesan parecido en la distancia euclidiana.

**Los puntajes de benchmark se dividieron por 100.** La fuente los publica como fracción 0-1 y acá se expresan como porcentaje.

### 3.4 Precios

| Tarifa | Cobertura | Rango (USD / 1M tokens) |
|---|---|---:|
| Entrada | 24/24 | 0,10 – 10,00 |
| Salida | 24/24 | 0,50 – 50,00 |
| Lectura de caché | 23/24 | 0,0036 – 1,00 |
| Escritura de caché | 9/24 | — |

Mediana: 1,13 de entrada y 4,12 de salida.

**El caso K2 Horizon.** Publica `0.00` de entrada y salida, y no tiene tarifa de caché. Un cero no es un precio: es la ausencia de oferta comercial. Se le asignó el mínimo observado del dataset (0,10 / 0,50 / 0,0036), que resulta ser exactamente la lista de precios de Claude Haiku 5.5 y GPT-6 Luna. La fila lleva `price_imputed = true` y `price_imputation_method = "minimo observado del dataset"`.

La consecuencia para la interfaz: **K2 Horizon va a encabezar cualquier ordenamiento por costo y no se puede contratar.** Hay que mostrarlo con esa advertencia visible, no esconderlo, porque es el modelo más rápido del conjunto y ocultarlo empobrece la comparación.

---

## 4. Decisiones en modelado

Se aplicaron exactamente cuatro, en este orden. Cada una se justifica con un número.

### 4.1 Seis features, sin `data`

`data` (AA-AnalystAgent) falta en 8 de 24. Incluirla obligaba a descartar 8 modelos y 6 proveedores. Con 6 features entran los 24.

### 4.2 Fuera la latencia de la distancia

La latencia correlaciona 0,77 con `professional` y 0,69 con `agentic`. Casi no aporta información nueva y contamina el eje de capacidad. Se excluyó del modelo, pero **se conserva como dato de la herramienta y de la figura**.

### 4.3 PCA sobre las cinco restantes, dos componentes

| Componente | Varianza | Acumulada | Qué mide |
|---|---:|---:|---|
| PC1 | 70,1% | 70,1% | capacidad (las cuatro de calidad en +0,45 a +0,49, velocidad en −0,36) |
| PC2 | 13,6% | **83,7%** | velocidad de salida (+0,87) |

La matriz de correlación muestra por qué hacía falta: el primer autovalor es 3,66 de 5, y las cuatro features de calidad correlacionan entre 0,61 y 0,84. Sin PCA, la distancia euclidiana cuenta la misma información cuatro veces.

### 4.4 KMeans con k = 4

`random_state=42`, `n_init=10`, sobre PC1 y PC2.

| k | Inercia (WCSS) | Entre (BCSS) | Entre/Dentro | Calinski-Harabasz | Davies-Bouldin | Silueta | Tamaños |
|---:|---:|---:|---:|---:|---:|---:|---|
| 3 | 21,23 | 79,18 | 3,73 | 39,2 | 0,67 | **0,476** | 4/7/13 |
| **4** | 15,43 | 84,98 | 5,51 | 36,7 | 0,68 | 0,459 | **4/11/5/4** |
| 5 | 10,22 | 90,20 | 8,83 | 41,9 | 0,63 | 0,466 | 4/4/5/5/6 |
| 6 | 7,65 | 92,77 | 12,13 | 43,7 | 0,54 | 0,467 | 1/4/4/5/5/5 |

**k = 4 se eligió por balance, no por silueta.** La silueta prefiere k=3 (0,476 contra 0,459), pero k=3 deja 13 de 24 modelos en un solo grupo casi indistinguible de la media. k=4 separa ese grupo en dos y permite describir el gradiente en cuatro tramos. El ratio entre/dentro crece de forma monótona con k por construcción, así que no sirve para elegir k; el que sí sirve es Calinski-Harabasz.

**Ningún k cumple la regla de 5 modelos por cluster.** Es la limitación estructural del conjunto y está en la sección 9.

---

## 5. Principales descubrimientos

### 5.1 El mercado se ordena en un gradiente, no en cuatro arquetipos

Los promedios crudos por cluster son **monótonos** en las seis variables: la capacidad sube de C0 a C3 y la velocidad baja, con el precio acompañando. No hay cruces.

| Variable | C0 Velocistas | C1 Equilibrados | C2 Trabajo pesado | C3 Frontera reflexiva | Global |
|---|---:|---:|---:|---:|---:|
| Velocidad (t/s) | **508,6** | 122,7 | 51,2 | 110,7 | 170,2 |
| Razonamiento (GDPval) | 34,7 | 52,6 | 55,5 | **65,4** | 52,3 |
| Código (SciCode) | 46,6 | 55,3 | 56,6 | **62,8** | 55,4 |
| Agéntico (TB 4.0) | **1,4** | 24,8 | 40,3 | **56,8** | 29,5 |
| Documentos (GDP.pdf) | 10,0 | 17,9 | 25,2 | **27,2** | 19,6 |
| Datos (AnalystAgent) | 23,8 | 42,1 | 44,5 | **57,1** | 44,5 |
| Latencia 1er token (s) | 1,4 | 41,2 | 114,0 | **304,1** | 93,5 |
| Tiempo por tarea (s) | **80** | 598 | **1.106** | 703 | — |
| Tokens por tarea | 40.416 | 75.797 | 57.159 | **112.235** | — |
| Precio entrada (USD/1M) | 0,48 | 0,81 | 3,49 | 5,00 | 2,01 |
| n | 4 | 11 | 5 | 4 | 24 |
| Proveedores | 4 | 10 | 4 | **2** | 16 |

**Cómo escribirlo**: es una escalera cortada en cuatro tramos, no cuatro formas distintas de ser un modelo. El lector técnico que mire esta tabla va a notar la monotonía de inmediato; anticiparlo es más fuerte que ocultarlo.

### 5.2 Los cuatro tramos

**C0 · Velocistas — 4 modelos.** El grupo más rápido (509 t/s) y el menos capaz: 1,4 puntos en Terminal-Bench y 10 en GDP.pdf, contra 25 y 18 del tramo siguiente. Responden en 1,4 s pero no completan tareas que requieran herramientas o varios pasos. Sirven para generar volumen, no para trabajo agéntico.
*Beam 1.0, Inkling, K2 Horizon 375B A23B, Nemotron 3.5 Super VL.*

**C1 · Equilibrados — 11 modelos.** El centro de la distribución y el grupo más numeroso: 123 t/s, 41 s hasta el primer token, calidad intermedia. No es un arquetipo sino el promedio del mercado: diez proveedores distintos y el lugar donde cae cualquier modelo que no sobresalga en ninguna dirección.
*Claude Haiku 5.5, DeepSeek V4.1 Flash 1017, GLM-5.3, GLM-5.3-Flash, GPT-6 Luna, Gemini 3.8 Flash, Grok 4.7, Mistral Large 4 Preview, Muse Spark Open, Qwen3.8 27B, Step 5 Preview.*

**C2 · Trabajo pesado — 5 modelos.** Sacrifican velocidad por trabajo agéntico y documental: 40 en Terminal-Bench y 25 en GDP.pdf. Generan a 51 t/s, la mitad que el tramo de frontera, y por eso son **los más lentos de punta a punta**: 1.106 s por tarea, el doble que el resto. Único grupo que mezcla OpenAI, Alibaba, Kimi y Xiaomi.
*GPT-6 Astra, GPT-6.1 Sol, Kimi K3, MiMo-V2.6-Pro, Qwen3.8 Max.*

**C3 · Frontera reflexiva — 4 modelos.** El techo de calidad: 65 de razonamiento, 57 de agéntico y 57 en datos. **No es lento generando**: escribe a 111 t/s, el segundo caudal más alto. Lo que lo hace tardar es el arranque (304 s hasta el primer token, porque razona antes de emitir) y salidas de 112.000 tokens por tarea, el doble que el resto. Tres de sus cuatro modelos son Claude y el cuarto es Muse Wonder: solo dos proveedores.
*Claude Fable 5.1, Claude Opus 5.5, Claude Sonnet 5.5, Muse Wonder.*

### 5.3 "Velocidad" son tres cosas distintas

Es el hallazgo que más cuidado exige al escribir, porque induce a error.

| Medida | C0 | C1 | C2 | C3 |
|---|---:|---:|---:|---:|
| Velocidad de salida (t/s) | 508,6 | 122,7 | 51,2 | 110,7 |
| Latencia primer token (s) | 1,4 | 41,2 | 114,0 | **304,1** |
| Tiempo por tarea (s) | **80** | 598 | **1.106** | 703 |

- **Caudal**: tokens por segundo una vez que arrancó.
- **Latencia**: cuánto tarda en emitir el primer token, y adentro está el razonamiento. Claude Opus 5.5 tarda 615 s en decir la primera palabra.
- **Tiempo por tarea**: la combinación de las dos más cuánto escribe.

**C3 tiene caudal alto y arranque tardísimo. C2 tiene caudal bajo y arranque moderado. Al multiplicar, C2 es el más lento de punta a punta.** Cualquier gráfico que use solo caudal va a mostrar a C3 como rápido y a invitar a la conclusión contraria a la que corresponde para una decisión real.

### 5.4 Cobertura por tarea: el alcance real de la herramienta

| Estado | Tareas | Modelos |
|---|---|---:|
| Completa | general, reasoning, coding, agentic, professional, long_context | 24/24 |
| Parcial | data, multimodal | 16 y 13 |
| Sin dato | instruction | 0 |

Esto define el producto: **seis tareas con el universo completo, dos parciales, una imposible**. En las parciales la interfaz debe mostrar "sin dato" junto al modelo en vez de omitirlo, o el usuario recibirá un ranking de 13 creyendo que son los mejores de 24.

### 5.5 El costo no sigue sola la capacidad

El precio de entrada va de 0,48 a 5,00 USD/1M entre los tramos, un factor de 10, mientras la capacidad media va de 34,7 a 65,4 de razonamiento, un factor de 1,9. **Duplicar la capacidad cuesta cinco veces más.** Es el dato que justifica la herramienta: no existe "el mejor modelo", existe el mejor para un presupuesto.

---

## 6. Especificación de la web interactiva

### 6.1 Datos que debe consumir

**Archivo principal**: `data/processed/aa_models_priced_2026-10-19.parquet` (24 filas). Campos relevantes:

- Identidad: `aa_slug`, `aa_name`, `creator_name`, `release_date`, `context_window_tokens`, `is_open_weights`, `is_reasoning`, `parameters_billions` (13/24)
- Precio: `price_in_usd_per_mtok`, `price_out_usd_per_mtok`, `price_cache_hit_usd_per_mtok`, `price_imputed`, `price_imputation_method`
- Rendimiento: `speed_tok_s`, `latency_ttft_s`, `ii_time_per_task_s`, `ii_output_tokens_per_task`
- Tareas: las 9 columnas de la tabla 3.2
- Modalidades: `input_modality_image`, etc.

**Archivo de clusters**: `data/processed/aa_clusters_k4_2026-10-19.parquet` agrega `cluster` (0-3) y `cluster_label`, más `pc1` y `pc2`.

**Figura ya generada**: `outputs/figures/aa_clusters_pc1_pc2.png` — sirve como referencia visual, pero la web debe reimplementarla interactiva.

### 6.2 Gráfico principal

**Dispersión en PC1 × PC2**, un color por cluster, etiqueta con el nombre del modelo en hover (no fija: con 24 puntos se superponen).

- **Eje X**: PC1, capacidad. **Eje Y**: PC2, velocidad de salida.
- **Tamaño del punto**: `context_window_tokens` en escala `log1p`.
- **Color**: cluster, con los cuatro nombres como leyenda.
- **Anotación obligatoria**: los ejes son componentes, no variables. Debe haber un texto que diga qué mide cada uno y que PC2 **no** es tiempo de respuesta.

**Gráfico alternativo, y probablemente el más útil para decidir**: capacidad (una tarea a elección) en X contra costo en Y, con escala logarítmica en el eje de costo. Permite ver la frontera de Pareto sin necesidad de entender un PCA.

### 6.3 Filtros

- Rango de precio de entrada (slider).
- Contexto mínimo (slider). Valores reales presentes en el dataset: 256.000, 500.000, 524.288, 983.616, 1.000.000 y 1.048.576 tokens. Conviene un control por umbral, no un desplegable de valores exactos.
- Latencia máxima (slider, escala logarítmica: 0,78 s a 615 s, que es el rango observado).
- Proveedor (multiselección, 16 opciones).
- Cluster (multiselección, 4 opciones).
- Solo pesos abiertos (checkbox).
- **Cobertura de la tarea elegida** (checkbox "mostrar solo modelos con dato"), que debe estar desactivado por defecto para que el usuario vea los faltantes.

### 6.4 Resaltadores

- **Por tarea**: el usuario elige una de las 9 tareas y se resaltan los 3 mejores modelos en esa columna con un anillo y una etiqueta de ranking. El resto se atenúa.
- **Por proveedor**: al pasar el mouse por la leyenda de proveedores se resaltan sus modelos.
- **Por modelo**: al hacer clic en un punto se fija su ficha con todas las métricas y su tramo.
- **Costo vs capacidad**: un toggle que colorea el punto según si está sobre la frontera de Pareto (ningún otro modelo es mejor y más barato a la vez).

### 6.5 Qué no debe hacer la interfaz

- **No ordenar por costo sin marcar a K2 Horizon**, cuyo precio es imputado y el modelo no se comercializa.
- **No mostrar un promedio ni un índice compuesto** entre las 9 columnas de tarea: son benchmarks de hosts distintos con coberturas distintas.
- **No esconder los modelos sin dato** en `data`, `multimodal` ni `instruction`.

---

## 7. Guía para el texto

**Extensión**: máximo 12 páginas. Presupuesto sugerido: 1 problema, 2 datos, 2 metodología, 4 resultados, 1,5 herramienta, 1,5 límites.

**Tono**: afirmaciones con número al lado. El documento defiende lo que midió y declara lo que no.

**Lo que sí se puede afirmar**:

- El mercado se ordena en un gradiente de capacidad, con cuatro tramos reconocibles.
- Duplicar la capacidad cuesta cinco veces más.
- El tramo de frontera no es lento generando: es lento arrancando.
- Seis de nueve tareas tienen cobertura completa.

**Lo que no se puede afirmar**:

- Que existan cuatro arquetipos de modelo. Son cuatro cortes de un continuo.
- Que estos 24 modelos representen al mercado: 7 son de dos laboratorios.
- Que un modelo sea mejor que otro "en general": depende de la tarea y del presupuesto.
- Que los puntajes sean comparables con los de otro leaderboard.

---

## 8. Notas: caminos que se descartaron

**Clusterizar sobre los ejes agregados de calidad.** Un eje que promedia ranks de benchmarks con coberturas distintas no es la misma medición en dos filas: dos modelos con el mismo valor pueden haber sido medidos con benchmarks diferentes. Se reemplazó por un benchmark por dimensión, el de menor cantidad de nulos.

**Incluir `data` en el modelo.** Costaba 8 modelos y 6 proveedores. Se conserva como etiqueta de reporte para los 16 que la tienen.

**Mantener la latencia en la distancia.** Correlaciona 0,77 con `professional`. Aportaba poco y contaminaba PC1. Se conserva como dato, no como feature.

**Imputar las features faltantes con MICE.** Se probó y se midió: contra la mediana, MICE gana en las features de benchmark pero **pierde 17,6× en latencia** (MAE 2,91 contra 0,165 en unidades escaladas). Con latencias que van de 0,78 s a 615 s, la regresión empuja las predicciones hacia la cola y el método es peor que no imputar. Se descartó como método general.

**Imputar el precio de K2 Horizon con MICE.** Devolvió un precio **negativo** (−0,38 USD/1M). La causa: K2 está fuera del rango de entrenamiento en `log1p(velocidad)` (6,97 contra un máximo de 6,08 en los otros 23). Una regresión lineal ahí extrapola. Se reemplazó por el mínimo observado del dataset, con un flag de procedencia.

**Meter precio y contexto en el espacio de clustering.** Sería lo correcto para una herramienta de decisión, pero contradice la convención del repo, que los excluye de la distancia. Queda pendiente como decisión de producto, no como error.

**UMAP o t-SNE.** Con 24 puntos no hay vecindad que preservar; producen dibujos convincentes de estructuras inexistentes.

**Ward, mezcla gaussiana y HDBSCAN.** Quedaron sin aplicar por decisión de alcance. Las tres atacarían el mismo problema: el tramo C1 concentra 11 de 24 y podría no ser un grupo real sino una zona de densidad baja.

**Aflojar el mínimo de 5 modelos por cluster.** No se aflojó ni se forzó: se reporta que ningún k lo cumple.

---

## 9. Notas: debilidades

**Cobertura.** 24 modelos de 16 proveedores, con 7 de Anthropic y OpenAI y 1 de Google. Un tramo entero (C3) tiene solo dos proveedores. La herramienta va a recomendar Claude con frecuencia anómala, y eso no se corrige con método.

**La escalera depende del outlier.** El IQR de z de `speed_tok_s` bajó a 0,659 en el subconjunto de 16 modelos completos porque K2 Horizon, Nemotron 3.5 y Beam son los tres más veloces y son los que no tienen `analyst_agent`. La forma del gradiente depende de pocos puntos extremos.

**Selección de k.** Ningún k cumple el mínimo de 5 por cluster; el mayor tiene 4. La silueta de 0,459 es aceptable pero no alta, y el tramo C1 es un continuo más que un grupo.

**Sin validación de estabilidad.** Nunca se corrió un bootstrap ni un análisis de remuestreo. **No se sabe si los cuatro tramos sobreviven a cambiar los datos.** Es la verificación más importante que falta y debería hacerse antes de publicar la partición como hallazgo.

**Un solo host.** Todo viene de Artificial Analysis. Los benchmarks no son comparables con los de otros leaderboards, y la fuente re-mide: Claude Opus 5.5 aparece con 615 s de latencia acá y 666 s en el leaderboard de la misma fuente.

**La extracción no está automatizada.** El payload se obtuvo a mano desde el navegador. Reproducir el dataset requiere repetir ese proceso. Sin automatización no hay actualización periódica posible.

**El precio de K2 es una asignación, no una medición.** Y el modelo no se vende por API. Cualquier ranking de costo que lo incluya está comparando un producto inexistente.

**Tres tareas tienen cobertura insuficiente.** `instruction` no tiene un solo dato; `multimodal` 13 de 24; `data` 16 de 24.

**El dataset no respeta la restricción de universo del proyecto**, que pide entre 41 y 100 modelos. Con 24 no se cumple, y el motivo es el límite de la fuente.

---

## 10. Notas: próximos pasos

**En orden de impacto:**

1. **Validación de estabilidad.** Bootstrap de 200 remuestreos con ARI entre corridas. Si los tramos no se sostienen, el artículo debe presentar el gradiente y no la partición. Es barato y protege la única afirmación estructural.

2. **Motor de recomendación.** Tabla tarea → columna → ranking, con filtros de precio, contexto y latencia. Es simultáneamente el backend de la herramienta y la sección de resultados del artículo. No existe todavía en ninguna forma.

3. **Costo ponderado del proyecto.** La fórmula del repo es `0,60 × entrada + 0,20 × caché + 0,20 × salida`. No se aplicó a estos 24. La web debería mostrarlo junto al blended 1:1 que publica la fuente.

4. **Ampliar la cobertura.** Con una API key de Artificial Analysis se pasa de 27 a cientos de modelos. Es la única intervención que ataca el problema de fondo.

5. **Automatizar la extracción** para que el dataset se pueda refrescar sin intervención manual.

6. **Probar HDBSCAN** sobre PC1/PC2: no fuerza a asignar los 24 puntos y dejaría el tramo medio como ruido si es un continuo, que es la hipótesis más probable.

7. **Evaluar un espacio de decisión** con precio y contexto dentro de la distancia. Cambiaría la naturaleza del resultado: pasaría de describir capacidad a describir conveniencia de compra.

---

## Anexo: archivos del proyecto

| Archivo | Contenido |
|---|---|
| `data/raw/aa_payload_2026-10-19.txt` | payload crudo de la fuente, inmutable |
| `data/processed/aa_models_2026-10-19.parquet` | 27 modelos × 82 columnas, sin normalizar |
| `data/processed/aa_tabla_2026-10-19.parquet` | 24 modelos, filtro de 6 o 7 features |
| `data/processed/aa_tabla_zscore_2026-10-19.parquet` | normalización con `log1p` donde corresponde |
| `data/processed/aa_pca_nolat_2026-10-19.parquet` | `pc1` y `pc2` sobre 5 variables |
| `data/processed/aa_clusters_k4_2026-10-19.parquet` | tramos asignados, con `pc1`/`pc2` |
| `data/processed/aa_models_priced_2026-10-19.parquet` | **tabla final para la web**, con precios completos y flags |
| `outputs/figures/aa_clusters_pc1_pc2.png` | dispersión de referencia |

| Script | Etapa |
|---|---|
| `src/aa_dataset.py` | extracción del payload y armado del dataset |
| `src/aa_table.py` | filtro de 6 o 7 features |
| `src/aa_normalize.py` | `log1p` + z-score |
| `src/aa_pca.py` | PCA, dos componentes |
| `src/cluster_aa.py` | KMeans para k = 3..6, con indicadores |
| `src/aa_cluster_k4.py` | k=4 fijo, promedios crudos, nombres y figura |
| `src/impute_k2_price.py` | imputación del precio de K2 y su validación |

Todo con `random_state=42`. El dataset se puede regenerar corriendo los scripts en ese orden.
