"""Network-free tests for the data-pipeline helpers."""

from scripts import _corpus
from scripts.run_benchmark import RESULTS_KEYS

LONG = "x" * 5 + " a long sentence of real prose that is clearly substantial " * 3


def test_short_and_junk_paragraphs_are_dropped():
    assert not _corpus.is_good_paragraph("too short")
    assert not _corpus.is_good_paragraph("| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |" * 6)
    assert _corpus.is_good_paragraph(LONG)


def test_clean_article_splits_and_filters():
    article = f"short\n\n{LONG}\n\nalso short"
    cleaned = _corpus.clean_article(article)
    assert cleaned == [LONG.strip()]


def test_dedupe_is_case_and_whitespace_insensitive():
    a = "The Quick Brown Fox jumps over things and keeps on going for a while here"
    b = "  the   quick brown fox JUMPS over things and keeps on going for a while here "
    out = list(_corpus.dedupe([a, b, a]))
    assert out == [a]


def test_sample_is_deterministic_for_a_seed():
    pool = [f"paragraph {i}" for i in range(100)]
    first = _corpus.sample(pool, 10, seed=42)
    again = _corpus.sample(pool, 10, seed=42)
    other = _corpus.sample(pool, 10, seed=7)
    assert first == again
    assert first != other
    assert len(first) == 10


def test_corpus_round_trips_through_jsonl(tmp_path):
    rows = _corpus.to_rows(["alpha text here", "beta text here"])
    path = tmp_path / "corpus.jsonl"
    _corpus.save_corpus(path, rows)
    assert _corpus.load_corpus(path) == rows
    assert rows[0] == {"id": 0, "text": "alpha text here"}


def test_results_schema_shape():
    # The shape run_benchmark writes; the frontend depends on these keys.
    example = {
        "dataset": "wikipedia-simple-en",
        "n": 10000,
        "dim": 384,
        "metric": "cosine",
        "k": 10,
        "sweep": [{"ef_search": 50, "recall_at_10": 0.95, "p50_latency_ms": 1.2}],
        "generated_at": "2026-01-01T00:00:00+00:00",
    }
    assert RESULTS_KEYS <= set(example)
    for point in example["sweep"]:
        assert {"ef_search", "recall_at_10", "p50_latency_ms"} <= set(point)
        assert 0.0 <= point["recall_at_10"] <= 1.0
