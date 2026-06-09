# Issue 01 — Deployment + polish

Status: done
PRD: ../PRD.md
Spec: /project-brief/locked-spec.md (decisions #4, #5, #11)

## Goal

Ship the live demo: backend on Render, frontend on Vercel, CI green, README that explains and sells the project.

## Tasks

- [ ] `.github/workflows/ci.yml` — `uv` install + `pytest` (engine + api) on push/PR.
- [ ] Deploy-step index build: run `download_data.py` + `build_index.py` to produce `index.pkl` (never committed).
- [ ] Render free web service — uvicorn start; build produces artifact; CORS origin = Vercel URL; `/health` healthcheck.
- [ ] Vercel — deploy `web/`; `VITE_API_BASE_URL` → Render URL.
- [ ] README — one-liner, corrected architecture diagram (FastAPI), plain-English HNSW, local-run, live link, benchmark table from `results.json`, "vs brute force" framing, deferred roadmap.
- [ ] Document Render spin-down; optional `/health` uptime pinger.
- [ ] Post-deploy verify: `/health` OK, live `/search` relevant, Vercel app calls backend (CORS), chart renders.

## Acceptance

- Live URL returns relevant results <100ms (excl. cold wake); CI green; README complete; demo link recorded.

## Commit

Branch `phase-6-deploy`; commit when acceptance passes.

## Comments

- Index delivery: user chose build-on-Render. De-risked it by committing `data/corpus.jsonl` (3.6 MB text) so the deploy embeds the committed corpus instead of re-streaming the dataset (no HF rate limits, no `datasets` build dep). Only the `api` extra is needed at build.
- CI (`.github/workflows/ci.yml`): Python (engine + api, fast suite) and web (typecheck + vitest) jobs; green on main.
- Render: `render.yaml` Blueprint, free web service, build embeds corpus → `index.pkl`, start = uvicorn, health check `/health`. Added a `buildFilter` so only backend/data changes trigger a rebuild. Runtime memory measured ~350 MB (fits 512 MB).
- Vercel: `web/vercel.json` (Vite + SPA rewrites), root dir `web`, `VITE_API_BASE_URL` → Render URL. Build-time URL baking verified in the shipped bundle.
- CORS left open (`*`) by user choice.
- Live: demo https://semantic-search-engine-virid.vercel.app · API https://semantic-search-api-223g.onrender.com. Verified `/health`, `/stats`, `/search` on Render and the cross-origin path from Vercel.
- README: full rewrite with plain-English HNSW, architecture, benchmark table, and an honest brute-force-vs-HNSW note (vectorized brute force wins at 10k; HNSW wins asymptotically).
- Honest latency note: Render free CPU gives 2-3 ms warm but spikes to 100-200 ms under contention; the precomputed benchmark chart (real hardware) is the trustworthy curve.
