# Issue 01 — React demo app

Status: ready-for-agent
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
