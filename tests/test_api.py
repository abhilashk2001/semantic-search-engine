"""API contract tests using a tiny in-process index and a stub embedder.

No model is downloaded: a StubEmbedder maps text -> a deterministic vector in
the index's dimension, so the full request path is exercised without fastembed.
"""

import hashlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.search_service import SearchService
from engine import HNSWIndex

DIM = 8


class StubEmbedder:
    dim = DIM

    def embed(self, texts):
        out = []
        for text in texts:
            seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "big")
            rng = np.random.default_rng(seed)
            out.append(rng.standard_normal(DIM).astype(np.float32))
        return np.asarray(out, dtype=np.float32)


@pytest.fixture
def client():
    rng = np.random.default_rng(0)
    index = HNSWIndex(dim=DIM, metric="cosine", seed=1)
    for i in range(200):
        index.insert(
            rng.standard_normal(DIM).astype(np.float32),
            metadata={"text": f"paragraph number {i}"},
        )
    service = SearchService(index, StubEmbedder(), build_time_ms=12.5)
    with TestClient(create_app(service)) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_text_returns_ranked_results(client):
    resp = client.post("/search", json={"query": "climate change", "k": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 5
    assert body["k"] == 5 and body["ef_search"] == 50
    assert "latency_ms" in body
    # scores sorted descending (higher = more similar)
    scores = [r["score"] for r in body["results"]]
    assert scores == sorted(scores, reverse=True)
    # text metadata flows through
    assert all(r["text"].startswith("paragraph number") for r in body["results"])


def test_search_vector_input(client):
    vec = [0.1] * DIM
    resp = client.post("/search", json={"vector": vec, "k": 3})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 3


def test_search_wrong_vector_dimension_is_400(client):
    resp = client.post("/search", json={"vector": [0.1, 0.2, 0.3]})
    assert resp.status_code == 400
    assert "dimension" in resp.json()["detail"].lower()


def test_search_requires_exactly_one_input(client):
    # both provided
    r1 = client.post("/search", json={"query": "x", "vector": [0.0] * DIM})
    assert r1.status_code == 422
    # neither provided
    r2 = client.post("/search", json={"k": 5})
    assert r2.status_code == 422


def test_search_rejects_out_of_range_params(client):
    assert client.post("/search", json={"query": "x", "k": 0}).status_code == 422
    assert client.post("/search", json={"query": "x", "ef_search": 0}).status_code == 422


def test_stats(client):
    body = client.get("/stats").json()
    assert body["node_count"] == 200
    assert body["build_time_ms"] == 12.5
    assert body["config"]["metric"] == "cosine"
    assert body["config"]["dim"] == DIM
    assert sum(body["layer_distribution"].values()) >= 200  # layer 0 holds all


def test_benchmark_returns_recall_in_unit_interval(client):
    body = client.post("/benchmark", json={"n_queries": 10}).json()
    assert 0.0 <= body["recall_at_k"] <= 1.0
    assert body["n_queries"] == 10
    assert body["sample_latency_ms"] >= 0.0
