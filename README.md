# Semantic Search Engine from Scratch

A semantic search engine I built from scratch in Python. The core is a
**Hierarchical Navigable Small World (HNSW)** vector index, the same kind of
approximate nearest-neighbor structure that powers Pinecone, Weaviate, Qdrant,
and Chroma, written with NumPy and the standard library only. No vector-search
libraries do the actual work. On top of the engine sits a FastAPI service and a
React app that lets you search 10,000 Wikipedia paragraphs by meaning.

- **Live demo:** https://semantic-search-engine-virid.vercel.app
- **API:** https://semantic-search-api-223g.onrender.com (try `/stats` or `/health`)

> The API runs on a free Render instance that sleeps when idle, so the first
> request after a nap takes 30 to 60 seconds to wake. The app shows a waking
> message while that happens.

## What it does

You type a phrase like "how do volcanoes erupt" and get back the paragraphs that
are closest in meaning, not the ones that share keywords. Each paragraph is
turned into a 384-dimension vector by an embedding model, and search becomes a
nearest-neighbor problem in that space. Doing that exactly means comparing your
query against every vector. HNSW instead walks a graph and gets there in roughly
`O(log N)` steps, trading a tiny bit of accuracy for a lot of speed at scale.

## How HNSW works, in plain English

Picture a road network with layers. The top layer has a few towns joined by long
highways. Each layer down adds more towns and shorter roads, until the bottom
layer contains every town with lots of local streets.

To find the town nearest your destination, you start on the highways up top and
keep moving to whichever connected town is closer to where you want to be. When
you can't get closer on this layer, you drop down a layer and repeat with the
finer roads. A few hops on highways followed by a few on local streets gets you
there far faster than visiting every town.

HNSW does the same thing with vectors:

- **Layer 0** holds every vector with many short-range links.
- **Higher layers** hold fewer vectors with longer-range links. A vector's top
  layer is drawn from an exponential distribution, so most vectors live only on
  layer 0 and a handful reach the top.
- **Search** enters at the top, greedily moves toward the query, drops a layer
  when it can't improve, and explores more thoroughly at layer 0.

Three knobs control the trade-offs:

| Knob | What it does | Effect |
|------|--------------|--------|
| `M` | links kept per vector | higher means better recall, more memory |
| `ef_construction` | candidate list size while building | higher means a better graph, slower build |
| `ef_search` | candidate list size while querying | higher means better recall, slower query |

The `ef_construction` vs `ef_search` split is the interesting part: build quality
and query effort are tuned independently. You can build once and then dial recall
against latency per query, which is exactly what the demo's slider does.

## Architecture

```
┌──────────────────────────────────────────────┐
│                React + Vite app                │   Vercel
│  search box · ef_search/k sliders · results    │
│  recall-vs-latency chart · index stats panel    │
└───────────────────────┬────────────────────────┘
                        │ REST (JSON)
┌───────────────────────▼────────────────────────┐
│                 FastAPI service                  │   Render
│  POST /search   text in, top-k out + latency     │
│  GET  /stats    node count, layer distribution    │
│  POST /benchmark small live recall check          │
│  GET  /sample   random paragraph (Surprise me)    │
│  GET  /health                                     │
│  query text embedded here with fastembed (ONNX)   │
└───────────────────────┬────────────────────────┘
                        │ in-process
┌───────────────────────▼────────────────────────┐
│              HNSW engine (pure Python)           │
│  HNSWIndex: insert / search / save / load         │
│  greedy beam search per layer, diversity-based     │
│  neighbor selection, exponential layer assignment  │
│  distances: cosine · dot · euclidean              │
└──────────────────────────────────────────────────┘
```

The engine has zero web or embedding dependencies, so it stays a clean,
standalone core. The query embedder uses fastembed (ONNX `all-MiniLM-L6-v2`)
rather than sentence-transformers, which keeps the server off PyTorch and inside
a 512 MB free tier.

## Benchmarks

Measured on the 10,000-paragraph index (384-dim, cosine), recall@10 against an
exact NumPy brute-force baseline, p50 latency over 200 queries:

| `ef_search` | recall@10 | p50 latency |
|------------:|----------:|------------:|
| 10 | 0.985 | 0.26 ms |
| 20 | 0.997 | 0.41 ms |
| 50 | 1.000 | 0.84 ms |
| 100 | 1.000 | 1.49 ms |
| 200 | 1.000 | 2.65 ms |

That is the recall/latency dial as one curve: recall climbs quickly and latency
grows smoothly as you ask the search to look harder.

**On "versus brute force":** at 10,000 vectors, a vectorized NumPy brute force is
already about 0.4 ms per query, because BLAS matrix multiplication is extremely
well optimized and the dataset is small. So at this size HNSW is not the faster
option, and that is the honest result. HNSW's advantage is asymptotic: brute
force is `O(N)` per query while HNSW is roughly `O(log N)`, so the gap only opens
up at hundreds of thousands to millions of vectors. This demo runs 10,000 so the
whole thing fits in free-tier memory, which makes it the right size to show the
algorithm working and the recall/latency trade-off, not to out-run NumPy at small
N. Regenerate the numbers with `uv run --extra data python -m scripts.run_benchmark`.

## Running it locally

### Engine and tests

```bash
uv sync --extra dev
uv run pytest -m "not slow"   # engine, persistence, and API tests
uv run pytest -m slow         # the 10k-vector recall gate
```

### Build the index and serve the API

```bash
uv sync --extra api
uv run python -m scripts.build_index            # embeds data/corpus.jsonl -> index.pkl
uv run uvicorn api.main:app --port 8000
```

To regenerate the corpus from scratch (needs the data extra):

```bash
uv run --extra data python -m scripts.download_data
```

### Run the web app

```bash
cd web
npm install
npm run dev        # http://localhost:5173, talks to the API on :8000
```

Point the frontend at a different backend with `VITE_API_BASE_URL`.

## Project structure

```
engine/    pure-Python HNSW index (the core)
api/       FastAPI service + fastembed query embedding
web/       React + TypeScript + Tailwind demo
scripts/   offline corpus, index build, and benchmark pipeline
benchmarks/ committed recall-vs-latency results the chart renders
data/      committed cleaned corpus (corpus.jsonl) the deploy builds from
```

## Tech

Python, NumPy, FastAPI, fastembed (ONNX `all-MiniLM-L6-v2`), React, TypeScript,
Vite, Tailwind, Recharts. Deployed on Render (API) and Vercel (web).

## Roadmap

Things deliberately left for later:

- Multi-collection API (`POST /collections`, per-collection vectors, delete)
- Metadata filtering during search
- Vector deletion with neighbor re-linking
- A 2D projection view of where a query lands among its neighbors
