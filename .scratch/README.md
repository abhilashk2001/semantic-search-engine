# VecLite — Phase plan

Source of truth: [`project-brief/locked-spec.md`](../project-brief/locked-spec.md).
Per phase: read PRD → read the `ready-for-agent` issue → code on a feature branch → commit.

| Phase | PRD | Issue | Delivers |
|-------|-----|-------|----------|
| 1 | [phase-1-hnsw-engine](phase-1-hnsw-engine/PRD.md) | [01](phase-1-hnsw-engine/issues/01-core-hnsw-engine.md) | Pure-Python HNSW engine + recall test |
| 2 | [phase-2-persistence](phase-2-persistence/PRD.md) | [01](phase-2-persistence/issues/01-index-persistence.md) | `save`/`load` + round-trip test |
| 3 | [phase-3-api](phase-3-api/PRD.md) | [01](phase-3-api/issues/01-fastapi-demo-api.md) | FastAPI demo API |
| 4 | [phase-4-data-pipeline](phase-4-data-pipeline/PRD.md) | [01](phase-4-data-pipeline/issues/01-dataset-embeddings-index.md) | Corpus + embeddings + `index.pkl` + `results.json` |
| 5 | [phase-5-web-demo](phase-5-web-demo/PRD.md) | [01](phase-5-web-demo/issues/01-react-demo-app.md) | React/Tailwind demo app |
| 6 | [phase-6-deploy](phase-6-deploy/PRD.md) | [01](phase-6-deploy/issues/01-deploy-and-polish.md) | Render + Vercel deploy, CI, README |
