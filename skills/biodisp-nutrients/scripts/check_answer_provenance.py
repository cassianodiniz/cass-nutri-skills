#!/usr/bin/env python3
"""Fail closed when an internal provenance record is incomplete."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", help="Internal provenance record path, or - for stdin")
    args = parser.parse_args()
    text = sys.stdin.read() if args.draft == "-" else Path(args.draft).read_text(encoding="utf-8")
    root = Path(__file__).resolve().parent.parent

    book = "Origem: livro" in text
    external = "Origem: externa" in text
    missing = "Não localizado no livro" in text
    if not any((book, external, missing)):
        return fail("adicione Origem: livro, Origem: externa ou Não localizado no livro")
    if sum((book, external, missing)) > 1 and "Separação de fontes:" not in text:
        return fail("fontes misturadas exigem o bloco Separação de fontes:")

    if book:
        pages = [int(value) for value in re.findall(r"PDF p\.\s*(\d+)", text)]
        if not pages:
            return fail("Origem: livro exige pelo menos uma citação PDF p. N")
        absent = [page for page in pages if not (root / "references" / "pages" / f"page-{page:04d}.md").is_file()]
        if absent:
            return fail(f"páginas citadas não existem na skill: {absent}")
        evidence = {
            int(page): snippet.strip()
            for page, snippet in re.findall(r"^Evidência \[PDF p\.\s*(\d+)\]:\s*(.+)$", text, re.MULTILINE)
        }
        missing_evidence = sorted(set(pages) - set(evidence))
        if missing_evidence:
            return fail(f"cada página citada exige Evidência [PDF p. N]: trecho; faltam {missing_evidence}")
        for page in sorted(set(pages)):
            snippet = normalize(evidence[page])
            if len(snippet) < 12:
                return fail(f"evidência curta demais para PDF p. {page}")
            page_text = normalize(
                (root / "references" / "pages" / f"page-{page:04d}.md").read_text(encoding="utf-8")
            )
            if snippet not in page_text:
                return fail(f"evidência não encontrada literalmente em PDF p. {page}")

    if external:
        if "Fonte externa:" not in text:
            return fail("Origem: externa exige Fonte externa:")
        if not re.search(r"https?://\S+", text):
            return fail("Fonte externa exige link verificável")

    print("PASS: registro interno de proveniência válido")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
