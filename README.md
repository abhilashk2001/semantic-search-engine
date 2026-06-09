# VecLite

A lightweight, dependency-free vector search engine built from scratch. It implements the
**Hierarchical Navigable Small World (HNSW)** approximate nearest-neighbor algorithm in pure
Python (NumPy + standard library only), then wraps it in a REST API and a live semantic-search
demo.

> Work in progress. Full documentation, benchmarks, and the live demo link land in a later phase.

## Layout

| Path | Role |
|------|------|
| `engine/` | Pure-Python HNSW index — the core, with no web or embedding dependencies |
| `api/` | FastAPI service over the engine (later phase) |
| `web/` | React + TypeScript demo app (later phase) |
| `scripts/` | Offline data, embedding, and benchmark pipeline (later phase) |

## Engine quickstart

```python
import numpy as np
from engine import HNSWIndex

index = HNSWIndex(dim=8, metric="cosine")
for vec in np.random.randn(1000, 8).astype("float32"):
    index.insert(vec, metadata={"source": "example"})

results = index.search(np.random.randn(8).astype("float32"), k=5)
for node_id, distance, metadata in results:
    print(node_id, distance, metadata)
```

## Development

```bash
uv sync --extra dev
uv run pytest            # fast suite
uv run pytest -m slow    # 10k-vector recall gate
```
