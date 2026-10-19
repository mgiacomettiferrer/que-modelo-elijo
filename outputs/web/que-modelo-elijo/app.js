/* ¿Qué modelo elijo para mi agente? / Which model should my agent use?
 * Datos: data/models.js (generado por src/web_export.py desde los parquet).
 * Regla de la herramienta: rankear por la columna de la tarea y filtrar.
 * Nunca se combina más de una columna de tarea en un mismo número.
 * Idioma: lo define <html lang>. Compatible con una CSP sin 'unsafe-inline'.
 */
(function () {
  "use strict";

  const EN = (document.documentElement.lang || "es").toLowerCase().startsWith("en");
  const T = (es, en) => (EN ? en : es);
  const LOCALE = EN ? "en-US" : "es-UY";

  const DATA = window.MODELS_DATA;
  if (!DATA || !window.d3) {
    const msg = T(
      "No se pudieron cargar los datos o la librería de gráficos.",
      "The data or the chart library could not be loaded."
    );
    document.querySelectorAll(".chart").forEach((el) => (el.textContent = msg));
    return;
  }

  const MODELS = DATA.modelos;
  const META = DATA.meta;
  const N = META.n_modelos;
  const CLUSTERS = DATA.clusters.map((c) => ({
    ...c,
    label: EN ? c.nombre_en || c.nombre : c.nombre,
    desc: EN ? c.descripcion_en || c.descripcion : c.descripcion,
  }));
  const CL = Object.fromEntries(CLUSTERS.map((c) => [c.id, c]));

  const TASK_LABEL = {
    general: T("General", "General"),
    reasoning: T("Razonamiento", "Reasoning"),
    coding: T("Código", "Coding"),
    agentic: T("Agéntico", "Agentic"),
    professional: T("Documentos profesionales", "Professional documents"),
    long_context: T("Contexto largo", "Long context"),
    data: T("Análisis de datos", "Data analysis"),
    multimodal: T("Multimodal (imágenes)", "Multimodal (images)"),
    instruction: T("Seguir instrucciones", "Instruction following"),
  };
  const TASKS = META.tareas.map((t) => ({ ...t, label: TASK_LABEL[t.id] || t.id }));
  const TASK = Object.fromEntries(TASKS.map((t) => [t.id, t]));

  const SYMBOLS = [d3.symbolCircle, d3.symbolSquare, d3.symbolTriangle, d3.symbolDiamond];
  const SHAPE_NAME = EN ? ["circle", "square", "triangle", "diamond"] : ["círculo", "cuadrado", "triángulo", "rombo"];

  // ---------- formato ----------
  const NODATA = T("sin dato", "no data");
  const nf = (d) => new Intl.NumberFormat(LOCALE, { minimumFractionDigits: d, maximumFractionDigits: d });
  const f0 = nf(0), f1 = nf(1), f2 = nf(2);
  const fmtInt = (v) => (v == null ? NODATA : f0.format(v));
  const fmtScore = (v) => (v == null ? NODATA : f1.format(v));
  const fmtUsd = (v) => {
    if (v == null) return NODATA;
    if (v > 0 && v < 0.1) return new Intl.NumberFormat(LOCALE, { maximumSignificantDigits: 2 }).format(v);
    return f2.format(v);
  };
  const fmtSecN = (v) => (v < 10 ? f2 : v < 100 ? f1 : f0).format(v);
  const fmtSec = (v) => (v == null ? NODATA : fmtSecN(v) + " s");
  const fmtSpeed = (v) => (v == null ? NODATA : f0.format(v) + " t/s");
  const fmtCtx = (v) => (v == null ? NODATA : f0.format(v));
  const yesNo = (v) => (v == null ? NODATA : v ? T("sí", "yes") : "no");
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const k2 = (m) => (m.precio_imputado ? "†" : "");
  const unitOf = (t) => (t.id === "general" ? T("índice de la fuente", "source index") : T("puntaje en %", "score in %"));
  const ord = (r) => (EN ? `#${r}` : `${r}.º`);

  // Costo ponderado (AGENTS.md): 60/20/20 con caché; 80/20 si falta la tarifa de lectura.
  MODELS.forEach((m) => {
    if (m.precio_in == null || m.precio_out == null) {
      m.ponderado = null;
      m.perfil = null;
    } else if (m.precio_cache == null) {
      m.ponderado = 0.8 * m.precio_in + 0.2 * m.precio_out;
      m.perfil = "80/20";
    } else {
      m.ponderado = 0.6 * m.precio_in + 0.2 * m.precio_cache + 0.2 * m.precio_out;
      m.perfil = "60/20/20";
    }
  });
  const COST_EXT = d3.extent(MODELS, (m) => m.ponderado);
  const COST_LABEL = {
    ponderado: T("Costo ponderado estimado (USD / 1M tokens)", "Estimated weighted cost (USD / 1M tokens)"),
    precio_in: T("Precio de entrada (USD / 1M tokens)", "Input price (USD / 1M tokens)"),
    precio_out: T("Precio de salida (USD / 1M tokens)", "Output price (USD / 1M tokens)"),
  };

  // Puesto de cada modelo en cada tarea, sobre los modelos con dato (no sobre los filtrados).
  const RANK = {};
  TASKS.forEach((t) => {
    const withData = MODELS.filter((m) => m[t.id] != null).sort((a, b) => b[t.id] - a[t.id]);
    RANK[t.id] = new Map(withData.map((m, i) => [m.slug, i + 1]));
  });

  // ---------- dominios de filtros ----------
  const ext = (k) => d3.extent(MODELS, (m) => m[k]);
  const [PMIN, PMAX] = ext("precio_in");
  const [LMIN, LMAX] = ext("latencia");
  const CTX_STEPS = Array.from(new Set(MODELS.map((m) => m.contexto).filter((v) => v != null))).sort((a, b) => a - b);
  const PROVIDERS = d3.rollups(MODELS, (v) => v.length, (m) => m.proveedor).sort((a, b) => d3.descending(a[1], b[1]) || d3.ascending(a[0], b[0]));

  const logSlider = (lo, hi) => ({
    toVal: (p) => Math.exp(Math.log(lo) + (Math.log(hi) - Math.log(lo)) * (p / 1000)),
  });
  const PS = logSlider(PMIN, PMAX);
  const LS = logSlider(LMIN, LMAX);

  const DEFAULTS = () => ({
    task: "agentic",
    onlyData: false,
    pMinPos: 0,
    pMaxPos: 1000,
    ctxIdx: 0,
    latPos: 1000,
    clusters: new Set(CLUSTERS.map((c) => c.id)),
    providers: new Set(PROVIDERS.map((p) => p[0])),
    openOnly: false,
  });
  const S = Object.assign(DEFAULTS(), {
    selected: null,
    hoverProvider: null,
    costMetric: "ponderado",
    mapTask: null,
    colorPareto: false,
    paretoK2: false,
    sort: { key: null, dir: 1 },
  });

  // Los extremos del slider son los valores observados exactos, para no dejar afuera al mínimo ni al máximo.
  const priceMin = () => (S.pMinPos <= 0 ? PMIN : PS.toVal(S.pMinPos));
  const priceMax = () => (S.pMaxPos >= 1000 ? PMAX : PS.toVal(S.pMaxPos));
  const latMax = () => (S.latPos >= 1000 ? LMAX : LS.toVal(S.latPos));
  const ctxMin = () => CTX_STEPS[S.ctxIdx];

  function visible() {
    const lo = Math.min(priceMin(), priceMax()), hi = Math.max(priceMin(), priceMax());
    return MODELS.filter(
      (m) =>
        m.precio_in != null && m.precio_in >= lo - 1e-9 && m.precio_in <= hi + 1e-9 &&
        m.contexto != null && m.contexto >= ctxMin() &&
        m.latencia != null && m.latencia <= latMax() + 1e-9 &&
        S.clusters.has(m.cluster) &&
        S.providers.has(m.proveedor) &&
        (!S.openOnly || m.pesos_abiertos) &&
        (!S.onlyData || m[S.task] != null)
    );
  }

  const top3 = (list, task) => (task ? list.filter((m) => m[task] != null).sort((a, b) => b[task] - a[task]).slice(0, 3) : []);

  // ---------- controles ----------
  const $ = (id) => document.getElementById(id);

  function buildControls() {
    $("filters").addEventListener("submit", (e) => e.preventDefault());

    $("meta-line").textContent = T(
      `${N} modelos de ${META.n_proveedores} proveedores, medidos por ${META.fuente}. Datos al ${META.corte}.`,
      `${N} models from ${META.n_proveedores} providers, measured by ${META.fuente}. Data as of ${META.corte}.`
    );

    $("map-task").innerHTML = `<option value="">${T("— ninguna tarea —", "— no task —")}</option>` + TASKS.map(
      (t) => `<option value="${t.id}"${t.cobertura === 0 ? " disabled" : ""}>${esc(t.label)} · ${esc(t.benchmark)}${
        t.cobertura === 0 ? T(" (sin datos)", " (no data)") : t.cobertura < N ? ` (${t.cobertura}/${N})` : ""}</option>`
    ).join("");
    $("map-task").addEventListener("change", (e) => { S.mapTask = e.target.value || null; renderPca(); });
    $("explorer").addEventListener("toggle", (e) => { if (e.target.open) render(); });

    $("task").innerHTML = TASKS.map(
      (t) => `<option value="${t.id}">${esc(t.label)} · ${esc(t.benchmark)} (${t.cobertura}/${N})</option>`
    ).join("");

    $("ctx").max = CTX_STEPS.length - 1;

    $("cluster-list").innerHTML = CLUSTERS.map(
      (c) => `<label class="check"><input type="checkbox" value="${c.id}" checked>
        ${swatch(c.id)} <span>C${c.id} · ${esc(c.label)} <span class="unit">(${c.n})</span></span></label>`
    ).join("");

    $("provider-list").innerHTML = PROVIDERS.map(
      ([p, n]) => `<label class="check" data-provider="${esc(p)}"><input type="checkbox" value="${esc(p)}" checked>
        <span>${esc(p)}</span><span class="n">${n}</span></label>`
    ).join("");

    $("pca-legend").innerHTML =
      CLUSTERS.map((c) => `<span>${swatch(c.id)} C${c.id} · ${esc(c.label)} (n=${c.n})</span>`).join("") +
      `<span>${T(
        `Tamaño del punto: costo ponderado estimado (USD / 1M tokens, 60/20/20), de USD ${fmtUsd(COST_EXT[0])} a ${fmtUsd(COST_EXT[1])}. Más grande, más caro.`,
        `Point size: estimated weighted cost (USD / 1M tokens, 60/20/20), from USD ${fmtUsd(COST_EXT[0])} to ${fmtUsd(COST_EXT[1])}. Bigger means more expensive.`
      )}</span>` +
      `<span>${T("† K2 Horizon: precio imputado, no se comercializa", "† K2 Horizon: imputed price, not sold commercially")}</span>` +
      `<span>${T("Contorno punteado: sin dato en la tarea elegida", "Dashed outline: no data for the selected task")}</span>`;

    $("tramos").innerHTML = CLUSTERS.map((c) => {
      const members = MODELS.filter((m) => m.cluster === c.id).map((m) => esc(m.nombre) + k2(m));
      return `<article class="tramo-card"><h3>${swatch(c.id)} C${c.id} · ${esc(c.label)} — ${c.n} ${T("modelos", "models")}</h3>
        <p>${esc(c.desc)}</p><p class="members">${members.join(", ")}</p></article>`;
    }).join("");

    syncControls();

    $("task").addEventListener("change", (e) => { S.task = e.target.value; render(); });
    $("only-data").addEventListener("change", (e) => { S.onlyData = e.target.checked; render(); });
    $("price-min").addEventListener("input", (e) => {
      S.pMinPos = +e.target.value;
      if (S.pMinPos > S.pMaxPos) { S.pMaxPos = S.pMinPos; $("price-max").value = S.pMaxPos; }
      render();
    });
    $("price-max").addEventListener("input", (e) => {
      S.pMaxPos = +e.target.value;
      if (S.pMaxPos < S.pMinPos) { S.pMinPos = S.pMaxPos; $("price-min").value = S.pMinPos; }
      render();
    });
    $("ctx").addEventListener("input", (e) => { S.ctxIdx = +e.target.value; render(); });
    $("lat").addEventListener("input", (e) => { S.latPos = +e.target.value; render(); });
    $("open-only").addEventListener("change", (e) => { S.openOnly = e.target.checked; render(); });
    $("cluster-list").addEventListener("change", (e) => {
      const id = +e.target.value;
      e.target.checked ? S.clusters.add(id) : S.clusters.delete(id);
      render();
    });
    $("provider-list").addEventListener("change", (e) => {
      const p = e.target.value;
      e.target.checked ? S.providers.add(p) : S.providers.delete(p);
      render();
    });
    // Leyenda de proveedores: hover o foco resalta sus modelos.
    const list = $("provider-list");
    const setHover = (p) => { if (S.hoverProvider !== p) { S.hoverProvider = p; renderCharts(visible()); } };
    list.addEventListener("mouseover", (e) => { const l = e.target.closest("[data-provider]"); if (l) setHover(l.dataset.provider); });
    list.addEventListener("mouseleave", () => setHover(null));
    list.addEventListener("focusin", (e) => { const l = e.target.closest("[data-provider]"); if (l) setHover(l.dataset.provider); });
    list.addEventListener("focusout", () => setHover(null));

    $("prov-all").addEventListener("click", () => { S.providers = new Set(PROVIDERS.map((p) => p[0])); syncControls(); render(); });
    $("prov-none").addEventListener("click", () => { S.providers = new Set(); syncControls(); render(); });
    $("reset").addEventListener("click", resetFilters);

    $("cost-metric").addEventListener("change", (e) => { S.costMetric = e.target.value; render(); });
    $("color-pareto").addEventListener("change", (e) => { S.colorPareto = e.target.checked; render(); });
    $("pareto-k2").addEventListener("change", (e) => { S.paretoK2 = e.target.checked; render(); });

    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && S.selected) { S.selected = null; render(); } });
    document.addEventListener("click", (e) => {
      const b = e.target.closest("[data-reset]");
      if (b) resetFilters();
      const s = e.target.closest("[data-select]");
      if (s) select(s.dataset.select);
    });
  }

  function resetFilters() {
    const keepTask = S.task;
    Object.assign(S, DEFAULTS(), { task: keepTask });
    syncControls();
    render();
  }

  function syncControls() {
    $("task").value = S.task;
    $("only-data").checked = S.onlyData;
    $("price-min").value = S.pMinPos;
    $("price-max").value = S.pMaxPos;
    $("ctx").value = S.ctxIdx;
    $("lat").value = S.latPos;
    $("open-only").checked = S.openOnly;
    $("cluster-list").querySelectorAll("input").forEach((i) => (i.checked = S.clusters.has(+i.value)));
    $("provider-list").querySelectorAll("input").forEach((i) => (i.checked = S.providers.has(i.value)));
  }

  function swatch(cid) {
    const p = d3.symbol(SYMBOLS[cid], 110)();
    return `<svg class="swatch" viewBox="-7 -7 14 14" aria-hidden="true"><path class="sw c${cid}" d="${p}"/></svg>`;
  }

  function select(slug) {
    // Re-render reemplaza el DOM: guardar dónde estaba el foco para devolverlo.
    const a = document.activeElement;
    const box = a && a.closest("[id]");
    const attr = a && ["data-select", "data-slug"].find((k) => a.hasAttribute(k));
    const sig = box && attr ? `#${box.id} [${attr}="${CSS.escape(a.getAttribute(attr))}"]` : null;
    S.selected = S.selected === slug ? null : slug;
    render();
    const back = sig && document.querySelector(sig);
    if (back) back.focus();
  }

  // ---------- render ----------
  function render() {
    const vis = visible();
    const lo = Math.min(priceMin(), priceMax()), hi = Math.max(priceMin(), priceMax());
    $("price-min-out").textContent = "USD " + fmtUsd(lo);
    $("price-max-out").textContent = "USD " + fmtUsd(hi);
    $("ctx-out").textContent = fmtCtx(ctxMin());
    $("lat-out").textContent = fmtSec(latMax());
    $("price-min").setAttribute("aria-valuetext", "USD " + fmtUsd(lo));
    $("price-max").setAttribute("aria-valuetext", "USD " + fmtUsd(hi));
    $("ctx").setAttribute("aria-valuetext", fmtCtx(ctxMin()) + " tokens");
    $("lat").setAttribute("aria-valuetext", fmtSec(latMax()));

    const t = TASK[S.task];
    $("task-hint").textContent =
      t.cobertura === 0
        ? T(`${t.benchmark} no tiene datos para ninguno de los ${N} modelos.`, `${t.benchmark} has no data for any of the ${N} models.`)
        : t.cobertura < N
        ? T(`${t.benchmark}: ${t.cobertura} de ${N} modelos tienen dato. Los otros ${N - t.cobertura} figuran como “sin dato”.`,
            `${t.benchmark}: ${t.cobertura} of ${N} models have data. The other ${N - t.cobertura} are listed as “no data”.`)
        : T(`${t.benchmark}: los ${N} modelos tienen dato.`, `${t.benchmark}: all ${N} models have data.`);

    const nd = vis.filter((m) => m[S.task] == null).length;
    $("count").textContent =
      vis.length === 0
        ? T("Ningún modelo cumple los filtros.", "No model matches the filters.")
        : T(`${vis.length} de ${N} modelos cumplen los filtros`, `${vis.length} of ${N} models match the filters`) +
          (nd ? T(`; ${nd} sin dato en ${t.benchmark}.`, `; ${nd} without data on ${t.benchmark}.`) : ".");

    renderRanking(vis);
    renderFicha();
    renderCharts(vis);
    renderTable(vis);
  }

  function renderCharts(vis) {
    renderPca();
    renderPareto(vis);
  }

  const emptyState = (msg) =>
    `<div class="empty-state"><p>${msg}</p><button type="button" data-reset>${T("Restablecer filtros", "Reset filters")}</button></div>`;
  const NO_MODELS = T("Ningún modelo cumple los filtros. Aflojá alguno o restablecelos.", "No model matches the filters. Loosen one or reset them.");

  function noTaskData(t) {
    return `<div class="empty-state">${T(
      `<p><strong>No hay datos para esta tarea.</strong> ${esc(t.benchmark)} no tiene puntaje para ninguno de los ${N} modelos en ${esc(META.fuente)} al ${META.corte}. No se puede rankear ni completar con otro benchmark: sería otra medición.</p><p>Elegí otra tarea para ver un ranking.</p>`,
      `<p><strong>There is no data for this task.</strong> ${esc(t.benchmark)} has no score for any of the ${N} models on ${esc(META.fuente)} as of ${META.corte}. It cannot be ranked or filled in with another benchmark: that would be a different measurement.</p><p>Pick another task to see a ranking.</p>`
    )}</div>`;
  }

  function renderRanking(vis) {
    const t = TASK[S.task];
    $("rank-title").textContent = T(`Ranking en ${t.label.toLowerCase()}`, `Ranking: ${t.label.toLowerCase()}`);
    const box = $("ranking");
    if (t.cobertura === 0) { box.innerHTML = noTaskData(t); return; }
    if (!vis.length) { box.innerHTML = emptyState(NO_MODELS); return; }

    const max = d3.max(MODELS, (m) => m[t.id]);
    const withData = vis.filter((m) => m[t.id] != null).sort((a, b) => b[t.id] - a[t.id]);
    const without = vis.filter((m) => m[t.id] == null).sort((a, b) => d3.ascending(a.nombre, b.nombre));
    const partial = t.cobertura < N
      ? `<p class="alert">${T(
          `Solo ${t.cobertura} de ${N} modelos tienen dato en ${esc(t.benchmark)}. Los que no lo tienen van al final como “sin dato”: no significa puntaje bajo, significa que no fue medido.`,
          `Only ${t.cobertura} of ${N} models have data on ${esc(t.benchmark)}. The rest go last as “no data”: that does not mean a low score, it means it was not measured.`
        )}</p>`
      : "";
    const row = (m, i) => {
      const v = m[t.id];
      const pct = v == null ? 0 : (100 * v) / max;
      return `<li class="${i < 3 && v != null ? "top" : ""} ${v == null ? "nodata" : ""}">
        <span class="pos">${v == null ? "—" : i + 1}</span>
        <span class="who">${swatch(m.cluster)} <button type="button" data-select="${esc(m.slug)}" aria-pressed="${S.selected === m.slug}">${esc(m.nombre)}${k2(m)}</button>
          ${m.precio_imputado ? `<span class="badge">${T("precio imputado · no se comercializa", "imputed price · not sold")}</span>` : ""}
          <small>${esc(m.proveedor)} · C${m.cluster} ${esc(CL[m.cluster].label)} · ${T("costo pond.", "weighted cost")} USD ${fmtUsd(m.ponderado)}</small>
          ${v == null ? "" : `<span class="bar" aria-hidden="true"><span data-w="${pct.toFixed(1)}"></span></span>`}</span>
        <span class="val">${fmtScore(v)}</span></li>`;
    };
    box.innerHTML =
      `<p class="rank-head">${esc(t.benchmark)} (${T("columna", "column")} <code>${esc(t.columna)}</code>), ${unitOf(t)}. ${T(
        "Mayor es mejor. Puestos dentro de los filtros.", "Higher is better. Positions within the filters.")}</p>` +
      partial +
      (withData.length ? "" : `<p class="alert">${T(`Ninguno de los modelos filtrados tiene dato en ${esc(t.benchmark)}.`, `None of the filtered models has data on ${esc(t.benchmark)}.`)}</p>`) +
      `<ol class="rank-list">${withData.map(row).join("")}${without.map((m) => row(m, -1)).join("")}</ol>`;
    // Ancho de las barras por CSSOM: la CSP del sitio bloquea los atributos style="".
    box.querySelectorAll("[data-w]").forEach((el) => (el.style.width = el.dataset.w + "%"));
  }

  function renderFicha() {
    const html = fichaHtml(MODELS.find((x) => x.slug === S.selected));
    document.querySelectorAll(".ficha-slot").forEach((box) => (box.innerHTML = html));
  }

  function fichaHtml(m) {
    if (!m) {
      return `<p class="empty">${T(
        "Hacé clic en un punto del mapa, en el ranking o en una fila de la tabla para ver su ficha. <kbd>Esc</kbd> la cierra.",
        "Click a point on the map, a ranking entry or a table row to see its profile. <kbd>Esc</kbd> closes it."
      )}</p>`;
    }
    const c = CL[m.cluster];
    const nd = `<span class="nd">${NODATA}</span>`;
    const taskRows = TASKS.map((t) => {
      const v = m[t.id];
      const r = RANK[t.id].get(m.slug);
      return `<dt>${esc(t.label)} <span class="unit">${esc(t.benchmark)}</span></dt><dd>${
        v == null ? nd : `${fmtScore(v)} · ${ord(r)} ${T("de", "of")} ${t.cobertura}`
      }</dd>`;
    }).join("");
    return `
      <p class="name">${esc(m.nombre)}${k2(m)}</p>
      <p class="unit">${esc(m.nombre_aa)} · ${esc(m.proveedor)}</p>
      <p class="tramo">${swatch(m.cluster)} ${T("Tramo", "Tier")} C${m.cluster} · ${esc(c.label)}</p>
      ${m.precio_imputado ? `<p class="alert">${T(
        `Precio imputado (${esc(m.precio_metodo_imputacion)}). La fuente publica 0,00 y el modelo no se comercializa por API.`,
        "Imputed price (minimum observed in the dataset). The source publishes 0.00 and the model is not sold via API."
      )}</p>` : ""}
      <h4>${T("Tiempos", "Timing")}</h4>
      <dl>
        <dt>${T("Caudal de salida", "Output throughput")}</dt><dd>${fmtSpeed(m.velocidad)}</dd>
        <dt>${T("Latencia al primer token", "Latency to first token")}</dt><dd>${fmtSec(m.latencia)}</dd>
        <dt>${T("Tiempo por tarea", "Time per task")}</dt><dd>${fmtSec(m.tiempo_por_tarea)}</dd>
        <dt>${T("Tokens por tarea", "Tokens per task")}</dt><dd>${fmtInt(m.tokens_por_tarea)}</dd>
      </dl>
      <h4>${T("Precios", "Prices")} <span class="unit">USD / 1M tokens</span></h4>
      <dl>
        <dt>${T("Entrada", "Input")}</dt><dd>${fmtUsd(m.precio_in)}</dd>
        <dt>${T("Salida", "Output")}</dt><dd>${fmtUsd(m.precio_out)}</dd>
        <dt>${T("Lectura de caché", "Cache read")}</dt><dd>${fmtUsd(m.precio_cache)}</dd>
        <dt>${COST_LABEL.ponderado}</dt><dd>${fmtUsd(m.ponderado)} <span class="unit">${m.perfil || ""}</span></dd>
      </dl>
      <h4>${T("Capacidad", "Capabilities")}</h4>
      <dl>
        <dt>${T("Contexto", "Context")}</dt><dd>${fmtCtx(m.contexto)} tokens</dd>
        <dt>${T("Pesos abiertos", "Open weights")}</dt><dd>${yesNo(m.pesos_abiertos)}</dd>
        <dt>${T("Razonamiento", "Reasoning")}</dt><dd>${yesNo(m.es_razonamiento)}</dd>
        <dt>${T("Lanzamiento", "Release")}</dt><dd>${m.fecha_lanzamiento ? esc(m.fecha_lanzamiento) : nd}</dd>
      </dl>
      <h4>${T("Tareas", "Tasks")} <span class="unit">${T("puntaje y puesto entre los modelos con dato", "score and position among models with data")}</span></h4>
      <dl>${taskRows}</dl>
      <p class="foot">${T(
        `Fuente: ${esc(META.fuente)}, corte ${META.corte}. Cada tarea es un benchmark distinto; no se promedian.`,
        `Source: ${esc(META.fuente)}, cutoff ${META.corte}. Each task is a different benchmark; they are not averaged.`
      )}</p>`;
  }

  // ---------- tooltip ----------
  const tip = $("tooltip");
  function showTip(m, x, y, task) {
    const t = task && TASK[task];
    tip.innerHTML = `<strong>${esc(m.nombre)}${k2(m)}</strong>${esc(m.proveedor)} · C${m.cluster} ${esc(CL[m.cluster].label)}<br>
      ${t ? `${esc(t.label)}: ${m[t.id] == null ? `<em>${NODATA}</em>` : fmtScore(m[t.id])}<br>` : ""}
      ${T("Costo pond.", "Weighted cost")}: USD ${fmtUsd(m.ponderado)} · ${T("Caudal", "Throughput")} ${fmtSpeed(m.velocidad)} · ${T("Latencia", "Latency")} ${fmtSec(m.latencia)}
      ${m.precio_imputado ? `<br><span class="warn">${T("Precio imputado: no se comercializa.", "Imputed price: not sold commercially.")}</span>` : ""}`;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    const left = Math.min(x + 14, window.innerWidth - r.width - 8);
    const top = y + r.height + 20 > window.innerHeight ? y - r.height - 12 : y + 14;
    tip.style.left = Math.max(8, left) + "px";
    tip.style.top = Math.max(8, top) + "px";
  }
  const hideTip = () => (tip.hidden = true);

  function bindPoints(sel, task) {
    sel
      .attr("tabindex", 0)
      .attr("data-slug", (m) => m.slug)
      .attr("role", "button")
      .attr("aria-label", (m) => {
        const t = task && TASK[task];
        return `${m.nombre}, ${m.proveedor}, ${T("tramo", "tier")} C${m.cluster} ${CL[m.cluster].label}` +
          (t ? `, ${t.label} ${fmtScore(m[t.id])}` : "") +
          (m.precio_imputado ? T(", precio imputado, no se comercializa", ", imputed price, not sold commercially") : "");
      })
      .attr("aria-pressed", (m) => S.selected === m.slug)
      .on("mouseenter mousemove", (e, m) => showTip(m, e.clientX, e.clientY, task))
      .on("mouseleave", hideTip)
      .on("focus", function (e, m) { const r = this.getBoundingClientRect(); showTip(m, r.right, r.top, task); })
      .on("blur", hideTip)
      .on("click", (e, m) => { e.stopPropagation(); select(m.slug); })
      .on("keydown", (e, m) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(m.slug); } });
  }

  function emphasis(vis, task) {
    const tops = top3(vis, task);
    const topSet = new Map(tops.map((m, i) => [m.slug, i + 1]));
    const hasTask = tops.length > 0;
    const dim = (m) => {
      if (S.hoverProvider) return m.proveedor !== S.hoverProvider;
      if (hasTask) return !topSet.has(m.slug) && S.selected !== m.slug;
      return false;
    };
    return { tops, topSet, dim };
  }

  // Mapa: el área del punto es el costo ponderado con log1p (convención del repo). Más grande, más caro.
  const sizeScale = d3.scaleLinear()
    .domain(d3.extent(MODELS, (m) => Math.log1p(m.ponderado)))
    .range([45, 520]);
  const mapArea = (m) => (m.ponderado == null ? 45 : sizeScale(Math.log1p(m.ponderado)));
  // En el gráfico de costo el costo ya está en el eje Y: tamaño fijo.
  const fixedArea = () => 120;
  const symbolPath = (m) => d3.symbol(SYMBOLS[m.cluster], mapArea(m))();
  const fixedPath = (m) => d3.symbol(SYMBOLS[m.cluster], fixedArea(m))();

  function frame(el, h) {
    const w = Math.max(300, el.clientWidth || 600);
    el.innerHTML = "";
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("width", w).attr("height", h)
      .attr("role", "group");
    return { svg, w, h };
  }

  function setAlt(svg, id, title, desc) {
    svg.attr("aria-labelledby", `${id}-t ${id}-d`);
    svg.append("title").attr("id", `${id}-t`).text(title);
    svg.append("desc").attr("id", `${id}-d`).text(desc);
  }

  // ---------- PC1 × PC2 ----------
  const PCX = d3.extent(MODELS, (m) => m.pc1);
  const PCY = d3.extent(MODELS, (m) => m.pc2);

  // El mapa es el nivel 2: siempre muestra los 24 modelos; los filtros del explorador no lo tocan.
  function renderPca() {
    const vis = MODELS;
    const el = $("pca");
    const narrow = el.clientWidth < 520;
    const { svg, w, h } = frame(el, narrow ? 440 : 560);
    const M = { t: 16, r: 18, b: 58, l: narrow ? 46 : 58 };
    const x = d3.scaleLinear().domain([PCX[0] - 0.5, PCX[1] + 0.6]).range([M.l, w - M.r]);
    const y = d3.scaleLinear().domain([PCY[0] - 0.3, PCY[1] + 0.3]).range([h - M.b, M.t]);
    const { tops, topSet, dim } = emphasis(vis, S.mapTask);
    const t = S.mapTask ? TASK[S.mapTask] : null;

    setAlt(svg, "pca-alt", T("Mapa de tramos en PC1 por PC2", "Tier map on PC1 by PC2"),
      T(`Dispersión de ${vis.length} modelos. Eje X: PC1, capacidad. Eje Y: PC2, caudal de salida en tokens por segundo, no tiempo de respuesta. Tamaño: costo ponderado. `,
        `Scatter of ${vis.length} models. X axis: PC1, capability. Y axis: PC2, output throughput in tokens per second, not response time. Size: weighted cost. `) +
      CLUSTERS.map((c) => T(`Tramo C${c.id} ${c.label}: ${SHAPE_NAME[c.id]}.`, `Tier C${c.id} ${c.label}: ${SHAPE_NAME[c.id]}.`)).join(" ") +
      (tops.length ? T(` Mejores en ${t.label}: `, ` Best on ${t.label}: `) + tops.map((m, i) => `${i + 1}. ${m.nombre}`).join(", ") + "." : "") +
      T(" La tabla de métricas más abajo tiene los mismos datos.", " The metrics table below has the same data."));

    svg.append("g").attr("class", "grid").attr("transform", `translate(0,${h - M.b})`)
      .call(d3.axisBottom(x).ticks(narrow ? 5 : 8).tickSize(-(h - M.b - M.t)).tickFormat(""));
    svg.append("g").attr("class", "grid").attr("transform", `translate(${M.l},0)`)
      .call(d3.axisLeft(y).ticks(6).tickSize(-(w - M.l - M.r)).tickFormat(""));
    svg.append("line").attr("class", "zero").attr("x1", x(0)).attr("x2", x(0)).attr("y1", M.t).attr("y2", h - M.b);
    svg.append("line").attr("class", "zero").attr("x1", M.l).attr("x2", w - M.r).attr("y1", y(0)).attr("y2", y(0));
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${h - M.b})`).call(d3.axisBottom(x).ticks(narrow ? 5 : 8));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${M.l},0)`).call(d3.axisLeft(y).ticks(6));
    svg.append("text").attr("class", "axis-label").attr("x", (M.l + w - M.r) / 2).attr("y", h - 24).attr("text-anchor", "middle")
      .text(T("PC1 · capacidad →  (componente, no variable)", "PC1 · capability →  (component, not a variable)"));
    svg.append("text").attr("class", "axis-note").attr("x", (M.l + w - M.r) / 2).attr("y", h - 8).attr("text-anchor", "middle")
      .text(T("PC2 (vertical) = caudal de salida en t/s. No es tiempo de respuesta.", "PC2 (vertical) = output throughput in t/s. Not response time."));
    svg.append("text").attr("class", "axis-label").attr("transform", `translate(14,${(M.t + h - M.b) / 2}) rotate(-90)`)
      .attr("text-anchor", "middle").text(narrow
        ? T("PC2 · caudal de salida ↑", "PC2 · output throughput ↑")
        : T("PC2 · caudal de salida (no latencia) ↑", "PC2 · output throughput (not latency) ↑"));

    // Nombre de cada tramo sobre su grupo, para leer el mapa sin pasar el mouse.
    const obstacles = [];
    CLUSTERS.forEach((c) => {
      const ms = MODELS.filter((m) => m.cluster === c.id);
      const text = narrow ? `C${c.id}` : `C${c.id} · ${c.label}`;
      const cw = textWidth(text, 13, 700);
      const cx = Math.min(w - M.r - cw / 2, Math.max(M.l + cw / 2, x(d3.mean(ms, (m) => m.pc1))));
      const cy = Math.max(M.t + 12, y(d3.max(ms, (m) => m.pc2)) - 26);
      svg.append("text").attr("class", `cluster-label t${c.id}`).attr("text-anchor", "middle")
        .attr("x", cx).attr("y", cy).text(text);
      obstacles.push({ x0: cx - cw / 2, x1: cx + cw / 2, y0: cy - 12, y1: cy + 3 });
    });

    const g = svg.append("g");
    // Los más caros (más grandes) se dibujan primero para no tapar a los chicos.
    const ordered = vis.slice().sort((a, b) => mapArea(b) - mapArea(a));
    const pts = g.selectAll("path.pt").data(ordered, (m) => m.slug).join("path")
      .attr("class", (m) => `pt c${m.cluster}${t && m[t.id] == null ? " nodata" : ""}${m.precio_imputado ? " imputed" : ""}${S.selected === m.slug ? " selected" : ""}${dim(m) ? " dim" : ""}`)
      .attr("d", symbolPath)
      .attr("transform", (m) => `translate(${x(m.pc1)},${y(m.pc2)})`);
    bindPoints(pts, S.mapTask);

    drawTopMarks(g, tops, topSet, (m) => [x(m.pc1), y(m.pc2)], w, mapArea, false);
    drawPointLabels(g, ordered, (m) => [x(m.pc1), y(m.pc2)], mapArea, obstacles,
      { x0: M.l, x1: w - M.r, y0: M.t, y1: h - M.b }, topSet, dim, narrow ? 10 : 11.5);
  }

  // Ancho real del texto con la fuente de la página, para ubicar etiquetas sin que se pisen.
  const measureCtx = document.createElement("canvas").getContext("2d");
  const FONT = getComputedStyle(document.body).fontFamily || "sans-serif";
  function textWidth(text, size, weight) {
    measureCtx.font = `${weight || 400} ${size}px ${FONT}`;
    return measureCtx.measureText(text).width;
  }

  // Etiqueta fija para cada punto. Colocación voraz: prueba ocho posiciones alrededor del
  // punto y se queda con la que menos pisa otras etiquetas, puntos o rótulos de tramo.
  function drawPointLabels(g, models, pos, area, obstacles, bounds, topSet, dim, size) {
    const boxes = obstacles.slice();
    const pts = models.map((m) => {
      const [px, py] = pos(m);
      return { m, px, py, r: Math.sqrt(area(m) / Math.PI) };
    });
    pts.forEach((p) => boxes.push({ x0: p.px - p.r, x1: p.px + p.r, y0: p.py - p.r, y1: p.py + p.r, own: p.m.slug }));
    const overlap = (a, b) => Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0)) * Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));
    const lh = size + 2;
    pts.slice().sort((a, b) => a.py - b.py).forEach((p) => {
      const rank = topSet.get(p.m.slug);
      const text = (rank && !S.hoverProvider ? `${rank}. ` : "") + p.m.nombre + k2(p.m);
      const tw = textWidth(text, size, rank ? 700 : 500);
      const gap = p.r + 4;
      const cands = [
        [gap, lh / 3, "start"], [-gap, lh / 3, "end"],
        [0, -gap - 2, "middle"], [0, gap + lh - 2, "middle"],
        [gap * 0.7, -gap * 0.7 - 2, "start"], [-gap * 0.7, -gap * 0.7 - 2, "end"],
        [gap * 0.7, gap * 0.7 + lh - 4, "start"], [-gap * 0.7, gap * 0.7 + lh - 4, "end"],
      ];
      let best = null;
      cands.forEach(([dx, dy, anchor]) => {
        const lx = p.px + dx, ly = p.py + dy;
        const x0 = anchor === "start" ? lx : anchor === "end" ? lx - tw : lx - tw / 2;
        const box = { x0, x1: x0 + tw, y0: ly - size, y1: ly + 3 };
        let cost = 0;
        if (box.x0 < bounds.x0 || box.x1 > bounds.x1 || box.y0 < bounds.y0 || box.y1 > bounds.y1) cost += 1e6;
        boxes.forEach((b) => { if (b.own !== p.m.slug) cost += overlap(box, b); });
        if (!best || cost < best.cost) best = { cost, lx, ly, anchor, box };
      });
      boxes.push(best.box);
      g.append("text")
        .attr("class", `pt-label${rank && !S.hoverProvider ? " top" : ""}${dim(p.m) ? " dim" : ""}${S.selected === p.m.slug ? " sel" : ""}`)
        .attr("x", best.lx).attr("y", best.ly).attr("text-anchor", best.anchor)
        .style("font-size", size + "px").text(text);
    });
  }

  function drawTopMarks(g, tops, topSet, pos, w, area, withLabels = true) {
    if (S.hoverProvider) return;
    tops.forEach((m) => {
      const [px, py] = pos(m);
      const r = Math.sqrt(area(m) / Math.PI) + 6;
      g.append("circle").attr("class", "ring").attr("cx", px).attr("cy", py).attr("r", r);
      if (!withLabels) return;
      const right = px < w - 170;
      g.append("text").attr("class", "rank-label").attr("x", px + (right ? r + 4 : -r - 4)).attr("y", py + 4)
        .attr("text-anchor", right ? "start" : "end").text(`${topSet.get(m.slug)}. ${m.nombre}${k2(m)}`);
    });
  }

  function drawSelectedLabel(g, vis, topSet, pos, w) {
    const m = vis.find((d) => d.slug === S.selected);
    if (!m || (topSet.has(m.slug) && !S.hoverProvider)) return;
    const [px, py] = pos(m);
    const right = px < w - 170;
    g.append("text").attr("class", "rank-label").attr("x", px + (right ? 14 : -14)).attr("y", py - 10)
      .attr("text-anchor", right ? "start" : "end").text(m.nombre + k2(m));
  }

  // ---------- costo vs capacidad ----------
  function pareto(points, key) {
    // Orden por costo ascendente; ante empate de costo, primero el de mayor puntaje.
    const sorted = points.slice().sort((a, b) => a[key] - b[key] || b[S.task] - a[S.task]);
    const front = [];
    let best = -Infinity;
    sorted.forEach((m) => { if (m[S.task] > best) { front.push(m); best = m[S.task]; } });
    return front;
  }

  function renderPareto(vis) {
    const el = $("pareto");
    const t = TASK[S.task];
    const key = S.costMetric;
    $("pareto-foot").textContent =
      (key === "ponderado"
        ? T(`Costo ponderado estimado (USD / 1M tokens) = 0,60 × entrada + 0,20 × lectura de caché + 0,20 × salida (pesos 60/20/20). Los ${N} modelos tienen tarifa de lectura de caché; la de K2 Horizon es imputada. Los pesos representan proporciones de tokens consumidos, no el costo real por tarea: el resultado no equivale al costo por tarea. `,
            `Estimated weighted cost (USD / 1M tokens) = 0.60 × input + 0.20 × cache read + 0.20 × output (weights 60/20/20). All ${N} models have a cache-read rate; K2 Horizon's is imputed. The weights are shares of tokens consumed, not the real cost per task: the result is not the cost per task. `)
        : "") +
      T(`Precios: ${META.fuente}, corte ${META.corte}. `, `Prices: ${META.fuente}, cutoff ${META.corte}. `) +
      (S.paretoK2
        ? T("La frontera incluye a K2 Horizon, cuyo precio es imputado.", "The frontier includes K2 Horizon, whose price is imputed.")
        : T("La frontera se calcula sin K2 Horizon (precio imputado, no se comercializa); el punto se muestra igual, marcado con †.",
            "The frontier is computed without K2 Horizon (imputed price, not sold); the point is still shown, marked with †."));

    if (t.cobertura === 0) { el.innerHTML = noTaskData(t); return; }
    if (!vis.length) { el.innerHTML = emptyState(NO_MODELS); return; }

    const narrow = el.clientWidth < 520;
    const { svg, w, h } = frame(el, narrow ? 380 : 440);
    const withData = vis.filter((m) => m[t.id] != null && m[key] != null);
    const without = vis.filter((m) => m[t.id] == null && m[key] != null);
    const band = without.length ? (narrow ? 54 : 70) : 0;
    const M = { t: 16, r: 18, b: 48, l: narrow ? 52 : 62 };
    const xr = d3.extent(MODELS, (m) => m[t.id]);
    const pad = (xr[1] - xr[0]) * 0.06 || 1;
    const x = d3.scaleLinear().domain([xr[0] - pad, xr[1] + pad]).range([M.l + band, w - M.r]);
    const yr = d3.extent(MODELS, (m) => m[key]);
    const y = d3.scaleLog().domain([yr[0] / 1.5, yr[1] * 1.5]).range([h - M.b, M.t]);
    const front = pareto(withData.filter((m) => S.paretoK2 || !m.precio_imputado), key);
    const frontSet = new Set(front.map((m) => m.slug));
    const { tops, topSet, dim } = emphasis(vis, S.task);

    setAlt(svg, "pareto-alt", T(`Costo contra puntaje en ${t.label}`, `Cost versus score on ${t.label}`),
      T(`Dispersión de ${withData.length} modelos con dato en ${t.benchmark}. Eje X: puntaje. Eje Y: ${COST_LABEL[key]}, escala logarítmica. `,
        `Scatter of ${withData.length} models with data on ${t.benchmark}. X axis: score. Y axis: ${COST_LABEL[key]}, log scale. `) +
      (without.length ? T(`${without.length} modelos sin dato se muestran en una franja aparte a la izquierda. `, `${without.length} models without data are shown in a separate band on the left. `) : "") +
      (front.length
        ? T("Frontera de Pareto, de más barato a más caro: ", "Pareto frontier, from cheapest to most expensive: ") + front.map((m) => m.nombre).join(", ") + "."
        : T("Sin frontera: no hay modelos con dato.", "No frontier: no models with data.")));

    svg.append("g").attr("class", "grid").attr("transform", `translate(0,${h - M.b})`)
      .call(d3.axisBottom(x).ticks(narrow ? 4 : 7).tickSize(-(h - M.b - M.t)).tickFormat(""));
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${h - M.b})`).call(d3.axisBottom(x).ticks(narrow ? 4 : 7));
    const yTicks = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100].filter((v) => v >= y.domain()[0] && v <= y.domain()[1]);
    svg.append("g").attr("class", "grid").attr("transform", `translate(${M.l},0)`)
      .call(d3.axisLeft(y).tickValues(yTicks).tickSize(-(w - M.l - M.r)).tickFormat(""));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${M.l},0)`)
      .call(d3.axisLeft(y).tickValues(yTicks).tickFormat((v) => fmtUsd(v)));
    svg.append("text").attr("class", "axis-label").attr("x", (M.l + band + w - M.r) / 2).attr("y", h - 10).attr("text-anchor", "middle")
      .text(`${t.label} · ${t.benchmark} (${t.id === "general" ? T("índice", "index") : "%"}) →`);
    svg.append("text").attr("class", "axis-label").attr("transform", `translate(14,${(M.t + h - M.b) / 2}) rotate(-90)`)
      .attr("text-anchor", "middle").text(narrow ? "USD / 1M tokens (log)" : COST_LABEL[key].replace(" (USD / 1M tokens)", "") + " · USD / 1M (log)");

    if (band) {
      svg.append("rect").attr("class", "nodata-band").attr("x", M.l + 2).attr("y", M.t).attr("width", band - 10).attr("height", h - M.b - M.t);
      svg.append("text").attr("class", "nodata-label").attr("x", M.l + band / 2 - 4).attr("y", h - M.b + 16).attr("text-anchor", "middle").text(NODATA);
    }

    const g = svg.append("g");
    if (front.length > 1) {
      g.append("path").attr("class", "frontier")
        .attr("d", d3.line().x((m) => x(m[t.id])).y((m) => y(m[key]))(front));
    }
    const pos = (m, i) => m[t.id] == null
      ? [M.l + band / 2 - 4 + ((i % 3) - 1) * (band / 5), y(m[key])]
      : [x(m[t.id]), y(m[key])];
    const all = withData.concat(without);
    const posMap = new Map(all.map((m) => [m.slug, pos(m, without.indexOf(m))]));

    const pts = g.selectAll("path.pt").data(all, (m) => m.slug).join("path")
      .attr("class", (m) => {
        const base = S.colorPareto ? (frontSet.has(m.slug) ? "front-on" : "front-off") : `c${m.cluster}`;
        return `pt ${base}${m[t.id] == null ? " nodata" : ""}${m.precio_imputado ? " imputed" : ""}${S.selected === m.slug ? " selected" : ""}${dim(m) ? " dim" : ""}`;
      })
      .attr("d", fixedPath)
      .attr("transform", (m) => `translate(${posMap.get(m.slug)[0]},${posMap.get(m.slug)[1]})`);
    bindPoints(pts, S.task);

    drawTopMarks(g, tops, topSet, (m) => posMap.get(m.slug), w, fixedArea);
    drawSelectedLabel(g, all, topSet, (m) => posMap.get(m.slug), w);

    const kk = all.find((m) => m.precio_imputado);
    if (kk && !topSet.has(kk.slug) && S.selected !== kk.slug) {
      const [px, py] = posMap.get(kk.slug);
      const right = px < w - 220;
      g.append("text").attr("class", "k2-note").attr("x", px + (right ? 12 : -12)).attr("y", py + 16)
        .attr("text-anchor", right ? "start" : "end").text(T("† K2 Horizon: precio imputado, no se vende", "† K2 Horizon: imputed price, not sold"));
    }
  }

  // ---------- tabla ----------
  const COLS = [
    { key: "nombre", label: T("Modelo", "Model"), txt: true },
    { key: "proveedor", label: T("Proveedor", "Provider"), txt: true },
    { key: "cluster", label: T("Tramo", "Tier"), fmt: (v) => `C${v} ${CL[v].label}`, txt: true },
    { key: "precio_in", label: T("Entrada", "Input"), sub: "USD / 1M", fmt: fmtUsd, cost: true },
    { key: "precio_out", label: T("Salida", "Output"), sub: "USD / 1M", fmt: fmtUsd, cost: true },
    { key: "precio_cache", label: T("Lectura caché", "Cache read"), sub: "USD / 1M", fmt: fmtUsd, cost: true },
    { key: "ponderado", label: T("Costo ponderado estimado", "Estimated weighted cost"), sub: "USD / 1M · 60/20/20", fmt: fmtUsd, cost: true },
    { key: "contexto", label: T("Contexto", "Context"), sub: "tokens", fmt: fmtCtx },
    { key: "velocidad", label: T("Caudal", "Throughput"), sub: "t/s", fmt: (v) => (v == null ? NODATA : f0.format(v)) },
    { key: "latencia", label: T("Latencia 1.er token", "Latency 1st token"), sub: "s", fmt: (v) => (v == null ? NODATA : fmtSecN(v)) },
    { key: "tiempo_por_tarea", label: T("Tiempo por tarea", "Time per task"), sub: "s", fmt: (v) => (v == null ? NODATA : f0.format(v)) },
    { key: "tokens_por_tarea", label: T("Tokens por tarea", "Tokens per task"), fmt: fmtInt },
    { key: "pesos_abiertos", label: T("Pesos abiertos", "Open weights"), fmt: yesNo, txt: true },
    ...TASKS.map((t) => ({ key: t.id, label: t.label, sub: `${t.benchmark} · ${t.cobertura}/${N}`, fmt: fmtScore })),
    { key: "procedencia", label: T("Procedencia", "Provenance"), txt: true, nosort: true },
  ];

  function renderTable(vis) {
    const table = $("table");
    const { key, dir } = S.sort;
    const head = `<thead><tr>${COLS.map((c) => {
      const aria = key === c.key ? (dir > 0 ? "ascending" : "descending") : "none";
      const arrow = key === c.key ? (dir > 0 ? " ▲" : " ▼") : "";
      const inner = `${esc(c.label)}${arrow}${c.sub ? `<small>${esc(c.sub)}</small>` : ""}`;
      return `<th scope="col" class="${c.txt ? "txt" : ""}" ${c.nosort ? "" : `aria-sort="${aria}"`}>${
        c.nosort ? inner : `<button type="button" data-sort="${c.key}">${inner}</button>`
      }</th>`;
    }).join("")}</tr></thead>`;

    const rows = vis.slice();
    if (key) {
      const col = COLS.find((c) => c.key === key);
      rows.sort((a, b) => {
        const va = a[key], vb = b[key];
        if (va == null && vb == null) return d3.ascending(a.nombre, b.nombre);
        if (va == null) return 1; // sin dato siempre al final
        if (vb == null) return -1;
        const cmp = col.txt ? d3.ascending(String(col.fmt ? col.fmt(va) : va), String(col.fmt ? col.fmt(vb) : vb)) : va - vb;
        return cmp * dir || d3.ascending(a.nombre, b.nombre);
      });
    } else {
      rows.sort((a, b) => a.cluster - b.cluster || d3.ascending(a.nombre, b.nombre));
    }

    const warn = $("sort-warning");
    const sortCol = COLS.find((c) => c.key === key);
    if (sortCol && sortCol.cost && rows.some((m) => m.precio_imputado)) {
      warn.hidden = false;
      warn.textContent = T(
        "Ordenado por costo: K2 Horizon (†) tiene precio imputado con el mínimo del dataset y no se comercializa. Si encabeza la lista, no es una opción contratable.",
        "Sorted by cost: K2 Horizon (†) has a price imputed with the dataset minimum and is not sold. If it tops the list, it is not an option you can buy."
      );
    } else {
      warn.hidden = true;
    }

    const body = rows.length
      ? rows.map((m) => `<tr tabindex="0" data-slug="${esc(m.slug)}" class="${S.selected === m.slug ? "sel" : ""}" aria-selected="${S.selected === m.slug}">${COLS.map((c) => {
          if (c.key === "procedencia") {
            return `<td class="prov">${esc(META.fuente)}, ${META.corte}${m.precio_imputado
              ? T(` · <strong>precio imputado</strong>: ${esc(m.precio_metodo_imputacion)}`, " · <strong>imputed price</strong>: minimum observed in the dataset")
              : ""}</td>`;
          }
          const v = m[c.key];
          const txt = c.fmt ? c.fmt(v) : v;
          if (c.key === "nombre") {
            return `<td class="txt model">${esc(m.nombre)}${k2(m)}${m.precio_imputado ? ` <span class="badge">${T("no se comercializa", "not sold")}</span>` : ""}</td>`;
          }
          return `<td class="${c.txt ? "txt" : ""}">${v == null ? `<span class="nd">${NODATA}</span>` : esc(txt)}</td>`;
        }).join("")}</tr>`).join("")
      : `<tr><td colspan="${COLS.length}">${emptyState(NO_MODELS)}</td></tr>`;

    table.innerHTML = `<caption>${T(
      `Fuente: ${esc(META.fuente)}, corte ${META.corte}. Puntajes de tarea en % (General es un índice), un benchmark por columna, todos del mismo host. † = precio imputado.`,
      `Source: ${esc(META.fuente)}, cutoff ${META.corte}. Task scores in % (General is an index), one benchmark per column, all from the same host. † = imputed price.`
    )}</caption>${head}<tbody>${body}</tbody>`;
    const n8020 = MODELS.filter((m) => m.perfil === "80/20").length;
    $("table-foot").textContent = T(
      "Costo ponderado estimado (USD / 1M tokens), pesos 60/20/20 (entrada / lectura de caché / salida); " +
        (n8020 ? `${n8020} modelos sin tarifa de caché usan 80/20 (caché asumida igual a la entrada, cota superior). ` : "ningún modelo necesitó asumir la tarifa de caché igual a la de entrada. ") +
        "Los pesos son proporciones de tokens consumidos y el resultado no equivale al costo por tarea. Precios con tarifa base.",
      "Estimated weighted cost (USD / 1M tokens), weights 60/20/20 (input / cache read / output); " +
        (n8020 ? `${n8020} models without a cache rate use 80/20 (cache assumed equal to input, an upper bound). ` : "no model needed the cache rate assumed equal to input. ") +
        "The weights are shares of tokens consumed and the result is not the cost per task. Base-tier prices."
    );
  }

  function bindTable() {
    const table = $("table");
    table.addEventListener("click", (e) => {
      const b = e.target.closest("[data-sort]");
      if (b) {
        const k = b.dataset.sort;
        const col = COLS.find((c) => c.key === k);
        // Primer clic: las tareas de mayor a menor, el resto de menor a mayor.
        const first = TASK[k] ? -1 : 1;
        S.sort = S.sort.key === k ? { key: k, dir: -S.sort.dir } : { key: k, dir: col.txt ? 1 : first };
        renderTable(visible());
        table.querySelector(`[data-sort="${k}"]`).focus();
        return;
      }
      const row = e.target.closest("tr[data-slug]");
      if (row) select(row.dataset.slug);
    });
    table.addEventListener("keydown", (e) => {
      const row = e.target.closest("tr[data-slug]");
      if (row && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(row.dataset.slug); }
    });
  }

  buildControls();
  bindTable();
  render();

  let raf = 0, lastW = 0;
  const ro = new ResizeObserver((entries) => {
    const w = Math.round(entries[0].contentRect.width);
    if (w === lastW) return;
    lastW = w;
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => renderCharts(visible()));
  });
  ro.observe(document.querySelector("main"));
})();
