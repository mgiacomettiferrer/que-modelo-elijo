# Plantilla de post de LinkedIn

Reemplazar los `<...>`. Objetivo: que alguien que no leyó el artículo se lleve una decisión concreta.

## Restricciones

- Español. Extensión objetivo: 900-1400 caracteres (el feed corta cerca de 1400).
- Máximo 3 emojis, y solo si aportan; nunca uno por bullet.
- Sin hashtags de relleno: 3-5, específicos.
- Cero cifras sin fuente. Toda métrica citada debe existir en `data/processed/`.
- No usar superlativos vacíos ("revolucionario", "game changer") ni cierres de una frase.

## Estructura

```
<hook: 1-2 líneas. El problema concreto, no el tema.>

Ej: "Elegir un LLM hoy es más difícil que usarlo: hay <N> modelos y la mayoría
de las comparaciones te obligan a leer 40 columnas."

<contexto breve: 2-3 líneas. Qué hiciste y con qué datos.>

Agrupé <N> modelos de <fuentes> por <features> y los clustericé. Corte: <fecha>.

<insight: la tabla o la lista. Acá va el valor.>

Los <K> grupos que aparecen:

1. <Etiqueta> — <qué es + 2-3 modelos>
2. <Etiqueta> — <...>
3. <Etiqueta> — <...>

<recomendación accionable por criterio>

Si tu criterio es <X>, andá a <cluster>. Si es <Y>, <cluster>.
<La trampa opcional: el dato contraintuitivo que hace que el post se comparta.>

<CTA suave, no "comentá sí" ni "seguime"> 

El artículo completo, con el método y los datos, está acá: <link>

#LLM #IA #DataScience <#...>
```

## Checklist antes de publicar

- [ ] El hook se entiende sin leer el resto.
- [ ] Se nombra al menos un model concreto por cluster.
- [ ] La fecha de corte y las fuentes aparecen.
- [ ] Cada número del post es rastreable en `data/processed/llm_features.parquet`.
- [ ] Sin señales de escritura IA: contrastes "no X sino Y", tríadas forzadas, "en un mundo donde", cierres de una línea.
- [ ] El link funciona y apunta a `outputs/article/clusters-llm.md`.

## Variante corta (solo para carrusel o primer comentario)

```
<N modelos> agrupados en <K> clusters.
Resumen: <una línea por cluster>.
Método y datos en el artículo <link>.
```
