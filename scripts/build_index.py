"""Embed the corpus and build the shippable HNSW index artifact.

Reads ``data/corpus.jsonl``, embeds every paragraph with fastembed (the same
model the API uses at query time), inserts into an HNSW index with the locked
defaults, and saves ``index.pkl``. Run:

    uv run --extra data python -m scripts.build_index
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from api.embedding import EMBED_DIM, FastEmbedEmbedder
from engine import HNSWIndex
from scripts._corpus import load_corpus

DEFAULT_CORPUS = Path("data/corpus.jsonl")
DEFAULT_OUT = Path("index.pkl")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--M", type=int, default=16)
    parser.add_argument("--ef-construction", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rows = load_corpus(args.corpus)
    print(f"Loaded {len(rows)} paragraphs from {args.corpus}")

    print("Embedding corpus with fastembed (all-MiniLM-L6-v2)...")
    embedder = FastEmbedEmbedder()
    vectors = embedder.embed([row["text"] for row in rows])
    assert vectors.shape == (len(rows), EMBED_DIM), vectors.shape

    print(f"Building HNSW index (M={args.M}, ef_construction={args.ef_construction})...")
    start = time.perf_counter()
    index = HNSWIndex(
        dim=EMBED_DIM,
        metric="cosine",
        M=args.M,
        ef_construction=args.ef_construction,
        seed=args.seed,
    )
    for row, vec in zip(rows, vectors):
        index.insert(np.asarray(vec, dtype=np.float32), metadata={"text": row["text"]})
    build_ms = (time.perf_counter() - start) * 1000.0

    index.build_time_ms = build_ms  # convenience attribute for tooling
    index.save(args.out)
    print(
        f"Built {index.node_count} nodes in {build_ms / 1000:.1f}s; "
        f"saved to {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)"
    )


if __name__ == "__main__":
    main()
