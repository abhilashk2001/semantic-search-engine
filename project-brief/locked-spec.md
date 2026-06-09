# VecLite — Locked Spec (source of truth)

This document records the decisions resolved during the planning interview. Every phase PRD
under `.scratch/` references these decisions. If a decision changes, change it here first.

## Win condition

A **full, cohesive project shipped fast** with a **live demo link**. Depth-of-algorithm study
is deferred to later. The from-scratch HNSW engine is the substance; the API + React app are its
packaging. Build them together, not as separate halves.

## Locked decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Goal | Full project, shipped fast, live demo link is the #1 deliverable. |
| 2 | Live dataset size | **10,000** vectors served live; architecture scales to 80k+; larger N benchmarked locally only. |
| 3 | Embeddings | **fastembed (ONNX `all-MiniLM-L6-v2`, 384-dim)** for BOTH corpus ingest and query time. No torch on the server. Same model both sides (non-negotiable — query and corpus must share the embedding space). |
| 4 | Index lifecycle | **Pre-build offline, ship a serialized artifact, load on boot.** Server boot = `HNSWIndex.load("index.pkl")` (sub-second). fastembed used at runtime only to embed the single incoming query. Artifact built in the deploy step, not committed. |
| 5 | Repo + deploy | **Monorepo** (`engine/`, `api/`, `web/`, `scripts/`, `benchmarks/`). Backend → **Render free web service**. Frontend → **Vercel**. CORS configured. Free-tier spin-down accepted. |
| 6 | Engine algorithm | All 3 metrics (cosine, dot, L2). Demo path = **cosine via normalize-on-insert + dot-product internally**. **Simple neighbor-selection first**, heuristic (Malkov `SELECT-NEIGHBORS-HEURISTIC`) kept behind same interface as fallback if recall@10 < 0.90. Defaults: `M=16`, `M_max0=32`, `ef_construction=200`, `ef_search=50`, `mL=1/ln(M)`. **Seeded RNG** for reproducible builds. |
| 7 | Benchmark | **Precompute the recall-vs-latency curve offline → static `benchmarks/results.json`** rendered by the frontend. Plus a **small live `POST /benchmark`** recall check (a few queries) to prove it's real. Live `ef_search` slider does real single-query searches. |
| 8 | API surface | **Focused demo API**: `POST /search` (text-first, vector optional), `GET /stats`, `POST /benchmark`, `GET /health`. Pydantic validation. Full multi-collection CRUD **deferred to roadmap** (engine stays multi-collection-capable internally). |
| 9 | Frontend | **Vite + React + TS + Tailwind**, dark single responsive page, plain `fetch` + one API-client module (no Redux/TanStack). Components: SearchBar, ResultsList, Controls (ef_search 10–200 + k 1–20, debounced), BenchmarkChart (Recharts from static JSON + live recall button), StatsPanel, "Surprise me". **t-SNE deferred.** |
| 10 | Dataset | **Wikipedia Simple English** via HF `datasets`, pulled **offline only**. **10k seeded clean sample** (drop <~150 char paragraphs, strip markup, dedupe). Paragraph text stored as node metadata. |
| 11 | Tooling | **`uv`** deps + lockfile. **`pytest`** engine tests: recall@10 ≥ 0.90 vs NumPy brute force, and save→load round-trip identity. **GitHub Actions**: pytest on push, build `index.pkl` on deploy. |

## Phase map

| Phase | Slug | Delivers |
|-------|------|----------|
| 1 | `phase-1-hnsw-engine` | Pure-Python HNSW engine + recall test. |
| 2 | `phase-2-persistence` | `save`/`load` (pickle) + round-trip test. |
| 3 | `phase-3-api` | FastAPI demo API (`/search`, `/stats`, `/benchmark`, `/health`). |
| 4 | `phase-4-data-pipeline` | Offline data + embeddings + `index.pkl` + `results.json`. |
| 5 | `phase-5-web-demo` | React/Tailwind demo app. |
| 6 | `phase-6-deploy` | Render + Vercel deploy, CI, README, benchmark table. |

## Workflow

Per phase: read PRD → the phase issue (`ready-for-agent`) → code on a feature branch → commit →
move to next phase. One PRD and one issue per phase.

## Definition of done (from brief)

Live URL returns relevant results <100ms; README explains HNSW in plain English; the
`ef_construction`/`ef_search` distinction, layer probability, and recall/latency tradeoff are
explainable; the benchmark chart makes the tradeoff tangible; clean commit history.
