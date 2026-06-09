# Issue 01 — Deployment + polish

Status: ready-for-agent
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
