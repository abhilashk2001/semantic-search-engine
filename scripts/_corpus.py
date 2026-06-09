"""Pure, network-free helpers for building the demo corpus.

Kept separate from ``download_data.py`` so the cleaning, dedupe, and sampling
logic is unit-testable without touching HuggingFace or the network.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable, Iterator

MIN_CHARS = 150
MIN_ALPHA_RATIO = 0.6


def split_paragraphs(article_text: str) -> list[str]:
    """Split an article into trimmed, non-empty paragraphs."""
    return [line.strip() for line in article_text.split("\n") if line.strip()]


def is_good_paragraph(paragraph: str) -> bool:
    """Keep substantial prose; drop stubs, tables, and markup-heavy lines."""
    if len(paragraph) < MIN_CHARS:
        return False
    alpha_like = sum(c.isalpha() or c.isspace() for c in paragraph)
    return alpha_like / len(paragraph) >= MIN_ALPHA_RATIO


def clean_article(article_text: str) -> list[str]:
    return [p for p in split_paragraphs(article_text) if is_good_paragraph(p)]


def _norm_key(paragraph: str) -> str:
    return " ".join(paragraph.lower().split())


def dedupe(paragraphs: Iterable[str]) -> Iterator[str]:
    """Yield paragraphs with case/whitespace-insensitive duplicates removed."""
    seen: set[str] = set()
    for p in paragraphs:
        key = _norm_key(p)
        if key in seen:
            continue
        seen.add(key)
        yield p


def sample(paragraphs: list[str], n: int, seed: int) -> list[str]:
    """Deterministically shuffle and take ``n`` paragraphs."""
    pool = list(paragraphs)
    random.Random(seed).shuffle(pool)
    return pool[:n]


def to_rows(paragraphs: list[str]) -> list[dict]:
    return [{"id": i, "text": text} for i, text in enumerate(paragraphs)]


def save_corpus(path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_corpus(path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
