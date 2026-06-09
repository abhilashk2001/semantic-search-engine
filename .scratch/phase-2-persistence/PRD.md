# PRD — Phase 2: Index Persistence

> References `project-brief/locked-spec.md`. Decisions #4 (index lifecycle), #11 (tooling).

## Problem Statement

Building a 10k-vector index requires embedding every paragraph and constructing the graph — too
slow to do on every server cold start (decision #4). On free-tier hosting that re-build would make
the first visitor wait minutes or time out, killing the live demo. I need to build the index once,
offline, then load a ready-made graph on boot in sub-second time.

## Solution

Add `save(filepath)` and `load(filepath)` to the engine. `save` serializes the entire index state
— vectors, per-layer connections, entry point, config, and node metadata (the paragraph text) —
to disk via `pickle`. `load` reconstructs an index that returns *identical* search results to the
in-memory original. This turns persistence into the load-bearing mechanism behind the demo's fast
boot, not a checkbox.

## User Stories

1. As a deploy pipeline, I want `save(path)` to write the full index to one file, so that I can
   produce a shippable `index.pkl` artifact offline.
2. As a server process, I want `load(path)` to restore an index in sub-second time, so that cold
   starts are fast and never re-embed.
3. As a quality gate, I want a loaded index to return byte-identical results to the in-memory one
   for the same queries, so that persistence is provably lossless.
4. As a deploy pipeline, I want the serialized artifact to include node metadata (paragraph text),
   so that loaded search results are human-readable without a separate data file.
5. As a server process, I want `load` to restore the exact config (M, ef_construction, metric,
   dim, seed), so that the index behaves identically post-load.
6. As a developer, I want a clear error when loading a missing or corrupt file, so that boot
   failures are diagnosable.
7. As a developer, I want the artifact format version-tagged, so that future format changes fail
   loudly instead of silently mis-loading.

## Implementation Decisions

- **Modules modified:** `engine/hnsw.py` gains `save(self, filepath)` and classmethod
  `load(cls, filepath) -> HNSWIndex`.
- **Format:** `pickle` of a plain dict capturing `{format_version, config, nodes, connections,
  entry_point_id, metadata}` — not the live object graph directly, to keep it inspectable and
  version-tolerant. NumPy arrays pickle natively.
- **Determinism:** the RNG seed is stored so a loaded index that receives further inserts behaves
  reproducibly.
- **No new runtime deps:** `pickle` is stdlib; the engine still depends only on `numpy`.

## Testing Decisions

- **What makes a good test:** asserts external behavior — same query → same `(id, distance, order)`
  before and after a save/load round-trip — not the pickle byte layout.
- **Modules tested:** `engine/hnsw.py` persistence path.
- **Core test:** build a small seeded index, run a set of queries, `save` to a temp path, `load`
  into a fresh object, re-run the same queries, assert identical results (ids, distances, ranking)
  and identical config/metadata. Add a negative test: loading a missing path raises a clear error.
- **Prior art:** reuses the seeded-fixture + query pattern established in Phase 1 tests.

## Out of Scope

- The offline script that *uses* `save` to produce the shipped `index.pkl` (Phase 4), any API
  (Phase 3), incremental/append persistence, and alternative formats (JSON, custom binary).

## Further Notes

- `pickle` is acceptable because we control both writer and reader (same codebase, CI-built
  artifact); it is never loaded from untrusted input.
- Keep `save`/`load` symmetric and small — they are exercised directly by Phase 4's build step and
  Phase 3's server boot.
