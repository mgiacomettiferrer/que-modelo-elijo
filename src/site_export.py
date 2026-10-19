"""Integra la herramienta web en el repo del sitio mauriciogiacometti.com.

Toma las páginas sueltas de `outputs/web/que-modelo-elijo/` (ES en `index.html`,
EN en `en/index.html`), extrae su `<main>` y lo envuelve con el header, el footer,
la analítica y las fuentes del sitio. Copia los assets compartidos (JS, CSS, datos,
D3 local y el PDF) a `public/portfolio/que-modelo-elijo/`.

El sitio sirve una CSP con `script-src 'self'`: por eso D3 va copiado al propio
sitio y las páginas no tienen scripts ni estilos inline.

Uso:
    python -m src.site_export --site <ruta al repo mauricio-page>
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

SRC = Path("outputs/web/que-modelo-elijo")
SLUG = "que-modelo-elijo"
BASE = f"/portfolio/{SLUG}/"
URL = "https://mauriciogiacometti.com"

ASSETS = [
    "app.js",
    "styles.css",
    "data/models.js",
    "vendor/d3.min.js",
    "docs/que-modelo-elijo-para-mi-agente.pdf",
]

PAGES = {
    "es": {
        "src": SRC / "index.html",
        "dest": Path("public/portfolio") / SLUG / "index.html",
        "lang": "es-UY",
        "home": "/",
        "path": BASE,
        "title": "¿Qué modelo elijo para mi agente? | Mauricio Giacometti",
        "og_title": "¿Qué modelo elijo para mi agente?",
        "description": "Cómo se ordenan 24 modelos de lenguaje de 16 proveedores según capacidad, velocidad y precio, y cómo elegir uno para tu agente. Datos de Artificial Analysis al 2026-10-19.",
        "og_locale": "es_UY",
        "skip": "Saltar al contenido",
        "home_label": "Mauricio Giacometti, inicio",
        "nav": [("Enfoque", "/#enfoque"), ("Trayectoria", "/#trayectoria"), ("Ideas", "/#ideas"), ("Portfolio", "/#portfolio")],
        "nav_label": "Navegación principal",
        "lang_label": "Idioma",
        "contact": ("Conversemos", "/#contacto"),
        "motto": "CONOCER PARA TRANSFORMAR.",
        "kicker": ("UN EXPERIMENTO / MODELOS DE LENGUAJE", "DATOS DE ARTIFICIAL ANALYSIS · 2026-10-19"),
        "back": "VOLVER AL SITIO ↑",
        "h1": ("¿Qué modelo elijo", "para mi agente?"),
    },
    "en": {
        "src": SRC / "en" / "index.html",
        "dest": Path("public/en/portfolio") / SLUG / "index.html",
        "lang": "en",
        "home": "/en/",
        "path": f"/en{BASE}",
        "title": "Which model should my agent use? | Mauricio Giacometti",
        "og_title": "Which model should my agent use?",
        "description": "How 24 language models from 16 providers line up by capability, speed and price, and how to pick one for your agent. Data from Artificial Analysis as of 2026-10-19.",
        "og_locale": "en",
        "skip": "Skip to content",
        "home_label": "Mauricio Giacometti, home",
        "nav": [("Approach", "/en/#approach"), ("Experience", "/en/#experience"), ("Ideas", "/en/#ideas"), ("Portfolio", "/en/#portfolio")],
        "nav_label": "Main navigation",
        "lang_label": "Language",
        "contact": ("Let’s talk", "/en/#contact"),
        "motto": "KNOW TO TRANSFORM.",
        "kicker": ("AN EXPERIMENT / LANGUAGE MODELS", "ARTIFICIAL ANALYSIS DATA · 2026-10-19"),
        "back": "BACK TO THE SITE ↑",
        "h1": ("Which model should", "my agent use?"),
    },
}


def extract_main(html: str) -> tuple[str, str]:
    main = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    tooltip = re.search(r'<div id="tooltip"[^>]*></div>', html)
    if not main or not tooltip:
        raise SystemExit("No encontré <main> o el tooltip en la página suelta.")
    return main.group(1), tooltip.group(0)


def adapt_body(body: str, cfg: dict) -> str:
    # Rutas relativas de la página suelta -> absolutas en el sitio.
    body = re.sub(r'href="(?:\.\./)?docs/', f'href="{BASE}docs/', body)
    # Título con el acento tipográfico del sitio (segunda línea en serif itálica).
    first, second = cfg["h1"]
    body = re.sub(r'<h1 id="l1-title">.*?</h1>', f'<h1 id="l1-title">{first}<br><em>{second}</em></h1>', body, count=1, flags=re.S)
    if "style=" in body or "onsubmit" in body or "onclick" in body:
        raise SystemExit("La página tiene estilos o handlers inline: la CSP del sitio los bloquea.")
    return body


def page(cfg: dict, body: str, tooltip: str) -> str:
    es, en = PAGES["es"]["path"], PAGES["en"]["path"]
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in cfg["nav"])
    active_es = ' active' if cfg["lang"] != "en" else ""
    active_en = ' active' if cfg["lang"] == "en" else ""
    k1, k2 = cfg["kicker"]
    return f"""<!doctype html>
<html lang="{cfg['lang']}">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-HJQH0KGETC"></script>
<script src="/gtag.js"></script>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#171916">
<title>{cfg['title']}</title>
<meta name="description" content="{cfg['description']}">
<link rel="canonical" href="{URL}{cfg['path']}">
<link rel="alternate" hreflang="es-UY" href="{URL}{es}">
<link rel="alternate" hreflang="en" href="{URL}{en}">
<link rel="alternate" hreflang="x-default" href="{URL}{es}">
<meta property="og:type" content="website"><meta property="og:locale" content="{cfg['og_locale']}"><meta property="og:url" content="{URL}{cfg['path']}"><meta property="og:title" content="{cfg['og_title']}"><meta property="og:description" content="{cfg['description']}"><meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;450;500;550;600;650;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="{BASE}styles.css">
</head>
<body class="qm-body">
<a class="skip" href="#principal">{cfg['skip']}</a>
<header class="site-header">
<a class="brand" href="{cfg['home']}" aria-label="{cfg['home_label']}">mg<span class="brand-dot">.</span></a>
<a class="header-name" href="{cfg['home']}">Mauricio<br>Giacometti</a>
<nav class="desktop-nav" aria-label="{cfg['nav_label']}">{nav}</nav>
<nav class="language-switch" aria-label="{cfg['lang_label']}"><a class="lang-toggle{active_es}" href="{es}" hreflang="es-UY" lang="es">ES</a><a class="lang-toggle{active_en}" href="{en}" hreflang="en" lang="en">EN</a></nav>
<a class="header-contact" href="{cfg['contact'][1]}">{cfg['contact'][0]} <span aria-hidden="true">↗</span></a>
</header>

<main id="principal" class="qm qm-site">
<div class="section-top mono qm-kicker"><span>{k1}</span><span>{k2}</span></div>
{body.strip()}
{tooltip}
</main>

<footer class="site-footer mono">
<span>© 2026 MAURICIO GIACOMETTI</span>
<span>{cfg['motto']}</span>
<a href="{cfg['home']}">{cfg['back']}</a>
</footer>

<script src="{BASE}vendor/d3.min.js"></script>
<script src="{BASE}data/models.js"></script>
<script src="{BASE}app.js"></script>
</body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", required=True, help="raíz del repo mauricio-page")
    args = parser.parse_args()
    site = Path(args.site)
    if not (site / "wrangler.jsonc").exists():
        raise SystemExit(f"{site} no parece el repo del sitio (falta wrangler.jsonc).")

    dest_assets = site / "public/portfolio" / SLUG
    for rel in ASSETS:
        target = dest_assets / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / rel, target)
        print(f"copiado {target}")

    for cfg in PAGES.values():
        body, tooltip = extract_main(cfg["src"].read_text(encoding="utf-8"))
        out = site / cfg["dest"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(cfg, adapt_body(body, cfg), tooltip), encoding="utf-8")
        print(f"escrito {out}")


if __name__ == "__main__":
    main()
