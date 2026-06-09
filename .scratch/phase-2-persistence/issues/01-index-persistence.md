# Issue 01 — Index persistence (save/load)

Status: ready-for-agent
PRD: ../PRD.md
Spec: /project-brief/locked-spec.md (decision #4)

## Goal

Serialize and restore a full HNSW index losslessly, enabling sub-second boot from a pre-built artifact.

## Tasks

- [ ] `HNSWIndex.save(filepath)` — pickle `{format_version, config, nodes, connections, entry_point_id, metadata}`.
- [ ] `HNSWIndex.load(filepath)` classmethod — reconstruct identical index; restore config + seed.
- [ ] Version tag check on load; clear error on missing/corrupt/incompatible file.
- [ ] Round-trip test: build seeded index → query → save → load → query → assert identical ids/distances/order + config/metadata.
- [ ] Negative test: loading missing path raises a clear error.

## Acceptance

- `pytest` green; loaded index returns identical results to in-memory original.
- Engine still depends only on `numpy` (+ stdlib `pickle`).

## Commit

Branch `phase-2-persistence`; commit when acceptance passes.

## Comments
