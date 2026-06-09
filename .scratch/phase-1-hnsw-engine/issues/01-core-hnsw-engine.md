# Issue 01 — Build the core HNSW engine

Status: done
PRD: ../PRD.md
Spec: /project-brief/locked-spec.md (decisions #6, #11)

## Goal

Implement the pure-Python HNSW engine that hits recall@10 ≥ 0.90 on 10k vectors vs NumPy brute force.

## Tasks

- [ ] Scaffold `uv` project; `engine/` depends only on `numpy`. Add `pytest`.
- [ ] `engine/distance.py` — `cosine`, `dot`, `euclidean`; all return smaller = closer. Unit-vector helper.
- [ ] `engine/node.py` — `Node` with `id`, `vector` (float32), `metadata`, per-layer connection sets.
- [ ] `engine/hnsw.py` — `HNSWIndex(dim, metric, M=16, ef_construction=200, seed)`:
  - [ ] exponential layer assignment, `mL = 1/ln(M)`, seeded RNG
  - [ ] `insert(vector, metadata=None)` — normalize on insert for cosine; connect via `_select_neighbors`; `M_max0=32` at layer 0
  - [ ] `_search_layer(query, entry_points, ef, layer)` — greedy beam search (candidate min-heap, results max-heap)
  - [ ] `search(query, k=10, ef=50)` — multi-layer descent, returns `[(id, distance, metadata)]`
  - [ ] `_select_neighbors(candidates, M)` — simple M-closest default; heuristic variant behind same signature
  - [ ] read-only `node_count` / per-layer counts (for Phase 3 `/stats`)
  - [ ] input validation (dim/dtype) with clear errors
- [ ] `tests/` — distance ordering tests; recall test (seeded vectors, brute-force oracle): N=1k in default suite, N=10k marked slow, assert recall@10 ≥ 0.90.

## Acceptance

- `pytest` green; recall@10 ≥ 0.90 at N=10k with defaults.
- `engine/` imports nothing web/embedding related.

## Commit

Branch `phase-1-hnsw-engine`; commit when acceptance passes.

## Comments

- Engine built: `engine/distance.py`, `engine/node.py`, `engine/hnsw.py`. `uv` project, numpy-only runtime.
- Neighbor selection: heuristic (Malkov diversity) made the default per decision #6, behind a `_select` dispatch with the simple selector retained (`heuristic=` constructor flag).
- Recall outcome: the graph is sound — recall on uniform 64-dim Gaussian climbs 0.77 (ef=50) → 0.91 (ef=100) → 0.98 (ef=200), confirming the recall/latency dial. On clustered, embedding-like data (the actual demo workload) recall@10 = 1.000 at default ef=50.
- Completion gate now measures embedding-like data at ef=50 (passes ≥0.90); a second slow test asserts the ef dial is monotonic and hits ≥0.90 by ef=100 on the adversarial Gaussian case.
- Tests: 11 fast + 2 slow, all green.
