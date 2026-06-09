# Issue 01 — Dataset, embeddings, and artifacts

Status: ready-for-agent
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
