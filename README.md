# ¿Qué modelo elijo para mi agente?

Análisis de 24 modelos de lenguaje de 16 proveedores según capacidad, velocidad y precio, con datos de [Artificial Analysis](https://artificialanalysis.ai/models) al 2026-10-19. Incluye una herramienta web interactiva. El documento técnico está en edición y se publicará más adelante.

- **Herramienta web:** [mauriciogiacometti.com/portfolio/que-modelo-elijo](https://mauriciogiacometti.com/portfolio/que-modelo-elijo/) ([English](https://mauriciogiacometti.com/en/portfolio/que-modelo-elijo/))
- **Especificación de datos y modelado:** [outputs/especificacion-datos-y-modelado.md](outputs/especificacion-datos-y-modelado.md)

## Qué encontramos

- El mercado se ordena en un **gradiente de capacidad**, que acá se corta en cuatro tramos (KMeans, k = 4, sobre los dos primeros componentes principales). Son cortes de un continuo, no cuatro tipos de modelo.
- **Duplicar la capacidad cuesta cinco veces más**: entre tramos, el precio de entrada medio va de 0,48 a 5,00 USD por millón de tokens y el puntaje medio de razonamiento de 34,7 a 65,4.
- **"Rápido" son tres medidas**: el tramo de frontera escribe a 111 t/s pero tarda 304 s en emitir el primer token.
- Seis de nueve tareas tienen datos para los 24 modelos; `instruction` (IFBench) no tiene ninguno.

## Límites que conviene leer antes de citar

- **La partición no está validada**: no se corrió ningún bootstrap ni análisis de estabilidad.
- **No representa al mercado**: 7 de los 24 modelos son de Anthropic y OpenAI, y el tramo de frontera tiene dos proveedores.
- **Un solo host**: los puntajes no son comparables con los de otros leaderboards.
- **K2 Horizon** tiene precio imputado (mínimo del dataset) y no se comercializa.

El detalle está en la sección 9 de la especificación.

## Estructura

```
src/                     scripts del pipeline, uno por etapa
data/interim/            intermedios regenerables (reportes, tablas)
data/processed/          parquet finales; aa_models_priced_2026-10-19.parquet es la tabla de la web
data/web/models.json     datos que consume la web
outputs/figures/         figuras generadas por código
outputs/web/que-modelo-elijo/   la web: estática, se abre con index.html (ES) o en/index.html (EN)
```

## Reproducir

```
pip install -r requirements.txt
python -m src.aa_dataset --payload data/raw/aa_payload_2026-10-19.txt
python -m src.aa_table
python -m src.aa_normalize
python -m src.aa_pca --exclude latency_ttft_s_z --exclude data_z --out data/processed/aa_pca_nolat_2026-10-19.parquet --csv data/interim/aa_pca_nolat_scores_2026-10-19.csv --report data/interim/aa_pca_nolat_report_2026-10-19.md
python -m src.aa_cluster_k4
python -m src.impute_k2_price --apply-min
python -m src.web_export
```

`data/raw/` no está en el repo: contiene el payload descargado de la página de Artificial Analysis y no se redistribuye. La extracción se hizo a mano desde el navegador, así que para reproducir desde cero hay que obtener ese payload de nuevo. Los parquet de `data/processed/` permiten regenerar la web y las figuras sin él.

Todo lo aleatorio usa `random_state=42` y las versiones están pinneadas en `requirements.txt`.

## Autor

Mauricio Giacometti · [mauriciogiacometti.com](https://mauriciogiacometti.com)
