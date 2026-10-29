#!/usr/bin/env python3
"""Cheap integrity checks for this skill package."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md",
    "DECISION_LOG.md",
    "references/source-metadata.md",
    "references/verified-values.md",
    "references/full_text.txt",
    "scripts/search.py",
]
REVIEWED = [44, 46, 92, 93, 95, 180, 181, 182, 183, 223, 224]


def main() -> None:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    page_files = list((ROOT / "references" / "pages").glob("page-*.txt"))
    missing_images = [
        page for page in REVIEWED
        if not (ROOT / "assets" / "page-images" / f"pdf-page-{page:03d}.png").is_file()
    ]
    assert not missing, f"missing required files: {missing}"
    assert len(page_files) == 273, f"expected 273 page files, found {len(page_files)}"
    assert not missing_images, f"missing reviewed images: {missing_images}"
    print("PASS: required files present")
    print("PASS: 273/273 physical PDF pages have page-addressable text")
    print("PASS: 11/273 physical PDF pages have retained visual review evidence")


if __name__ == "__main__":
    main()
