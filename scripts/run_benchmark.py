"""Sweep ef_search and record recall@10 vs latency to benchmarks/results.json.

Runs on real hardware (not the free-tier server) so the demo's chart shows
trustworthy, flattering numbers. The frontend renders this static file; it is
never recomputed live. Run:

    uv run --extra data python -m scripts.run_benchmark
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from engine import HNSWIndex

DEFAULT_INDEX = Path("index.pkl")
DEFAULT_OUT = Path("benchmarks/results.json")
EF_SWEEP = [10, 20, 30, 50, 75, 100, 150, 200]
RESULTS_KEYS = {"dataset", "n", "dim", "metric", "k", "sweep", "generated_at"}


def ground_truth(matrix: np.ndarray, ids: list[int], q: np.ndarray, k: int, metric: str):
    if metric in ("cosine", "dot"):
        dists = -(matrix @ q)
    else:
        diff = matrix - q
        dists = np.einsum("ij,ij->i", diff, diff)
    return {ids[i] for i in np.argsort(dists)[:k]}


def run(index: HNSWIndex, n_queries: int, k: int, seed: int) -> list[dict]:
    ids = sorted(index.nodes)
    matrix = np.stack([index.nodes[i].vector for i in ids])
    rng = np.random.default_rng(seed)
    sample = rng.choice(len(ids), size=min(n_queries, len(ids)), replace=False)
    queries = [matrix[i] for i in sample]
    truths = [ground_truth(matrix, ids, q, k, index.metric) for q in queries]

    sweep = []
    for ef in EF_SWEEP:
        hits = 0
        latencies = []
        for q, truth in zip(queries, truths):
            start = time.perf_counter()
            got = {nid for nid, _, _ in index.search(q, k=k, ef=ef)}
            latencies.append((time.perf_counter() - start) * 1000.0)
            hits += len(truth & got)
        sweep.append(
            {
                "ef_search": ef,
                "recall_at_10": round(hits / (k * len(queries)), 4),
                "p50_latency_ms": round(float(np.percentile(latencies, 50)), 4),
            }
        )
        print(f"ef={ef:>3}: recall@{k}={sweep[-1]['recall_at_10']:.3f} "
              f"p50={sweep[-1]['p50_latency_ms']:.3f}ms")
    return sweep


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--n-queries", type=int, default=200)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    index = HNSWIndex.load(args.index)
    print(f"Loaded {index.node_count} vectors (dim={index.dim}, metric={index.metric})")
    sweep = run(index, args.n_queries, args.k, args.seed)

    results = {
        "dataset": "wikipedia-simple-en",
        "n": index.node_count,
        "dim": index.dim,
        "metric": index.metric,
        "k": args.k,
        "sweep": sweep,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
