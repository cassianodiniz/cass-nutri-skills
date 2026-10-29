#!/usr/bin/env python3
"""Build the deterministic FTS5 and mention index from page Markdown files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char)).casefold()
    return re.sub(r"\s+", " ", value)


def source_contains_alias(body: str, folded_body: str, alias: str, folded_alias: str) -> bool:
    """Avoid treating Portuguese conjunctions as one-letter vitamin names."""
    vitamin_code = re.fullmatch(r"vitamina\s+([A-Z](?:\s?\d+)?)", alias)
    if vitamin_code:
        code = re.escape(vitamin_code.group(1)).replace(r"\ ", r"\s*")
        return bool(re.search(rf"(?i:vitamina)\s+{code}(?!\w)", body))
    return bool(re.search(rf"(?<!\w){re.escape(folded_alias)}(?!\w)", folded_body))


def chapter_for_page(page: int, starts: list[int]) -> str:
    chapter = 0
    for index, start in enumerate(starts, start=1):
        if page < start:
            break
        chapter = index
    return f"ch{chapter:02d}" if chapter else "front-matter"


def source_fingerprint(page_files: list[Path], aliases_path: Path) -> str:
    digest = hashlib.sha256(aliases_path.read_bytes())
    for page_file in page_files:
        stat = page_file.stat()
        digest.update(f"{page_file.name}:{stat.st_size}:{stat.st_mtime_ns}".encode())
    return digest.hexdigest()


def build(root: Path, output: Path) -> dict:
    aliases_path = root / "references" / "search" / "topic-aliases.json"
    metadata = json.loads((root / "metadata" / "extraction.json").read_text(encoding="utf-8"))
    topics = json.loads(aliases_path.read_text(encoding="utf-8"))["topics"]
    page_files = sorted((root / "references" / "pages").glob("page-*.md"))
    fingerprint = source_fingerprint(page_files, aliases_path)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp.sqlite3")
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(str(temporary))
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=OFF;
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE pages(
                page INTEGER PRIMARY KEY,
                chapter TEXT NOT NULL,
                page_path TEXT NOT NULL,
                body TEXT NOT NULL,
                folded_body TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE pages_fts USING fts5(
                body,
                content='pages',
                content_rowid='page',
                tokenize='unicode61 remove_diacritics 2'
            );
            CREATE TABLE topic_aliases(
                canonical TEXT NOT NULL,
                label TEXT NOT NULL,
                home_chapter TEXT NOT NULL,
                alias TEXT NOT NULL,
                folded_alias TEXT NOT NULL,
                PRIMARY KEY(canonical, folded_alias)
            );
            CREATE TABLE mentions(
                canonical TEXT NOT NULL,
                page INTEGER NOT NULL,
                alias TEXT NOT NULL,
                PRIMARY KEY(canonical, page, alias),
                FOREIGN KEY(page) REFERENCES pages(page)
            );
            CREATE INDEX mentions_topic_page ON mentions(canonical, page);
            """
        )
        connection.execute("INSERT INTO metadata VALUES (?, ?)", ("fingerprint", fingerprint))
        connection.execute("INSERT INTO metadata VALUES (?, ?)", ("schema_version", "2"))

        normalized_topics = []
        for topic in topics:
            aliases = sorted(set(topic["aliases"]), key=lambda item: (-len(fold(item)), fold(item)))
            normalized_topics.append((topic, [(alias, fold(alias)) for alias in aliases]))
            for alias, folded_alias in normalized_topics[-1][1]:
                connection.execute(
                    "INSERT INTO topic_aliases VALUES (?, ?, ?, ?, ?)",
                    (topic["canonical"], topic["label"], topic["home_chapter"], alias, folded_alias),
                )

        mention_count = 0
        for page_file in page_files:
            page = int(re.search(r"(\d+)", page_file.stem).group(1))
            body = page_file.read_text(encoding="utf-8")
            folded_body = fold(body)
            chapter = chapter_for_page(page, metadata["chapter_starts"])
            relative_path = page_file.relative_to(root).as_posix()
            connection.execute(
                "INSERT INTO pages VALUES (?, ?, ?, ?, ?)",
                (page, chapter, relative_path, body, folded_body),
            )
            for topic, aliases in normalized_topics:
                for alias, folded_alias in aliases:
                    if source_contains_alias(body, folded_body, alias, folded_alias):
                        connection.execute(
                            "INSERT OR IGNORE INTO mentions VALUES (?, ?, ?)",
                            (topic["canonical"], page, alias),
                        )
                        mention_count += 1
        connection.execute("INSERT INTO pages_fts(pages_fts) VALUES ('rebuild')")
        connection.commit()
    finally:
        connection.close()
    temporary.replace(output)
    return {"pages": len(page_files), "mentions": mention_count, "fingerprint": fingerprint}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.root / "references" / "search" / "book-search.sqlite3"
    print(json.dumps(build(args.root, output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
