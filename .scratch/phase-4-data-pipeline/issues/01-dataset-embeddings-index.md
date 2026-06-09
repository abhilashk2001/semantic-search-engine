# Issue 01 — Dataset, embeddings, and artifacts

Status: done
PRD: ../PRD.md
Spec: /project-brief/locked-spec.md (decisions #2, #3, #4, #7, #10)

## Goal

Offline pipeline producing the two shippable artifacts: `index.pkl` and `benchmarks/results.json`.

## Tasks

- [ ] `scripts/download_data.py` — fetch Wikipedia Simple English (HF `datasets`); clean (strip markup, drop <~150 chars, dedupe); seeded deterministic 10k sample → `data/corpus.jsonl` (git-ignored).
- [ ] `scripts/build_index.py` — embed corpus with fastembed `all-MiniLM-L6-v2` (normalized float32); insert into `HNSWIndex` (locked defaults, seeded) with `metadata={"text": ...}`; `save("index.pkl")`; record build time.
- [ ] `scripts/run_benchmark.py` — held-out queries; brute-force top-10 oracle; sweep ~8 `ef_search` points; record recall@10 + p50 latency → `benchmarks/results.json`.
- [ ] Isolate `datasets`/fastembed in an offline dependency group (not API runtime).
- [ ] Light tests: cleaning yields 10k unique ≥-threshold paragraphs (small fixture); `results.json` schema valid, recall in [0,1].

## Acceptance

- Running the scripts produces a loadable `index.pkl` and a schema-valid `results.json`.
- Real-corpus recall@10 ≥ 0.90 (else flip engine to heuristic neighbor selector).

## Commit

Branch `phase-4-data-pipeline`; commit when acceptance passes (artifacts git-ignored).

## Comments

- Scripts: `scripts/_corpus.py` (pure helpers), `download_data.py` (streams `wikimedia/wikipedia` 20231101.simple), `build_index.py`, `run_benchmark.py`. `datasets`/`fastembed` isolated in the `[data]` extra.
- Real run: 10,000 unique clean paragraphs (min 150 / avg 346 chars); embedded with fastembed all-MiniLM-L6-v2; index built in 23.7s; `index.pkl` = 20 MB (git-ignored).
- Benchmark on real embeddings: recall@10 = 0.985 @ ef=10 (0.26ms p50) → 1.000 @ ef=50 (0.84ms). Written to `benchmarks/results.json` (committed).
- End-to-end smoke with the real model returned semantically correct results in ~1–2ms (climate/composers/volcanoes).
- Engine: `build_time_ms` now persisted in the artifact and surfaced via `/stats`. Tests: `test_corpus.py` added; full fast suite 31 passed.
- recall@10 ≥ 0.90 on real data — no need to revisit the neighbor selector.
