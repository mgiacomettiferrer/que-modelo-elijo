"""Pipeline de clustering de modelos LLM.

Un modulo por etapa:
    research  ->  data/raw/models_<fecha>.json
    clean     ->  data/interim/models_clean.parquet
    normalize ->  data/interim/models_scaled.parquet
    report    ->  data/interim/nulls_report_<fecha>.md

El esquema canonico y los roles de cada columna viven en `src.schema`.
"""
