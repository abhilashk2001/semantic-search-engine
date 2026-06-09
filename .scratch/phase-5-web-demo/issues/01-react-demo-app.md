# Issue 01 — React demo app

Status: done
PRD: ../PRD.md
Spec: /project-brief/locked-spec.md (decisions #5, #7, #9)

## Goal

A clean, dark, single-page React app that makes the live semantic search demo land in 10 seconds.

## Tasks

- [ ] Scaffold `web/` — Vite + React + TS + Tailwind; dark theme; responsive single page.
- [ ] `web/src/api.ts` — typed client (`search`, `stats`, `benchmark`), base URL from `VITE_API_BASE_URL`.
- [ ] `SearchBar` — text input → `api.search`.
- [ ] `ResultsList` — top-k paragraphs + similarity score + "found in X ms" badge.
- [ ] `Controls` — `ef_search` (10–200) + `k` (1–20) sliders; debounced live re-search.
- [ ] `BenchmarkChart` — Recharts curve from static `results.json`; "run live recall check" button → `POST /benchmark`.
- [ ] `StatsPanel` — node count, layer distribution, build time, config from `GET /stats`.
- [ ] `SurpriseButton` — random paragraph → search its neighbors.
- [ ] Cold-start "waking the server…" state.
- [ ] Vitest + RTL tests (fetch mocked): query→results render; slider→debounced search; chart renders from fixture.

## Acceptance

- App runs against local backend; search, sliders, chart, stats, surprise all work; tests green.

## Commit

Branch `phase-5-web-demo`; commit when acceptance passes.

## Comments

- Scaffolded `web/` (Vite 6 + React 18 + TS + Tailwind v4 via `@tailwindcss/vite`), dark single page.
- `src/api.ts` typed client (base URL from `VITE_API_BASE_URL`); components SearchBar, Controls (ef/k sliders), ResultsList (score bars + latency badge), StatsPanel (layer distribution bars), BenchmarkChart (Recharts from static `results.json` + live recall button), SurpriseButton. App wires debounced live search + cold-start "waking" state.
- Benchmark JSON: `web/src/data/results.json` committed; `sync:benchmark` npm prebuild/predev script re-copies from `../benchmarks` so it stays fresh. Chart renders statically even when the backend is asleep.
- Surprise me: picks from a curated example-query list (no backend `/sample` endpoint needed) — a small, documented deviation from "random paragraph".
- Tests: 6 vitest/RTL (api payload + error, App stats render, type→search, slider→debounced re-search, chart render). Typecheck clean; production build OK (158 KB gzip).
- Live integration verified: backend on real index.pkl, dev server boots, CORS preflight + cross-origin POST /search succeed with correct results in ~1ms.
