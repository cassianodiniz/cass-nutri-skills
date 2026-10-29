#!/usr/bin/env python3
"""Split pdftotext output on form-feed boundaries, preserving physical PDF pages."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "full_text.txt"
DEST = ROOT / "references" / "pages"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    pages = SOURCE.read_text(encoding="utf-8").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    for number, text in enumerate(pages, start=1):
        header = f"PDF_PHYSICAL_PAGE={number}\n"
        (DEST / f"page-{number:03d}.txt").write_text(header + text, encoding="utf-8")
    print(f"wrote {len(pages)} page files to {DEST}")


if __name__ == "__main__":
    main()
