# Normalizacion z-score: tabla de Artificial Analysis

- Entrada: `aa_tabla_2026-10-19.parquet`
- Filas: 24
- Features normalizadas: 7
- Formula: `z = (x - media) / desvio`, desvio poblacional (ddof=0)
- Faltantes: se conservan. Media y desvio se calculan solo con lo observado.

## Diagnostico por feature

| Feature | Transformacion | n | media | desvio | z min | z max | IQR de z | dentro de \|z\|<=1 | fuera de \|z\|>3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `speed_tok_s` | log1p + z | 24 | 4.7665 | 0.7764 | -1.41 | 2.84 | 1.13 | 17 | 0 |
| `latency_ttft_s` | log1p + z | 24 | 2.7134 | 2.0367 | -1.05 | 1.82 | 1.77 | 15 | 0 |
| `reasoning` | z | 24 | 52.3324 | 10.3471 | -2.27 | 1.54 | 1.30 | 17 | 0 |
| `coding` | z | 24 | 55.3723 | 5.6719 | -2.19 | 2.03 | 1.27 | 17 | 0 |
| `agentic` | z | 24 | 29.4823 | 20.2875 | -1.45 | 1.68 | 1.62 | 12 | 0 |
| `professional` | z | 24 | 19.6417 | 6.6435 | -1.84 | 1.71 | 1.25 | 16 | 0 |
| `data` | z | 16 | 44.5312 | 10.3727 | -2.00 | 1.25 | 1.39 | 11 | 0 |

## Efecto del log1p en las features de cola

| Feature | IQR de z sin log1p | IQR de z con log1p | Ganancia |
|---|---:|---:|---:|
| `speed_tok_s` | 0.48 | 1.13 | x2.35 |
| `latency_ttft_s` | 0.73 | 1.77 | x2.43 |

El IQR de z es el rango donde cae la mitad central de los modelos. Si se
duplica o mas, la transformacion devolvio poder de discriminacion que el
extremo se estaba comiendo.


## Que dice el IQR de z

Si el rango intercuartilico de `z` es chico, la mitad central de los modelos
ocupa una banda angosta y el z-score no los separa: el extremo se llevo el
desvio. Un IQR cercano a 1 o mas significa que la escala sigue discriminando.
