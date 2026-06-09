# Issue 01 — FastAPI demo API

Status: done
PRD: ../PRD.md
Spec: /project-brief/locked-spec.md (decisions #3, #7, #8)

## Goal

Expose the engine over a focused, validated REST API that embeds query text server-side and loads the pre-built index once on boot.

## Tasks

- [ ] `api/embedding.py` — shared fastembed `all-MiniLM-L6-v2` wrapper; text → normalized 384-dim float32.
- [ ] `api/schemas.py` — Pydantic models for search/stats/benchmark request + response.
- [ ] `api/search_service.py` — thin layer over `HNSWIndex` (search, stats, live recall check).
- [ ] `api/main.py` — FastAPI app:
  - [ ] lifespan startup: `HNSWIndex.load(index.pkl)` + fastembed init; fail fast if artifact missing
  - [ ] `POST /search` (text-first, vector optional; `k`, `ef_search`; returns text+score+latency_ms)
  - [ ] `GET /stats` (node_count, layer_distribution, build_time_ms, config)
  - [ ] `POST /benchmark` (small live recall check, brute-force oracle over loaded vectors)
  - [ ] `GET /health`
  - [ ] CORS via env-configurable origin
- [ ] Tests via `TestClient` against a tiny in-process fixture index + stub embedder.

## Acceptance

- `pytest` green; `/search` text path returns ranked results; bad vector dim → 422/400; `/stats`, `/benchmark`, `/health` shapes correct.
- No torch in deps; model loads in lifespan, not at import.

## Commit

Branch `phase-3-api`; commit when acceptance passes.

## Comments

- Built `api/embedding.py` (fastembed wrapper, imported lazily so it never loads in tests), `api/schemas.py` (Pydantic v2), `api/search_service.py` (HTTP-free service over the engine), `api/main.py` (app + injectable lifespan).
- `create_app(service=None)`: prod loads `index.pkl` + fastembed on startup; tests inject a `SearchService` with a `StubEmbedder`, so unit tests download no model.
- `/search` is text-first with a raw-vector fallback; exactly-one-input enforced by a Pydantic `model_validator`; wrong vector dim → 400; out-of-range k/ef → 422. `/stats`, `/benchmark` (small live recall check), `/health` complete the surface. CORS origins via `VECLITE_CORS_ORIGINS`.
- Deps split: `[api]` (fastapi, uvicorn, fastembed) vs `[dev]` (pytest, fastapi, httpx). No torch.
- Tests: 8 API contract tests; full fast suite 25 passed.
