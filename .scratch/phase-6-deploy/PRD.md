# PRD — Phase 6: Deployment + Polish

> References `project-brief/locked-spec.md`. Decisions #4 (artifact in deploy step), #5 (Render+Vercel), #11 (CI).

## Problem Statement

Everything works locally, but the project's whole point is a **live URL a recruiter can click**.
Nothing is deployed, there's no CI, and there's no README that explains what HNSW is or what was
built. I need the backend live on Render, the frontend live on Vercel, the index artifact built
reproducibly in the deploy step (not committed), and documentation that makes the project legible
and impressive to both engineers and non-technical readers.

## Solution

Wire up deployment and documentation. A GitHub Actions workflow runs pytest on push and builds the
`index.pkl` artifact during deploy (decision #4). The FastAPI backend deploys to a Render free web
service (loading that artifact on boot); the React app deploys to Vercel pointed at the Render URL
via env. A README ties it together: one-liner, architecture diagram, plain-English HNSW
explanation, local run instructions, the live demo link, and a benchmark table generated from
`results.json`. Free-tier spin-down is documented and optionally mitigated with a pinger.

## User Stories

1. As a recruiter, I want a single live URL, so that I can type a phrase and get relevant results
   in under 100 ms (excluding cold wake).
2. As a maintainer, I want GitHub Actions to run pytest on every push, so that regressions are
   caught.
3. As a deploy pipeline, I want `index.pkl` built in the deploy step from the corpus, so that no
   binary artifact is committed and the artifact is reproducible (decision #4).
4. As a deploy pipeline, I want the FastAPI backend running on Render free tier with the artifact
   loaded on boot, so that the API is publicly reachable.
5. As a deploy pipeline, I want the React app on Vercel configured with the Render backend URL, so
   that the frontend talks to the live API.
6. As a security-minded maintainer, I want CORS locked to the Vercel origin in production, so that
   the API isn't open to arbitrary origins.
7. As a reader, I want a README with a one-liner, architecture diagram, and plain-English HNSW
   explanation, so that I understand the project without reading code.
8. As an engineer reader, I want a benchmark table (recall@10 + latency at several `ef_search`
   values) and "vs brute force" framing, so that I can see exactly what the index buys.
9. As a visitor hitting a slept backend, I want documented expectations (and optionally a pinger),
   so that the cold-start delay isn't mistaken for a broken demo.
10. As a future-me, I want the deferred roadmap (multi-collection CRUD, t-SNE, delete, filtering)
    listed, so that the project's growth path is clear.
11. As a hiring reviewer, I want a clean commit history across phases, so that the build story reads
    well.

## Implementation Decisions

- **CI:** `.github/workflows/ci.yml` — job 1: `uv` install + `pytest` (engine + api) on push/PR.
  Deploy-time index build runs either in a CI job or Render's build command (`scripts/download_data.py`
  + `scripts/build_index.py`) so `index.pkl` is produced fresh, never committed.
- **Backend deploy (Render):** free web service; start command runs uvicorn; build command produces
  `index.pkl`; env vars set the allowed CORS origin (Vercel URL). Health check on `GET /health`.
- **Frontend deploy (Vercel):** build the `web/` app; `VITE_API_BASE_URL` set to the Render URL.
- **README:** one-liner, architecture diagram (reuse brief's, corrected to FastAPI), plain-English
  HNSW section, local-run instructions (engine, api, web), live demo link, benchmark table
  rendered from `benchmarks/results.json`, "vs brute force" framing, deferred roadmap.
- **Spin-down note:** document Render free-tier sleep; optionally add a free uptime pinger hitting
  `/health`.

## Testing Decisions

- **What makes a good test:** deployment is validated by *observation*, not unit tests — the CI
  pytest gate already covers code; here we verify the live endpoints behave.
- **Verification steps:** after deploy, `GET /health` returns OK; `POST /search` on the live URL
  returns relevant results; the Vercel app loads and successfully calls the Render backend
  (CORS works); the benchmark chart renders. Record the live demo URL in the README.
- **Prior art:** the `/verify` and `/run` skills can drive a live check post-deploy.

## Out of Scope

- Paid hosting / autoscaling, custom domains, multi-collection CRUD, t-SNE, node deletion, metadata
  filtering (all roadmap), and any non-free infrastructure.

## Further Notes

- This phase closes the Definition of Done in `locked-spec.md`. After it, the deferred roadmap items
  become candidate follow-up issues.
- Keep secrets (any keys) in platform env settings, never in the repo.
