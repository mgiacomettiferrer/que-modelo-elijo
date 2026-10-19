"""Convierte el artículo en Markdown a PDF para descargarlo desde la web.

Pasos:
1. Markdown -> HTML con estilos de impresión (tablas, figura embebida en base64
   para que el PDF no dependa de rutas relativas).
2. HTML -> PDF con Chrome o Edge en modo headless (`--print-to-pdf`).

El PDF queda dentro de la carpeta de la web para publicarse con ella.

Uso:
    python -m src.article_pdf
    python -m src.article_pdf --chrome "<ruta al ejecutable>"
"""

from __future__ import annotations

import argparse
import base64
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown

ARTICLE = Path("outputs/article/que-modelo-elijo-para-mi-agente.md")
OUT = Path("outputs/web/que-modelo-elijo/docs/que-modelo-elijo-para-mi-agente.pdf")

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "msedge",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font: 10.5pt/1.5 "Segoe UI", system-ui, sans-serif; color: #1d1f23; }
h1 { font-size: 22pt; margin: 0 0 4pt; }
h2 { font-size: 14pt; margin: 18pt 0 6pt; border-bottom: 1px solid #ccc; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 6pt 0; page-break-inside: avoid; }
th, td { border-bottom: 1px solid #ddd; padding: 3pt 5pt; text-align: left; }
th { background: #f1f0ec; }
code { font-family: Consolas, monospace; font-size: 9pt; }
img { max-width: 100%; page-break-inside: avoid; }
hr { border: 0; border-top: 1px solid #ddd; margin: 12pt 0; }
em { color: #444; }
"""


def find_browser(explicit: str | None) -> str:
    for cand in [explicit] if explicit else CANDIDATES:
        path = shutil.which(cand) or (cand if cand and Path(cand).exists() else None)
        if path:
            return path
    raise SystemExit("No encontré Chrome ni Edge. Pasá la ruta con --chrome.")


def embed_images(html: str, base: Path) -> str:
    """Reemplaza src relativos por data URIs, para que el PDF sea autocontenido."""

    def repl(match: re.Match) -> str:
        src = match.group(1)
        path = (base / src).resolve()
        if not path.exists():
            raise SystemExit(f"Figura no encontrada: {path}")
        data = base64.b64encode(path.read_bytes()).decode()
        return f'src="data:image/png;base64,{data}"'

    return re.sub(r'src="(?!data:|https?:)([^"]+)"', repl, html)


def build_html(md_path: Path) -> str:
    body = markdown.markdown(md_path.read_text(encoding="utf-8"), extensions=["tables"])
    body = embed_images(body, md_path.parent)
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        f"<title>¿Qué modelo elijo para mi agente?</title><style>{CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="src", default=str(ARTICLE))
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--chrome", default=None)
    args = parser.parse_args()

    browser = find_browser(args.chrome)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "article.html"
        html_path.write_text(build_html(Path(args.src)), encoding="utf-8")
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out}",
                html_path.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
    print(f"escrito {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
