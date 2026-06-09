"""Download and clean a deterministic 10k-paragraph Wikipedia Simple English corpus.

Streams the dataset (never a full local download), splits articles into
paragraphs, filters junk, dedupes, then takes a seeded sample. Writes
``data/corpus.jsonl`` (git-ignored). Run:

    uv run --extra data python -m scripts.download_data
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts._corpus import clean_article, dedupe, sample, save_corpus, to_rows

DATASET = "wikimedia/wikipedia"
CONFIG = "20231101.simple"
DEFAULT_OUT = Path("data/corpus.jsonl")


def collect_paragraphs(target_pool: int) -> list[str]:
    """Stream articles and collect up to ``target_pool`` clean, deduped paragraphs."""
    from datasets import load_dataset

    stream = load_dataset(DATASET, CONFIG, split="train", streaming=True)
    pool: list[str] = []
    seen: set[str] = set()
    for article in stream:
        for paragraph in clean_article(article["text"]):
            key = " ".join(paragraph.lower().split())
            if key in seen:
                continue
            seen.add(key)
            pool.append(paragraph)
        if len(pool) >= target_pool:
            break
    return pool


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=10_000, help="paragraphs to keep")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--pool-factor",
        type=int,
        default=4,
        help="collect n*pool_factor paragraphs before sampling, for variety",
    )
    args = parser.parse_args()

    print(f"Streaming {DATASET}/{CONFIG} for ~{args.n * args.pool_factor} paragraphs...")
    pool = list(dedupe(collect_paragraphs(args.n * args.pool_factor)))
    print(f"Collected {len(pool)} clean unique paragraphs; sampling {args.n}.")

    chosen = sample(pool, args.n, args.seed)
    if len(chosen) < args.n:
        raise SystemExit(
            f"Only {len(chosen)} paragraphs available; increase --pool-factor."
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    save_corpus(args.out, to_rows(chosen))
    print(f"Wrote {len(chosen)} paragraphs to {args.out}")


if __name__ == "__main__":
    main()
