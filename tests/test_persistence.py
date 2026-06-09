"""Round-trip tests: a loaded index must behave identically to the original."""

import numpy as np
import pytest

from engine import HNSWIndex


def build_index(n=300, dim=16, seed=7):
    rng = np.random.default_rng(seed)
    index = HNSWIndex(dim=dim, metric="cosine", M=16, ef_construction=200, seed=42)
    for i in range(n):
        index.insert(rng.standard_normal(dim).astype(np.float32), metadata={"i": i})
    queries = rng.standard_normal((20, dim)).astype(np.float32)
    return index, queries


def test_round_trip_identical_results(tmp_path):
    index, queries = build_index()
    path = tmp_path / "index.pkl"
    index.save(path)
    loaded = HNSWIndex.load(path)

    # Config preserved.
    assert (loaded.dim, loaded.metric, loaded.M, loaded.ef_construction) == (
        index.dim,
        index.metric,
        index.M,
        index.ef_construction,
    )
    assert loaded.node_count == index.node_count

    # Same queries -> identical ids, distances, ranking, and metadata.
    for q in queries:
        before = index.search(q, k=10, ef=50)
        after = loaded.search(q, k=10, ef=50)
        assert [r[0] for r in before] == [r[0] for r in after]
        assert [r[1] for r in before] == [r[1] for r in after]
        assert [r[2] for r in before] == [r[2] for r in after]


def test_metadata_survives_round_trip(tmp_path):
    index, _ = build_index(n=50)
    path = tmp_path / "index.pkl"
    index.save(path)
    loaded = HNSWIndex.load(path)
    assert loaded.nodes[0].metadata == {"i": 0}
    assert loaded.nodes[49].metadata == {"i": 49}


def test_inserts_continue_reproducibly_after_load(tmp_path):
    """RNG state is preserved, so post-load inserts match an uninterrupted build."""
    index, _ = build_index(n=100)
    path = tmp_path / "index.pkl"
    index.save(path)
    loaded = HNSWIndex.load(path)

    rng = np.random.default_rng(999)
    extra = rng.standard_normal((10, 16)).astype(np.float32)
    a = [index.insert(v, metadata={"x": True}) for v in extra]
    b = [loaded.insert(v, metadata={"x": True}) for v in extra]
    assert a == b

    q = rng.standard_normal(16).astype(np.float32)
    assert index.search(q, k=5) == loaded.search(q, k=5)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        HNSWIndex.load(tmp_path / "does-not-exist.pkl")


def test_load_corrupt_file_raises(tmp_path):
    bad = tmp_path / "bad.pkl"
    bad.write_bytes(b"not a pickle")
    with pytest.raises(ValueError):
        HNSWIndex.load(bad)


def test_load_rejects_wrong_format_version(tmp_path):
    import pickle

    path = tmp_path / "wrong.pkl"
    with open(path, "wb") as fh:
        pickle.dump({"format_version": 999}, fh)
    with pytest.raises(ValueError, match="format version"):
        HNSWIndex.load(path)
