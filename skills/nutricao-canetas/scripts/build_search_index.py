#!/usr/bin/env python3
"""Build a local SQLite FTS5 index for a generated book skill."""

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
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()


def load_json(path: Path, default: object) -> object:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_topics(root: Path) -> list[dict]:
    path = root / "references" / "search" / "topic-aliases.json"
    payload = load_json(path, {"topics": []})
    topics = payload.get("topics", []) if isinstance(payload, dict) else []
    normalized = []
    for raw in topics:
        canonical = str(raw.get("canonical", "")).strip()
        label = str(raw.get("label", canonical)).strip()
        home = str(raw.get("home_chapter", "")).strip()
        aliases = []
        for value in raw.get("aliases", []):
            alias = str(value).strip()
            if alias and len(fold(alias)) >= 2:
                aliases.append(alias)
        aliases = list(dict.fromkeys(aliases))
        if canonical and aliases:
            normalized.append(
                {
                    "canonical": canonical,
                    "label": label or canonical,
                    "home_chapter": home,
                    "aliases": aliases,
                }
            )
    return normalized


def load_ranges(root: Path) -> list[dict]:
    path = root / "references" / "search" / "chapter-ranges.json"
    payload = load_json(path, {"ranges": []})
    ranges = payload.get("ranges", []) if isinstance(payload, dict) else []
    normalized = []
    for item in ranges:
        try:
            start = int(item["start_page"])
            end = int(item["end_page"])
        except (KeyError, TypeError, ValueError):
            continue
        chapter = str(item.get("chapter", "")).strip()
        if chapter and start > 0 and end >= start:
            normalized.append({"chapter": chapter, "start_page": start, "end_page": end})
    return normalized


def chapter_for_page(page: int, ranges: list[dict]) -> str:
    for item in ranges:
        if item["start_page"] <= page <= item["end_page"]:
            return item["chapter"]
    return "unmapped"


def discover_documents(root: Path) -> list[dict]:
    page_files = sorted((root / "references" / "pages").glob("page-*.md"))
    ranges = load_ranges(root)
    documents = []
    if page_files:
        for path in page_files:
            match = re.search(r"(\d+)", path.stem)
            if not match:
                continue
            page = int(match.group(1))
            documents.append(
                {
                    "kind": "page",
                    "ordinal": page,
                    "page": page,
                    "chapter": chapter_for_page(page, ranges),
                    "path": path,
                }
            )
        return documents

    chapter_files = sorted((root / "references" / "chapters").glob("*-source.md"))
    for ordinal, path in enumerate(chapter_files, start=1):
        match = re.match(r"(ch\d+)", path.name, flags=re.IGNORECASE)
        documents.append(
            {
                "kind": "chapter",
                "ordinal": ordinal,
                "page": None,
                "chapter": match.group(1).lower() if match else path.stem,
                "path": path,
            }
        )
    return documents


def source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    documents = discover_documents(root)
    for document in documents:
        path = document["path"]
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    for name in ("topic-aliases.json", "chapter-ranges.json"):
        path = root / "references" / "search" / name
        if path.is_file():
            digest.update(name.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def contains_alias(folded_body: str, folded_alias: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(folded_alias)}(?!\w)", folded_body))


def build(root: Path, output: Path) -> dict:
    root = root.resolve()
    documents = discover_documents(root)
    if not documents:
        raise ValueError(
            "No indexable sources found. Create references/pages/page-*.md or "
            "references/chapters/*-source.md first."
        )
    topics = load_topics(root)
    fingerprint = source_fingerprint(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(str(temporary))
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=OFF;
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE documents(
                id INTEGER PRIMARY KEY,
                document_kind TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                page INTEGER,
                chapter TEXT NOT NULL,
                source_path TEXT NOT NULL UNIQUE,
                body TEXT NOT NULL,
                folded_body TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE documents_fts USING fts5(
                body,
                content='documents',
                content_rowid='id',
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
                document_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                PRIMARY KEY(canonical, document_id, alias),
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );
            CREATE INDEX mentions_topic_document ON mentions(canonical, document_id);
            """
        )
        connection.execute("INSERT INTO metadata VALUES (?, ?)", ("schema_version", "1"))
        connection.execute("INSERT INTO metadata VALUES (?, ?)", ("fingerprint", fingerprint))

        normalized_topics = []
        for topic in topics:
            aliases = [(alias, fold(alias)) for alias in topic["aliases"]]
            normalized_topics.append((topic, aliases))
            for alias, folded_alias in aliases:
                connection.execute(
                    "INSERT INTO topic_aliases VALUES (?, ?, ?, ?, ?)",
                    (
                        topic["canonical"],
                        topic["label"],
                        topic["home_chapter"],
                        alias,
                        folded_alias,
                    ),
                )

        mention_count = 0
        for document in documents:
            path = document["path"]
            body = path.read_text(encoding="utf-8")
            folded_body = fold(body)
            cursor = connection.execute(
                """INSERT INTO documents
                   (document_kind, ordinal, page, chapter, source_path, body, folded_body)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    document["kind"],
                    document["ordinal"],
                    document["page"],
                    document["chapter"],
                    path.relative_to(root).as_posix(),
                    body,
                    folded_body,
                ),
            )
            document_id = cursor.lastrowid
            for topic, aliases in normalized_topics:
                for alias, folded_alias in aliases:
                    if contains_alias(folded_body, folded_alias):
                        connection.execute(
                            "INSERT OR IGNORE INTO mentions VALUES (?, ?, ?)",
                            (topic["canonical"], document_id, alias),
                        )
                        mention_count += 1
        connection.execute("INSERT INTO documents_fts(documents_fts) VALUES ('rebuild')")
        connection.commit()
    except sqlite3.OperationalError as exc:
        if "fts5" in str(exc).casefold():
            raise RuntimeError("This Python SQLite build does not include FTS5") from exc
        raise
    finally:
        connection.close()
    temporary.replace(output)
    return {
        "documents": len(documents),
        "mentions": mention_count,
        "fts5_enabled": True,
        "fingerprint": fingerprint,
        "database": output.relative_to(root).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "references" / "search" / "book-search.sqlite3"
    print(json.dumps(build(root, output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
