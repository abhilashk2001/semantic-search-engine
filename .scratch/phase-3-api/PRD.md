# PRD — Phase 3: FastAPI Demo API

> References `project-brief/locked-spec.md`. Decisions #3 (embeddings), #7 (benchmark), #8 (API surface).

## Problem Statement

The HNSW engine works in-process, but the demo needs it reachable over HTTP so a React frontend
(and recruiters) can query it. A user types English — they must not have to supply a 384-float
vector. I need a small, well-validated REST API that embeds query text server-side, searches the
pre-built index, and reports stats and a live recall check, while staying light enough to run in
512 MB on free-tier hosting.

## Solution

A FastAPI app in `api/` that loads the pre-built `index.pkl` once on startup (decision #4) and
holds a single fastembed model for query-time embedding (decision #3). It exposes a focused
surface: `POST /search` (text-first), `GET /stats`, `POST /benchmark` (small live recall check),
and `GET /health`. Requests and responses are validated with Pydantic. CORS allows the Vercel
frontend origin. Full multi-collection CRUD is deferred (decision #8).

## User Stories

1. As a frontend, I want `POST /search` to accept query *text*, so that users can search in plain
   English without computing embeddings.
2. As a frontend, I want each search result to include the paragraph text, a similarity score, and
   the measured query latency, so that I can render readable, ranked results with a speed badge.
3. As a frontend, I want to pass `k` and `ef_search` to `/search`, so that the sliders change live
   behavior.
4. As an API client, I want `POST /search` to optionally accept a raw vector instead of text, so
   that programmatic callers can bypass embedding.
5. As an API client, I want clear validation errors for wrong vector dimension, empty queries, or
   out-of-range `k`/`ef`, so that misuse fails with a meaningful message.
6. As a frontend, I want `GET /stats` to return node count, per-layer distribution, build time, and
   config (M, ef_construction, metric), so that I can render the stats panel.
7. As a frontend, I want `POST /benchmark` to run a quick recall check over a handful of queries and
   return recall@k, so that the demo can prove results are computed live, not faked.
8. As an uptime pinger / platform, I want `GET /health` to return cheaply, so that wake/health
   checks work.
9. As a server operator, I want the index and embedding model loaded exactly once at startup, so
   that per-request latency stays low and memory stays within 512 MB.
10. As the frontend deployed on Vercel, I want CORS to permit my origin, so that browser calls
    succeed.
11. As a developer, I want startup to fail fast with a clear message if `index.pkl` is missing, so
    that misconfigured deploys are obvious.

## Implementation Decisions

- **Modules built:** `api/main.py` (app + lifespan startup), `api/schemas.py` (Pydantic models),
  `api/embedding.py` (fastembed wrapper), `api/search_service.py` (thin layer over `HNSWIndex`).
- **Startup (lifespan):** load `index.pkl` via `HNSWIndex.load`; instantiate fastembed
  `all-MiniLM-L6-v2`; record load/build-time metadata for `/stats`. Fail fast if artifact absent.
- **`POST /search` contract:** body `{query?: str, vector?: float[], k: int=10, ef_search: int=50}`;
  exactly one of `query`/`vector` required. Response `{results: [{text, score, id}], latency_ms,
  k, ef_search}`. `score` is similarity (1 − distance for cosine) so higher = better in the UI.
- **`GET /stats` contract:** `{node_count, layer_distribution, build_time_ms, config: {M,
  ef_construction, metric, dim}}`.
- **`POST /benchmark` contract:** body `{n_queries?: int}` (small, capped); response
  `{recall_at_k, k, n_queries, sample_latency_ms}`. Ground truth computed by in-process brute force
  over the loaded vectors for the sampled queries only (kept small per decision #7).
- **Embedding:** single shared fastembed instance; query text → 384-dim float32, normalized to
  match the engine's cosine convention.
- **CORS:** allowed origin configurable via env (the Vercel URL); `*` permitted in local dev.
- **Deps:** `fastapi`, `uvicorn`, `pydantic`, `fastembed`, `numpy`, `engine` (local). No torch.

## Testing Decisions

- **What makes a good test:** asserts the API's external contract — status codes, response shape,
  validation errors — via FastAPI's `TestClient`, against a tiny fixture index built in-process
  (not the real 10k artifact).
- **Modules tested:** `api/main.py` routes and `api/schemas.py` validation.
- **Core tests:** `/search` with text returns ranked results of the right shape; `/search` with a
  wrong-dimension vector returns a 422/400 with a clear message; `/stats` returns the expected
  keys; `/benchmark` returns a recall value in [0,1]; `/health` returns OK. Build the fixture index
  with the Phase 1 engine + a stubbed/tiny embedder to avoid downloading the model in unit tests.
- **Prior art:** seeded-fixture pattern from Phase 1; standard FastAPI `TestClient` usage.

## Out of Scope

- Multi-collection CRUD (`POST /collections`, per-collection vectors, `DELETE`) — roadmap.
- The real dataset and `index.pkl` production (Phase 4), the frontend (Phase 5), deployment (Phase 6).

## Further Notes

- The live recall-check (`/benchmark`) is intentionally small; the full recall-vs-latency curve is
  precomputed offline (Phase 4) and rendered from static JSON, never recomputed live.
- Keep the embedding model load off the import path (do it in lifespan) so tests can run without it.
