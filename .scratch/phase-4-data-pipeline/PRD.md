# PRD — Phase 4: Dataset + Embeddings + Artifacts

> References `project-brief/locked-spec.md`. Decisions #2 (size), #3 (embeddings), #4 (artifact), #7 (benchmark), #10 (dataset).

## Problem Statement

The engine and API are generic, but the live demo needs real, human-readable content to search and
a trustworthy benchmark curve to display. I need an offline pipeline that turns Wikipedia text into
a clean 10k-paragraph corpus, embeds it with the same model the API uses at query time, builds the
HNSW index, and produces the two shippable artifacts: `index.pkl` and `benchmarks/results.json`.
None of this may run on the live server (decision #4) or bloat its memory.

## Solution

Offline scripts in `scripts/` that run on a developer machine / CI: `download_data.py` fetches and
cleans a deterministic 10k sample of Wikipedia Simple English; `build_index.py` embeds it with
fastembed and builds + `save`s `index.pkl` (paragraph text stored as node metadata); and
`run_benchmark.py` sweeps `ef_search`, computes recall@10 vs brute force and p50 latency on real
hardware, and writes `benchmarks/results.json`. HF `datasets` and any heavy deps stay confined to
these offline scripts and never enter the API runtime.

## User Stories

1. As a pipeline operator, I want `download_data.py` to fetch Wikipedia Simple English via HF
   `datasets`, so that I have real text to search.
2. As a pipeline operator, I want the sample to be a deterministic 10k paragraphs (seeded), so that
   the artifact is reproducible.
3. As a search-quality owner, I want short (<~150 char) paragraphs, markup, and duplicates filtered
   out, so that results look clean and relevant.
4. As a pipeline operator, I want `build_index.py` to embed the corpus with fastembed
   `all-MiniLM-L6-v2`, so that corpus and query vectors share one embedding space (decision #3).
5. As a pipeline operator, I want each paragraph's text stored as node metadata, so that loaded
   search results are human-readable with no separate lookup.
6. As a deploy pipeline, I want `build_index.py` to `save` a single `index.pkl` artifact, so that
   the API boots by loading it.
7. As a demo owner, I want `run_benchmark.py` to sweep `ef_search` (~8 points) and record recall@10
   and p50 latency on real hardware, so that the frontend chart is accurate and flattering.
8. As a demo owner, I want benchmark results written to `benchmarks/results.json` in a stable shape,
   so that the frontend renders the curve from static data without recomputation.
9. As a README author, I want the benchmark runnable at larger N locally, so that I can publish
   scale numbers beyond the 10k live set (decision #2).
10. As a server operator, I want HF `datasets` / heavy deps isolated to `scripts/`, so that the API
    image stays within 512 MB.

## Implementation Decisions

- **Modules built:** `scripts/download_data.py`, `scripts/build_index.py`,
  `scripts/run_benchmark.py`. Optional shared `scripts/_corpus.py` for load/clean helpers.
- **Corpus:** Wikipedia Simple English; deterministic seeded sample to exactly 10k post-filter;
  cleaning = strip markup/whitespace, drop <~150 chars, dedupe on normalized text. Output a
  cleaned corpus file (e.g. JSONL of `{id, text}`) under `data/` (git-ignored).
- **Embedding:** fastembed `all-MiniLM-L6-v2`, batched; vectors float32, normalized (cosine
  convention). Same wrapper concept as `api/embedding.py` to guarantee parity.
- **Index build:** insert all 10k into `HNSWIndex` with locked defaults (M=16, ef_construction=200,
  seeded), `metadata={"text": ...}`; `save("index.pkl")`. Record build time for `/stats`.
- **Benchmark:** held-out query set; brute-force top-10 oracle (NumPy) per query; for each
  `ef_search` in the sweep, measure recall@10 and p50 latency over the query set; write
  `benchmarks/results.json` = `{dataset, n, dim, metric, sweep: [{ef_search, recall_at_10,
  p50_latency_ms}], generated_at}`.
- **Dep isolation:** `datasets` and fastembed used here; declared in a scripts/offline dependency
  group, not the API runtime group.

## Testing Decisions

- **What makes a good test:** validates artifact *shape and integrity*, not exact floating values.
- **Modules tested:** lightly — cleaning helpers and artifact schema.
- **Core checks:** cleaning produces exactly 10k unique paragraphs all ≥ threshold length (run on a
  small fixture, not the full download); `results.json` conforms to the agreed schema and recall
  values lie in [0,1] and are non-decreasing as `ef_search` grows (sanity, with tolerance). The
  full download + build is an operational script run, not a unit test.
- **Prior art:** brute-force oracle reused from Phase 1; `save`/`load` from Phase 2.

## Out of Scope

- The API (Phase 3, done), the frontend chart rendering (Phase 5), deployment/CI wiring (Phase 6),
  and any non-Wikipedia datasets.

## Further Notes

- `index.pkl` and `data/` are git-ignored; the artifact is rebuilt in the deploy step (decision #4).
- Sanity-check recall@10 ≥ 0.90 on the real corpus here; if it underperforms, flip the engine's
  neighbor selector to the heuristic (Phase 1 interface already supports it).
