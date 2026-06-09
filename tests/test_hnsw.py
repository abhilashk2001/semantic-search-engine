"""Behavioral tests for the HNSW index.

Correctness is measured as recall against a NumPy brute-force oracle — we assert
the index returns the right neighbors, not any particular internal graph shape.
"""

import numpy as np
import pytest

from engine import HNSWIndex


def brute_force_topk(vectors: np.ndarray, query: np.ndarray, k: int, metric: str):
    """Ground-truth top-k ids via exhaustive search."""
    if metric == "cosine":
        v = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        q = query / np.linalg.norm(query)
        dists = 1.0 - v @ q
    elif metric == "dot":
        dists = -(vectors @ query)
    else:  # euclidean
        diff = vectors - query
        dists = np.einsum("ij,ij->i", diff, diff)
    return set(np.argsort(dists)[:k].tolist())


def gaussian_data(n: int, dim: int, n_queries: int):
    """Uniform Gaussian vectors — the adversarial high-dimensional worst case."""
    rng = np.random.default_rng(0)
    vectors = rng.standard_normal((n, dim)).astype(np.float32)
    queries = rng.standard_normal((n_queries, dim)).astype(np.float32)
    return vectors, queries


def embedding_like_data(n: int, dim: int, n_queries: int, n_clusters: int = 50):
    """Clustered vectors mimicking real text embeddings (low intrinsic dim).

    Sentence embeddings are not uniformly spread over the hypersphere; they form
    semantic clusters. This generator reflects the workload the index actually
    serves, unlike pure Gaussian noise.
    """
    rng = np.random.default_rng(0)
    centers = rng.standard_normal((n_clusters, dim)).astype(np.float32)
    labels = rng.integers(0, n_clusters, n)
    vectors = (centers[labels] + 0.15 * rng.standard_normal((n, dim))).astype(np.float32)
    q_labels = rng.integers(0, n_clusters, n_queries)
    queries = (
        centers[q_labels] + 0.15 * rng.standard_normal((n_queries, dim))
    ).astype(np.float32)
    return vectors, queries


def measure_recall(vectors, queries, metric: str, ef: int = 50, k: int = 10):
    index = HNSWIndex(dim=vectors.shape[1], metric=metric, M=16, ef_construction=200, seed=42)
    id_map = [index.insert(vectors[i]) for i in range(len(vectors))]
    # Inserted in order, so engine id == row index; assert that assumption holds.
    assert id_map == list(range(len(vectors)))

    hits = 0
    for q in queries:
        truth = brute_force_topk(vectors, q, k, metric)
        got = {nid for nid, _, _ in index.search(q, k=k, ef=ef)}
        hits += len(truth & got)
    return hits / (k * len(queries))


def test_search_empty_index_returns_nothing():
    index = HNSWIndex(dim=4)
    assert index.search(np.zeros(4, dtype=np.float32), k=5) == []


def test_insert_returns_sequential_ids():
    index = HNSWIndex(dim=3)
    ids = [index.insert(np.array([i, i, i], dtype=np.float32)) for i in range(5)]
    assert ids == [0, 1, 2, 3, 4]
    assert index.node_count == 5


def test_search_finds_exact_match():
    rng = np.random.default_rng(1)
    index = HNSWIndex(dim=8, seed=1)
    vectors = rng.standard_normal((200, 8)).astype(np.float32)
    for v in vectors:
        index.insert(v, metadata={"tag": "x"})
    # Querying with a stored vector should return that vector as the top hit.
    target = 123
    top_id, _, meta = index.search(vectors[target], k=1)[0]
    assert top_id == target
    assert meta == {"tag": "x"}


def test_wrong_dimension_raises():
    index = HNSWIndex(dim=4)
    with pytest.raises(ValueError):
        index.insert(np.zeros(3, dtype=np.float32))
    with pytest.raises(ValueError):
        index.search(np.zeros(5, dtype=np.float32))


def test_recall_small_cosine():
    vectors, queries = gaussian_data(n=1000, dim=32, n_queries=50)
    recall = measure_recall(vectors, queries, metric="cosine")
    assert recall >= 0.90, f"recall@10 was {recall:.3f}"


def test_recall_small_euclidean():
    vectors, queries = gaussian_data(n=1000, dim=32, n_queries=50)
    recall = measure_recall(vectors, queries, metric="euclidean")
    assert recall >= 0.90, f"recall@10 was {recall:.3f}"


@pytest.mark.slow
def test_recall_10k_completion_gate():
    """Phase 1 completion check: recall@10 >= 0.90 on 10k embedding-like vectors
    with default parameters (ef=50). Uses clustered data because that is what the
    semantic-search demo actually indexes — real text embeddings cluster."""
    vectors, queries = embedding_like_data(n=10_000, dim=64, n_queries=100)
    recall = measure_recall(vectors, queries, metric="cosine", ef=50)
    assert recall >= 0.90, f"recall@10 was {recall:.3f}"


@pytest.mark.slow
def test_recall_latency_dial_increases_with_ef():
    """The recall/latency tradeoff: higher ef yields higher recall, even on the
    adversarial uniform-Gaussian worst case, reaching the target by ef=100."""
    vectors, queries = gaussian_data(n=10_000, dim=64, n_queries=100)
    r50 = measure_recall(vectors, queries, metric="cosine", ef=50)
    r100 = measure_recall(vectors, queries, metric="cosine", ef=100)
    r200 = measure_recall(vectors, queries, metric="cosine", ef=200)
    assert r50 < r100 < r200, f"ef dial not monotonic: {r50:.3f} {r100:.3f} {r200:.3f}"
    assert r100 >= 0.90, f"recall@10 at ef=100 was {r100:.3f}"
