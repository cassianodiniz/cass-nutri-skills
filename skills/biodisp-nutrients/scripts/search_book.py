#!/usr/bin/env python3
"""Fast chapter-aware and comprehensive retrieval over the recovered book."""

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
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e",
    "em", "entre", "o", "os", "ou", "para", "por", "qual", "quais", "que", "sobre",
    "sua", "suas", "seu", "seus", "toda", "todas", "todo", "todos", "tudo", "um", "uma",
}

INTENTS = {
    "interactions": {
        "triggers": ("interacao", "interacoes", "interage", "junto", "combina"),
        "signals": ("interacao", "absor", "biodispon", "aument", "redu", "diminu", "inib", "compet", "sinerg", "depend", "efeito", "regener", "recicl", "atenu", "antagon", "modul"),
    },
    "absorption": {
        "triggers": ("absorcao", "absorver", "biodisponibilidade"),
        "signals": ("absor", "biodispon", "micela", "lipidio", "transport", "aument", "redu", "inib"),
    },
    "deficiency": {
        "triggers": ("deficiencia", "carencia"),
        "signals": ("deficien", "carencia", "deple", "sintoma", "concentracao", "estado nutricional"),
    },
    "toxicity": {
        "triggers": ("toxicidade", "excesso", "limite", "risco"),
        "signals": ("toxic", "excesso", "limite", "risco", "advers", "dose"),
    },
    "recommendation": {
        "triggers": ("recomendacao", "recomendacoes", "quanto", "dose", "necessidade"),
        "signals": ("recomend", "ingestao", "necessidade", "mg", "µg", "dose", "dri", "rda", "ear"),
    },
}


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char)).casefold()
    return re.sub(r"\s+", " ", value)


def boundary_contains(text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text))


def ensure_index(root: Path, database: Path) -> None:
    if database.is_file():
        return
    from build_search_index import build
    build(root, database)


def load_topics(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        "SELECT canonical, label, home_chapter, alias, folded_alias FROM topic_aliases "
        "ORDER BY length(folded_alias) DESC, canonical"
    ).fetchall()
    topics: dict[str, dict] = {}
    for canonical, label, home, alias, folded_alias in rows:
        topic = topics.setdefault(canonical, {"canonical": canonical, "label": label, "home_chapter": home, "aliases": []})
        topic["aliases"].append((alias, folded_alias))
    return list(topics.values())


def detect_topics(query: str, topics: list[dict]) -> list[dict]:
    folded_query = fold(query)
    detected = []
    for topic in topics:
        matches = [alias for alias, folded_alias in topic["aliases"] if boundary_contains(folded_query, folded_alias)]
        if matches:
            detected.append({
                "canonical": topic["canonical"],
                "label": topic["label"],
                "home_chapter": topic["home_chapter"],
                "matched_aliases": matches,
            })
    detected.sort(key=lambda topic: folded_query.find(fold(topic["matched_aliases"][0])))
    return detected


def detect_intents(query: str) -> tuple[list[str], tuple[str, ...]]:
    folded_query = fold(query)
    names = []
    signals = []
    for name, definition in INTENTS.items():
        if any(boundary_contains(folded_query, trigger) for trigger in definition["triggers"]):
            names.append(name)
            signals.extend(definition["signals"])
    return names or ["general"], tuple(dict.fromkeys(signals))


def query_terms(query: str, detected: list[dict]) -> list[str]:
    folded_query = fold(query)
    for topic in detected:
        for alias in topic["matched_aliases"]:
            folded_query = re.sub(rf"(?<!\w){re.escape(fold(alias))}(?!\w)", " ", folded_query)
    return [token for token in re.findall(r"[a-z0-9]+", folded_query) if len(token) > 2 and token not in STOPWORDS]


def source_contains_alias(body: str, alias: str) -> bool:
    vitamin_code = re.fullmatch(r"vitamina\s+([A-Z](?:\s?\d+)?)", alias)
    if vitamin_code:
        code = re.escape(vitamin_code.group(1)).replace(r"\ ", r"\s*")
        return bool(re.search(rf"(?i:vitamina)\s+{code}(?!\w)", body))
    return boundary_contains(fold(body), fold(alias))


def best_passage(
    body: str,
    aliases: list[str],
    terms: list[str],
    signals: tuple[str, ...],
    all_topics: list[dict],
    detected_canonicals: set[str],
    cross_relation: bool,
) -> tuple[str, str, list[str]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", body) if block.strip()]
    if not blocks:
        return "", "", []
    alias_blocks = [
        block for block in blocks
        if any(source_contains_alias(block, alias) for alias in aliases)
    ]
    if alias_blocks:
        blocks = alias_blocks
    needles = [fold(item) for item in aliases] + terms + list(signals)
    def related_topics(block: str) -> list[str]:
        related = []
        sentences = [
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", block))
            if part.strip()
        ]
        for sentence in sentences:
            folded_sentence = fold(sentence)
            has_primary = any(source_contains_alias(sentence, alias) for alias in aliases)
            has_relation_signal = any(signal in folded_sentence for signal in signals)
            if not (has_primary and has_relation_signal):
                continue
            for topic in all_topics:
                if topic["canonical"] in detected_canonicals:
                    continue
                if any(source_contains_alias(sentence, alias) for alias, _ in topic["aliases"]):
                    related.append(topic["canonical"])
        return list(dict.fromkeys(related))

    def score(block: str) -> tuple[int, int]:
        folded_block = fold(block)
        hits = sum(4 for alias in aliases if source_contains_alias(block, alias))
        hits += sum(2 for term in terms if term in folded_block)
        hits += sum(1 for signal in signals if signal in folded_block)
        if cross_relation and any(signal in folded_block for signal in signals):
            hits += 12 * min(len(related_topics(block)), 2)
        return hits, -len(block)
    block = max(blocks, key=score)
    normalized = re.sub(r"\s+", " ", block).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    alias_sentences = [sentence for sentence in sentences if any(source_contains_alias(sentence, alias) for alias in aliases)]
    evidence = max(alias_sentences or sentences or [normalized], key=score)
    # No ellipsis: this remains an exact substring after whitespace normalization,
    # ready to paste into check_answer_provenance.py.
    evidence = evidence[:500].rstrip()
    snippet = normalized if len(normalized) <= 900 else normalized[:897].rstrip() + "..."
    return snippet, evidence, related_topics(evidence)


def retrieve(root: Path, query: str, limit: int, per_chapter: int, comprehensive: bool) -> dict:
    started = time.perf_counter()
    database = root / "references" / "search" / "book-search.sqlite3"
    ensure_index(root, database)
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        topics = load_topics(connection)
        detected = detect_topics(query, topics)
        intents, signals = detect_intents(query)
        terms = query_terms(query, detected)
        aliases = [alias for topic in detected for alias, _ in next(t["aliases"] for t in topics if t["canonical"] == topic["canonical"])]
        detected_canonicals = {topic["canonical"] for topic in detected}
        cross_relation = "interactions" in intents and len(detected) == 1

        if detected:
            placeholders = ",".join("?" for _ in detected)
            canonicals = [topic["canonical"] for topic in detected]
            rows = connection.execute(
                f"""
                SELECT p.page, p.chapter, p.page_path, p.body, p.folded_body,
                       COUNT(DISTINCT m.canonical) AS matched_topic_count,
                       GROUP_CONCAT(DISTINCT m.canonical) AS matched_topics
                FROM pages p JOIN mentions m ON m.page=p.page
                WHERE m.canonical IN ({placeholders})
                GROUP BY p.page
                """,
                canonicals,
            ).fetchall()
            primary = detected[0]
            matching_pages, matching_chapters = connection.execute(
                """SELECT COUNT(DISTINCT m.page), COUNT(DISTINCT p.chapter)
                   FROM mentions m JOIN pages p ON p.page=m.page WHERE m.canonical=?""",
                (primary["canonical"],),
            ).fetchone()
        else:
            fts_terms = [term for term in terms if len(term) >= 3]
            if not fts_terms:
                rows = []
            else:
                expression = " OR ".join(f'"{term}"' for term in fts_terms)
                rows = connection.execute(
                    """SELECT p.page, p.chapter, p.page_path, p.body, p.folded_body,
                              0, '' FROM pages_fts f JOIN pages p ON p.page=f.rowid
                       WHERE pages_fts MATCH ? ORDER BY bm25(pages_fts) LIMIT 200""",
                    (expression,),
                ).fetchall()
            matching_pages = len(rows)
            matching_chapters = len({row[1] for row in rows})

        scored = []
        home_chapters = {topic["home_chapter"] for topic in detected}
        primary_home = detected[0]["home_chapter"] if detected else None
        for page, chapter, page_path, body, folded_body, matched_count, matched_topics in rows:
            if chapter == "front-matter":
                continue
            topic_score = matched_count * 120
            home_score = 75 if chapter == primary_home else (25 if chapter in home_chapters else 0)
            term_score = sum(min(folded_body.count(term), 6) * 4 for term in terms)
            signal_score = sum(min(folded_body.count(signal), 5) for signal in signals)
            pair_bonus = 180 if len(detected) > 1 and matched_count == len(detected) else 0
            snippet, evidence, related_topics = best_passage(
                body, aliases, terms, signals, topics, detected_canonicals, cross_relation
            )
            relation_bonus = 80 if cross_relation and related_topics else 0
            scored.append({
                "page": page,
                "chapter": chapter,
                "page_path": page_path,
                "score": topic_score + home_score + term_score + signal_score + pair_bonus + relation_bonus,
                "matched_topic_count": matched_count,
                "matched_topics": matched_topics.split(",") if matched_topics else [],
                "related_topics": related_topics,
                "snippet": snippet,
                "evidence": evidence,
            })

        by_chapter: dict[str, list[dict]] = defaultdict(list)
        for hit in sorted(scored, key=lambda item: (-item["score"], item["page"])):
            by_chapter[hit["chapter"]].append(hit)
        ordered_chapters = sorted(
            by_chapter,
            key=lambda chapter: (
                chapter != primary_home,
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
        for hit in selected:
            hit["score"] = round(hit["score"], 3)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "query": query,
            "source_scope": "book-only",
            "external_sources_used": False,
            "detected_topics": detected,
            "intents": intents,
            "coverage": {
                "primary_topic": detected[0]["canonical"] if detected else None,
                "matching_pages": matching_pages,
                "matching_chapters": matching_chapters,
                "returned_pages": len(selected),
                "returned_chapters": len({hit["chapter"] for hit in selected}),
            },
            "results": selected,
            "retrieval_time_ms": elapsed_ms,
        }
    finally:
        connection.close()


def print_text(result: dict) -> None:
    topics = ", ".join(topic["label"] for topic in result["detected_topics"]) or "nenhum alias cadastrado"
    coverage = result["coverage"]
    print(f"Tópicos: {topics}")
    print(f"Cobertura: {coverage['matching_pages']} páginas em {coverage['matching_chapters']} capítulos")
    print(f"Busca: {result['retrieval_time_ms']:.2f} ms\n")
    for hit in result["results"]:
        print(f"{hit['chapter']} | PDF p. {hit['page']} | score {hit['score']}")
        print(hit["snippet"])
        print(f"[{hit['page_path']}]\n")


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
