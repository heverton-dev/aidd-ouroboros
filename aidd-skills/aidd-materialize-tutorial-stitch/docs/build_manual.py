"""Gera docs/MANUAL.pdf a partir de docs/MANUAL.md: Pandoc (HTML com sumário) -> Chrome/Edge headless (PDF).
Numera as páginas com pypdf + reportlab quando disponíveis. Uso: python docs/build_manual.py"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SRC, CSS, HTML, PDF = DOCS / "MANUAL.md", DOCS / "manual.css", DOCS / "MANUAL.html", DOCS / "MANUAL.pdf"


def browser() -> str:
    cands = {
        "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
        "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
    }.get(platform.system(), [])
    for c in cands + [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chrome", "msedge")]:
        if c and Path(c).exists():
            return c
    sys.exit("Chrome/Edge não encontrado")


def number_pages(pdf: Path) -> None:
    try:
        from io import BytesIO
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
    except ImportError:
        print("pypdf/reportlab ausentes: PDF sem numeração de páginas")
        return
    reader, writer = PdfReader(str(pdf)), PdfWriter()
    total = len(reader.pages)
    for i, page in enumerate(reader.pages, 1):
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        if i > 1:  # capa sem número
            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=(w, h))
            c.setFont("Helvetica", 8)
            c.setFillGray(0.45)
            c.drawString(42, 24, "aidd-tutorial-creator · Manual completo")
            c.drawRightString(w - 42, 24, f"{i} / {total}")
            c.save()
            buf.seek(0)
            page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)
    writer.add_metadata({"/Title": "aidd-tutorial-creator — Manual completo", "/Author": "aidd-tutorial-creator"})
    with open(pdf, "wb") as f:
        writer.write(f)


def main() -> None:
    pandoc = shutil.which("pandoc") or sys.exit("pandoc não encontrado")
    subprocess.run([pandoc, str(SRC), "-o", str(HTML), "--standalone", "--toc", "--toc-depth=2",
                    "--embed-resources", "--css", str(CSS), "--metadata", "lang=pt-BR"], check=True)
    subprocess.run([browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={PDF}", HTML.as_uri()], check=True, capture_output=True)
    number_pages(PDF)
    HTML.unlink(missing_ok=True)
    print(f"{PDF} ({PDF.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
