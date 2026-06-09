# PRD — Phase 1: Core HNSW Engine

> References `project-brief/locked-spec.md`. Decisions #6 (engine algorithm), #11 (tooling).

## Problem Statement

I want to perform semantic similarity search over a large vector collection, but exact (brute
force) k-NN compares the query against every vector — O(N×D) — which is too slow at scale. I need
an approximate nearest-neighbor index that finds the top-k closest vectors in roughly O(log N),
implemented from scratch (no vector-search libraries) so the core is genuinely mine to own and
explain. Nothing exists yet — this phase builds the algorithm itself, with no API and no demo.

## Solution

A pure-Python `engine/` package implementing the Hierarchical Navigable Small World (HNSW)
algorithm over NumPy `float32` vectors. It exposes an `HNSWIndex` with `insert` and `search`, a
`distance` module (cosine, dot, L2), exponential layer assignment, and greedy beam search per
layer. Correctness is proven by a recall test against a NumPy brute-force baseline. The package
has zero web or embedding dependencies so it stays independently testable and ownable.

## User Stories

1. As an engine consumer, I want to construct an `HNSWIndex` with configurable `M`,
   `ef_construction`, and a distance metric, so that I can tune the build for my data.
2. As an engine consumer, I want to `insert(vector, metadata)` a node, so that the vector becomes
   searchable and its metadata (e.g. source text) travels with it.
3. As an engine consumer, I want each inserted vector validated for correct dimensionality and
   dtype, so that malformed input fails loudly rather than corrupting the graph.
4. As an engine consumer, I want `search(query, k, ef)` to return the top-k nearest nodes with
   their distances and metadata, so that I can rank results.
5. As an engine consumer, I want to choose cosine, dot-product, or L2 distance, so that I can
   match the geometry of my embedding space.
6. As a text-search user, I want cosine to be the default behavior, so that text embeddings are
   compared by angle (normalize-on-insert, dot-product internally).
7. As an engine maintainer, I want layer assignment sampled from an exponential distribution
   (`mL = 1/ln(M)`), so that most nodes live at layer 0 and a few reach higher layers.
8. As an engine maintainer, I want greedy beam search within a single layer
   (`_search_layer(query, entry_points, ef, layer)`), so that multi-layer search composes from it.
9. As an engine maintainer, I want neighbor selection behind one interface with a simple
   "M-closest" implementation first and a heuristic variant available, so that I can swap to the
   heuristic if recall is insufficient without changing call sites.
10. As an engine maintainer, I want layer-0 to allow up to `M_max0 = 2*M` connections, so that the
    densest layer has enough connectivity for good recall.
11. As an engine maintainer, I want a seeded RNG, so that builds are reproducible and benchmarks
    are deterministic.
12. As a quality gate, I want a recall@k measurement comparing HNSW results to NumPy brute force,
    so that I can prove the index is correct.
13. As a quality gate, I want recall@10 ≥ 0.90 on a 10,000-vector test set with default
    parameters, so that Phase 1 has an objective completion check.
14. As a developer, I want the engine to have no FastAPI/fastembed imports, so that it stays a
    clean, standalone, ownable core.

## Implementation Decisions

- **Modules built:** `engine/distance.py`, `engine/node.py`, `engine/hnsw.py`, `engine/__init__.py`.
- **`Node`**: holds `id`, `vector` (`np.ndarray` float32), `metadata` (dict), and per-layer
  connections (`dict[int, set[node_id]]`). Vectors are normalized on insert when the metric is
  cosine.
- **`HNSWIndex`** public interface: `__init__(dim, metric="cosine", M=16, ef_construction=200, seed=...)`,
  `insert(vector, metadata=None) -> id`, `search(query, k=10, ef=50) -> list[(id, distance, metadata)]`,
  plus read-only properties for node count and per-layer counts (consumed by Phase 3 `/stats`).
- **Internal methods:** `_search_layer(query, entry_points, ef, layer)` (greedy beam search using a
  candidate min-heap and a results max-heap), `_select_neighbors(candidates, M)` (simple variant
  default; heuristic variant behind same signature).
- **Distance contract:** all metrics return a value where **smaller = closer** so search logic is
  metric-agnostic. Cosine = `1 - dot(unit_a, unit_b)`; dot = `-dot(a,b)`; L2 = squared euclidean.
- **Layer assignment:** `floor(-ln(U) * mL)` with `mL = 1/ln(M)`, drawn from the seeded RNG.
- **Defaults:** `M=16`, `M_max0=32`, `ef_construction=200`, `ef_search=50` (search default).
- **Multi-collection-capable:** the index is a single collection; nothing precludes Phase 3+ from
  holding several `HNSWIndex` instances (CRUD deferred per decision #8).
- **Tooling:** `uv` project; engine depends only on `numpy`.

## Testing Decisions

- **What makes a good test:** asserts external behavior — that `search` returns the correct
  neighbors — not internal graph shape. We do not assert specific edges or layer membership.
- **Modules tested:** `engine/hnsw.py` and `engine/distance.py` via `tests/`.
- **Core test:** insert N seeded random vectors, run HNSW `search` and NumPy brute-force `argsort`
  for the same queries, compute `recall@10 = |HNSW_topk ∩ truth_topk| / k` averaged over many
  queries; assert **≥ 0.90 at N=10,000** with defaults. A faster N=1,000 variant runs in the
  default suite; the 10k gate runs as a marked/slower test.
- **Distance tests:** small hand-checkable vectors confirm ordering (closer pairs yield smaller
  values) for each metric, and that cosine ignores magnitude.
- **Prior art:** none yet — this establishes the test pattern (seeded fixtures + brute-force oracle)
  that Phase 2 reuses.

## Out of Scope

- Persistence (Phase 2), any HTTP/API layer (Phase 3), embeddings or real datasets (Phase 4),
  the heuristic neighbor variant becoming default (only if recall fails), node deletion, and
  multi-collection CRUD.

## Further Notes

- If recall@10 lands below 0.90 on real (Phase 4) embeddings, flip the default to the heuristic
  neighbor selector — the interface already supports it; no caller changes.
- Keep `_search_layer` allocation-light; it is the hot path the live demo's latency depends on.
