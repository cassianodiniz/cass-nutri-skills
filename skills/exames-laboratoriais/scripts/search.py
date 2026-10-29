#!/usr/bin/env python3
"""Page-aware literal/regex search over the extracted source."""

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "references" / "pages"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search extracted book pages and print physical PDF-page provenance."
    )
    parser.add_argument("query", help="literal text by default; regex with --regex")
    parser.add_argument("--regex", action="store_true")
    parser.add_argument("--context", type=int, default=3)
    parser.add_argument("--max-hits", type=int, default=20)
    args = parser.parse_args()

    pattern = re.compile(args.query if args.regex else re.escape(args.query), re.IGNORECASE)
    hits = 0
    for path in sorted(PAGES.glob("page-*.txt")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            if not pattern.search(line):
                continue
            page = int(path.stem.split("-")[-1])
            start = max(1, index - args.context)
            end = min(len(lines), index + args.context + 1)
            print(f"=== PDF physical page {page}; {path.name}; lines {start + 1}-{end} ===")
            for line_no in range(start, end):
                print(f"{line_no + 1:04d}: {lines[line_no]}")
            hits += 1
            if hits >= args.max_hits:
                return


if __name__ == "__main__":
    main()
