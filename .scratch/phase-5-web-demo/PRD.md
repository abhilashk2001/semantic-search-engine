# PRD — Phase 5: React Demo App

> References `project-brief/locked-spec.md`. Decisions #5 (deploy topology), #7 (benchmark), #9 (frontend).

## Problem Statement

The engine and API exist, but the project's #1 deliverable is a *live demo link a recruiter can
click and immediately understand*. There is no UI yet. I need a clean, fast single-page app where a
non-technical visitor types a phrase and sees semantically relevant Wikipedia paragraphs in
milliseconds, can feel the recall/latency tradeoff by moving a slider, and can see the index's
internals — all without reading any code.

## Solution

A Vite + React + TypeScript single-page app in `web/`, styled with Tailwind in a dark theme that
screenshots well (decision #9). It calls the FastAPI backend through one thin `fetch`-based API
client. Features: a search bar, a results list with similarity scores and a live latency badge,
`ef_search`/`k` sliders that re-run search live (debounced), a Recharts recall-vs-latency curve
rendered from the precomputed `results.json`, an index stats panel, and a "Surprise me" button.
The t-SNE visualization is deferred.

## User Stories

1. As a visitor, I want a prominent search box, so that I can type a phrase and search immediately.
2. As a visitor, I want the top-k results shown as readable paragraphs with a similarity score, so
   that I can judge relevance at a glance.
3. As a visitor, I want each search to show how fast it ran (e.g. "found in 3.2 ms"), so that the
   speed of HNSW is tangible.
4. As a curious visitor, I want an `ef_search` slider (10–200), so that I can trade latency for
   recall and watch results/speed change live.
5. As a curious visitor, I want a `k` slider (1–20), so that I can control how many results return.
6. As a visitor, I want slider changes to re-run the search automatically but debounced, so that
   dragging feels live without hammering the server.
7. As an analytical visitor, I want a recall-vs-latency chart, so that I can see the core HNSW
   tradeoff as a curve.
8. As an analytical visitor, I want a "run live recall check" button on the chart, so that I can
   confirm the numbers are computed, not faked.
9. As a curious visitor, I want an index stats panel (total vectors, layer distribution, build
   time, config), so that I can see what's under the hood.
10. As a visitor who doesn't know what to type, I want a "Surprise me" button, so that it picks a
    random paragraph and searches its neighbors.
11. As a mobile visitor, I want the page to be responsive and dark-themed, so that it looks good on
    any device and in screenshots.
12. As a developer, I want all backend calls funneled through one API-client module with a
    configurable base URL, so that pointing at local vs deployed backend is a one-line change.
13. As a visitor on a cold backend, I want a graceful loading/wake state, so that free-tier
    spin-down doesn't show a broken page.

## Implementation Decisions

- **Stack:** Vite + React + TypeScript + Tailwind; Recharts for the chart; plain `fetch`, no Redux/
  TanStack. State via hooks.
- **Modules built:** `web/src/api.ts` (typed client: `search`, `stats`, `benchmark`, base URL from
  env), and components `SearchBar`, `ResultsList`, `Controls`, `BenchmarkChart`, `StatsPanel`,
  `SurpriseButton`, composed in `App.tsx`.
- **Search flow:** `SearchBar` + `Controls` state → debounced call to `api.search({query, k,
  ef_search})` → `ResultsList` renders `{text, score}` + latency badge.
- **Chart:** `BenchmarkChart` imports/fetches the static `results.json` (copied into `web/` build
  or fetched from a known path) and plots recall@10 vs p50 latency across the `ef_search` sweep; a
  button calls `POST /benchmark` for the live recall value.
- **Surprise me:** requests a random corpus paragraph (via a stats/sample affordance or a fixed
  client list) and searches its text.
- **Config:** `VITE_API_BASE_URL` env var selects backend; defaults to localhost in dev.
- **Cold-start UX:** show a "waking the server…" state on first request timeout/retry.

## Testing Decisions

- **What makes a good test:** component tests assert user-visible behavior — typing then results
  render, slider change triggers a (mocked) search — not internal state. Backend is mocked at the
  `api.ts` boundary.
- **Modules tested:** `api.ts` (request shape) and the search/results interaction, using Vitest +
  React Testing Library with `fetch` mocked.
- **Core tests:** typing a query and submitting calls `api.search` with the right payload and
  renders returned results; moving the `ef_search` slider re-issues a debounced search; the chart
  renders points from a fixture `results.json`.
- **Prior art:** none in-repo; establishes the frontend test pattern.

## Out of Scope

- t-SNE / 2D vector visualization (roadmap), deployment (Phase 6), auth, multi-collection UI.

## Further Notes

- The full recall-vs-latency curve is static (Phase 4 `results.json`); only the single-query slider
  and the small recall-check button hit the backend live (decision #7).
- Keep the design minimal and high-contrast — this page is what a recruiter screenshots.
