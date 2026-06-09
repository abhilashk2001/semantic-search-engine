"""A thin service layer over :class:`~engine.hnsw.HNSWIndex`.

Holds the loaded index and the query embedder, and implements the three
operations the API exposes: search, stats, and a small live recall check.
Knows nothing about HTTP — that lives in :mod:`api.main`.
"""

from __future__ import annotations

import time

import numpy as np

from engine import HNSWIndex

from .embedding import Embedder
from .schemas import (
    BenchmarkResponse,
    SearchResponse,
    SearchResultItem,
    StatsResponse,
)


def _to_score(metric: str, distance: float) -> float:
    """Convert engine distance (smaller = closer) to a similarity (higher = better)."""
    if metric == "cosine":
        return 1.0 - distance
    # dot and euclidean both store smaller = closer; negate for a "higher better" score.
    return -distance


class SearchService:
    def __init__(
        self,
        index: HNSWIndex,
        embedder: Embedder,
        build_time_ms: float | None = None,
    ) -> None:
        self.index = index
        self.embedder = embedder
        self.build_time_ms = build_time_ms

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(
        self,
        *,
        query: str | None = None,
        vector: list[float] | None = None,
        k: int = 10,
        ef_search: int = 50,
    ) -> SearchResponse:
        if vector is not None:
            vec = np.asarray(vector, dtype=np.float32)
        else:
            vec = self.embedder.embed([query])[0]

        start = time.perf_counter()
        raw = self.index.search(vec, k=k, ef=ef_search)
        latency_ms = (time.perf_counter() - start) * 1000.0

        results = [
            SearchResultItem(
                id=node_id,
                text=metadata.get("text"),
                score=_to_score(self.index.metric, distance),
            )
            for node_id, distance, metadata in raw
        ]
        return SearchResponse(
            results=results, latency_ms=latency_ms, k=k, ef_search=ef_search
        )

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #
    def stats(self) -> StatsResponse:
        return StatsResponse(
            node_count=self.index.node_count,
            layer_distribution=self.index.layer_distribution,
            build_time_ms=self.build_time_ms,
            config={
                "M": self.index.M,
                "ef_construction": self.index.ef_construction,
                "metric": self.index.metric,
                "dim": self.index.dim,
            },
        )

    # ------------------------------------------------------------------ #
    # Live recall check (small, by design — the full curve is precomputed)
    # ------------------------------------------------------------------ #
    def benchmark(self, n_queries: int = 10, k: int = 10) -> BenchmarkResponse:
        ids = sorted(self.index.nodes)
        if not ids:
            return BenchmarkResponse(
                recall_at_k=0.0, k=k, n_queries=0, sample_latency_ms=0.0
            )

        matrix = np.stack([self.index.nodes[i].vector for i in ids])
        rng = np.random.default_rng(0)
        sample = rng.choice(len(ids), size=min(n_queries, len(ids)), replace=False)

        hits = 0
        total_latency = 0.0
        for row in sample:
            q = matrix[row]
            truth = self._ground_truth(matrix, ids, q, k)
            start = time.perf_counter()
            got = {nid for nid, _, _ in self.index.search(q, k=k, ef=50)}
            total_latency += (time.perf_counter() - start) * 1000.0
            hits += len(truth & got)

        n = len(sample)
        return BenchmarkResponse(
            recall_at_k=hits / (k * n),
            k=k,
            n_queries=n,
            sample_latency_ms=total_latency / n,
        )

    def _ground_truth(
        self, matrix: np.ndarray, ids: list[int], q: np.ndarray, k: int
    ) -> set[int]:
        metric = self.index.metric
        if metric in ("cosine", "dot"):
            dists = -(matrix @ q)
        else:  # euclidean
            diff = matrix - q
            dists = np.einsum("ij,ij->i", diff, diff)
        top = np.argsort(dists)[:k]
        return {ids[i] for i in top}
