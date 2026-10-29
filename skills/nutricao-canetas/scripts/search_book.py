#!/usr/bin/env python3
"""Search a generated book skill through aliases, mentions, and SQLite FTS5."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import unicodedata
from collections import defaultdict
from pathlib import Path


STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "da", "das", "de", "do", "dos", "e",
    "em", "for", "from", "how", "in", "is", "o", "of", "on", "or", "os", "para",
    "por", "qual", "quais", "que", "sobre", "the", "to", "um", "uma", "what", "with",
}


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()


def boundary_contains(text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text))


def index_fingerprint(database: Path) -> str | None:
    if not database.is_file():
        return None
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        try:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key='fingerprint'"
            ).fetchone()
            return row[0] if row else None
        finally:
            connection.close()
    except sqlite3.Error:
        return None


def ensure_index(root: Path, database: Path) -> bool:
    from build_search_index import build, source_fingerprint

    expected = source_fingerprint(root)
    if index_fingerprint(database) == expected:
        return False
    build(root, database)
    return True


def load_topics(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        "SELECT canonical, label, home_chapter, alias, folded_alias FROM topic_aliases "
        "ORDER BY length(folded_alias) DESC, canonical"
    ).fetchall()
    topics: dict[str, dict] = {}
    for canonical, label, home, alias, folded_alias in rows:
        topic = topics.setdefault(
            canonical,
            {"canonical": canonical, "label": label, "home_chapter": home, "aliases": []},
        )
        topic["aliases"].append((alias, folded_alias))
    return list(topics.values())


def detect_topics(query: str, topics: list[dict]) -> list[dict]:
    folded_query = fold(query)
    detected = []
    for topic in topics:
        matches = [
            alias
            for alias, folded_alias in topic["aliases"]
            if boundary_contains(folded_query, folded_alias)
        ]
        if matches:
            detected.append(
                {
                    "canonical": topic["canonical"],
                    "label": topic["label"],
                    "home_chapter": topic["home_chapter"],
                    "matched_aliases": matches,
                }
            )
    detected.sort(key=lambda item: folded_query.find(fold(item["matched_aliases"][0])))
    return detected


def query_terms(query: str, detected: list[dict]) -> list[str]:
    value = fold(query)
    for topic in detected:
        for alias in topic["matched_aliases"]:
            value = re.sub(rf"(?<!\w){re.escape(fold(alias))}(?!\w)", " ", value)
    return [
        token
        for token in re.findall(r"[\w-]+", value, flags=re.UNICODE)
        if len(token) >= 3 and token not in STOPWORDS
    ]


def best_passage(body: str, needles: list[str]) -> tuple[str, str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", body) if block.strip()]
    if not blocks:
        return "", ""

    def score(block: str) -> tuple[int, int]:
        folded = fold(block)
        return sum(1 for needle in needles if needle and needle in folded), -len(block)

    block = max(blocks, key=score)
    normalized = re.sub(r"\s+", " ", block).strip()
    evidence = normalized[:500].rstrip()
    snippet = normalized if len(normalized) <= 900 else normalized[:897].rstrip() + "..."
    return snippet, evidence


def retrieve(root: Path, query: str, limit: int, per_chapter: int, comprehensive: bool) -> dict:
    started = time.perf_counter()
    database = root / "references" / "search" / "book-search.sqlite3"
    rebuilt = ensure_index(root, database)
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        topics = load_topics(connection)
        detected = detect_topics(query, topics)
        terms = query_terms(query, detected)
        detected_canonicals = [topic["canonical"] for topic in detected]
        aliases = [fold(alias) for topic in detected for alias in topic["matched_aliases"]]

        if detected:
            placeholders = ",".join("?" for _ in detected)
            rows = connection.execute(
                f"""
                SELECT d.id, d.document_kind, d.ordinal, d.page, d.chapter,
                       d.source_path, d.body, d.folded_body,
                       COUNT(DISTINCT m.canonical), GROUP_CONCAT(DISTINCT m.canonical)
                FROM documents d JOIN mentions m ON m.document_id=d.id
                WHERE m.canonical IN ({placeholders})
                GROUP BY d.id
                """,
                detected_canonicals,
            ).fetchall()
            primary = detected[0]["canonical"]
            matching_documents, matching_chapters = connection.execute(
                """SELECT COUNT(DISTINCT m.document_id), COUNT(DISTINCT d.chapter)
                   FROM mentions m JOIN documents d ON d.id=m.document_id
                   WHERE m.canonical=?""",
                (primary,),
            ).fetchone()
            retrieval_mode = "alias-map"
        else:
            if not terms:
                rows = []
            else:
                expression = " AND ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)
                rows = connection.execute(
                    """SELECT d.id, d.document_kind, d.ordinal, d.page, d.chapter,
                              d.source_path, d.body, d.folded_body, 0, ''
                       FROM documents_fts f JOIN documents d ON d.id=f.rowid
                       WHERE documents_fts MATCH ? ORDER BY bm25(documents_fts) LIMIT 250""",
                    (expression,),
                ).fetchall()
            matching_documents = len(rows)
            matching_chapters = len({row[4] for row in rows})
            retrieval_mode = "fts5"

        scored = []
        primary_home = detected[0]["home_chapter"] if detected else ""
        expected_topic_count = len(detected)
        for row in rows:
            (
                _document_id,
                kind,
                ordinal,
                page,
                chapter,
                source_path,
                body,
                folded_body,
                matched_count,
                matched_topics,
            ) = row
            term_score = sum(min(folded_body.count(term), 8) * 3 for term in terms)
            topic_score = matched_count * 100
            pair_bonus = 200 if expected_topic_count > 1 and matched_count == expected_topic_count else 0
            home_bonus = 50 if primary_home and chapter == primary_home else 0
            snippet, evidence = best_passage(body, aliases + terms)
            scored.append(
                {
                    "document_kind": kind,
                    "ordinal": ordinal,
                    "page": page,
                    "chapter": chapter,
                    "source_path": source_path,
                    "score": topic_score + pair_bonus + home_bonus + term_score,
                    "matched_topic_count": matched_count,
                    "matched_topics": matched_topics.split(",") if matched_topics else [],
                    "snippet": snippet,
                    "evidence": evidence,
                }
            )

        by_chapter: dict[str, list[dict]] = defaultdict(list)
        for hit in sorted(scored, key=lambda item: (-item["score"], item["ordinal"])):
            by_chapter[hit["chapter"]].append(hit)
        ordered_chapters = sorted(
            by_chapter,
            key=lambda chapter: (
                chapter != primary_home if expected_topic_count <= 1 else False,
                -by_chapter[chapter][0]["score"],
                chapter,
            ),
        )
        selected = []
        rounds = per_chapter if comprehensive else 1
        for round_index in range(rounds):
            for chapter in ordered_chapters:
                if round_index < len(by_chapter[chapter]):
                    selected.append(by_chapter[chapter][round_index])
                    if len(selected) >= limit:
                        break
            if len(selected) >= limit:
                break
        return {
            "query": query,
            "source_scope": "book-only",
            "external_sources_used": False,
            "retrieval_mode": retrieval_mode,
            "index_rebuilt": rebuilt,
            "detected_topics": detected,
            "coverage": {
                "primary_topic": detected[0]["canonical"] if detected else None,
                "matching_documents": matching_documents,
                "matching_chapters": matching_chapters,
                "returned_documents": len(selected),
                "returned_chapters": len({item["chapter"] for item in selected}),
            },
            "results": selected,
            "retrieval_time_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    finally:
        connection.close()


def print_text(result: dict) -> None:
    coverage = result["coverage"]
    print(
        f"Coverage: {coverage['matching_documents']} documents in "
        f"{coverage['matching_chapters']} chapters"
    )
    print(f"Mode: {result['retrieval_mode']} | Search: {result['retrieval_time_ms']:.2f} ms\n")
    for hit in result["results"]:
        location = f"page {hit['page']}" if hit["page"] is not None else hit["chapter"]
        print(f"{location} | {hit['source_path']} | score {hit['score']}")
        print(hit["snippet"] + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--per-chapter", type=int, default=2)
    parser.add_argument("--comprehensive", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    result = retrieve(root, args.query, args.limit, args.per_chapter, args.comprehensive)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 0 if result["results"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
