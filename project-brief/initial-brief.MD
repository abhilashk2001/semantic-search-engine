### Project Brief

---

## 1. Project Abstract

**VecLite** is a lightweight, dependency-free vector search engine built from scratch. It implements the **Hierarchical Navigable Small World (HNSW)** algorithm — the same approximate nearest neighbor (ANN) indexing algorithm used internally by Pinecone, Weaviate, Qdrant, and Chroma — without relying on any existing vector search library.

The project demonstrates a deep understanding of how modern AI infrastructure works at the search layer: how embeddings are indexed, how similarity queries are resolved in sub-linear time, and what tradeoffs exist between recall accuracy, query latency, and index build time.

On top of the core engine, VecLite ships with a **REST API** and a **React demo app** that lets users perform live semantic search over a real dataset (e.g. 50,000 Wikipedia paragraphs or arXiv abstracts), making the project immediately demoable and tangible to both engineers and non-technical recruiters.

> **The one-liner:** "I built the core indexing and search engine that powers tools like Pinecone — from scratch, no libraries — and wrapped it in a live semantic search demo."

---

## 2. Technologies

### Core engine
| Technology | Role |
|---|---|
| **Python 3.11+** | Primary implementation language |
| **NumPy** | Vector storage (`np.ndarray` of `float32`) and distance computation |
| **Pure Python** | HNSW graph structure — no vector search libraries used |

### API server
| Technology | Role |
|---|---|
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **Pydantic** | Request/response validation and schema enforcement |

### Embeddings
| Technology | Role |
|---|---|
| **sentence-transformers** | Generate embeddings locally — `all-MiniLM-L6-v2` (384 dims, no API key needed) |
| **OpenAI Embeddings API** | Optional — richer 1536-dim embeddings for the demo dataset |

### Demo app
| Technology | Role |
|---|---|
| **React + TypeScript** | Frontend search interface |
| **Vite** | Dev server and bundler |
| **Recharts** | Recall vs latency tradeoff curve visualization |

### Data & persistence
| Technology | Role |
|---|---|
| **pickle / JSON** | Index serialization — save and load graph state to disk |
| **Wikipedia Simple English dataset** | Pre-embedded corpus for live demo (80k paragraphs via HuggingFace datasets) |

### Testing & benchmarking
| Technology | Role |
|---|---|
| **pytest** | Unit and integration tests |
| **NumPy brute force k-NN** | Ground truth baseline for recall measurement |
| **time / cProfile** | Latency benchmarking and profiling |

### Deployment
| Technology | Role |
|---|---|
| **Railway / Render** | Free-tier FastAPI hosting |
| **Vercel** | React demo app hosting |
---

## 3. Problem Statement and Examples

### The core problem

Modern AI applications — RAG pipelines, semantic search, recommendation engines, duplicate detection — all rely on **vector similarity search**: given a query, find the most semantically similar items from a large collection.

Each item (a document, image, product, code snippet) is represented as a **vector embedding** — a list of floating point numbers that encode its meaning. Two semantically similar items have vectors that are close together in high-dimensional space. Search means finding the vectors closest to the query vector.

The naive solution is **exact nearest neighbor (k-NN) search**: compare the query vector against every single vector in the collection and return the top-k closest.

```
query vector: [0.12, 0.87, 0.34, ... 384 dimensions]

brute force:
  distance(query, vector_1) = 0.82
  distance(query, vector_2) = 0.31   ← closest
  distance(query, vector_3) = 0.67
  ...
  distance(query, vector_50000) = 0.44

time complexity: O(N × D)  where N = number of vectors, D = dimensions
```

This works fine at small scale. It breaks down fast:

| Dataset size | Dimensions | Brute force latency |
|---|---|---|
| 10,000 vectors | 384 | ~8ms |
| 100,000 vectors | 384 | ~80ms |
| 1,000,000 vectors | 384 | ~800ms |
| 10,000,000 vectors | 1536 | ~30 seconds |

At production scale, brute force is completely unusable. You need an index.

---

### Real examples where this matters

**Example 1 — RAG pipeline (retrieval-augmented generation)**

A company builds a chatbot over their internal documentation. They have 200,000 documentation chunks, each embedded as a 1536-dimension vector. A user asks a question. The system needs to find the 5 most relevant chunks in under 50ms to include in the LLM prompt.

Brute force: ~300ms per query. With HNSW: ~2ms per query. At 1,000 queries/day, that's the difference between a usable product and an unusable one.

**Example 2 — Semantic search over articles**

A news aggregator wants to show "related articles" for any story. They have 5 million articles indexed. When a user reads an article about climate change, the system must find semantically similar articles in real time.

Exact search across 5M vectors: ~4 seconds. With HNSW: ~5ms. One is a feature, the other is a bug.

**Example 3 — Duplicate detection in a code repository**

A developer tool wants to detect near-duplicate code snippets across 500,000 functions to flag potential copy-paste bugs. Each function is embedded and compared against the rest. Without an index, this is 500,000 × 500,000 comparisons — computationally infeasible. With HNSW, it's a manageable indexing + batch query operation.

---

### Why brute force doesn't scale: the geometry

The reason search in high-dimensional spaces is hard has a name: **the curse of dimensionality**. As dimensions increase, all vectors start to feel equidistant from each other. The contrast between "close" and "far" collapses. This makes spatial partitioning tricks (like k-d trees, which work well in 3D) useless beyond ~20 dimensions. You need a fundamentally different approach — which is exactly what HNSW provides.

---

## 4. Solution

### What HNSW does

HNSW builds a **multi-layer proximity graph** over the vector collection. Each vector becomes a node. Edges connect vectors that are close in embedding space. Search traverses this graph greedily — moving from node to node, always toward the query — to find approximate nearest neighbors in **O(log N)** time instead of O(N).

### The layered structure

```
Layer 2 (sparse, long-range connections):
    [v1] ————————————————————— [v8]
      \                         /
Layer 1 (medium density):
    [v1] —— [v3] —— [v5] —— [v8]
      |       |       |       |
Layer 0 (all vectors, dense connections):
    [v1]-[v2]-[v3]-[v4]-[v5]-[v6]-[v7]-[v8]...
```

- **Layer 0** contains every vector with many short-range connections
- **Higher layers** contain fewer vectors with longer-range connections
- Each vector is assigned a maximum layer at insert time (sampled from an exponential distribution — most vectors live only in layer 0, a few reach higher layers)

### How search works

```
1. Enter at the single entry point node at the top layer
2. Greedily move to the neighbor closest to the query
3. When no closer neighbor exists at this layer, drop down one layer
4. Repeat until layer 0
5. At layer 0, explore more thoroughly and collect top-k results
```

This is analogous to how you'd navigate a highway system: take the highway (top layer) to get close to your destination fast, then exit onto local roads (lower layers) to find the exact address.

### Key parameters you control

| Parameter | What it does | Tradeoff |
|---|---|---|
| `M` | Number of connections per node | Higher M → better recall, more memory |
| `ef_construction` | Candidate list size during index build | Higher → better index quality, slower build |
| `ef_search` | Candidate list size during query | Higher → better recall, higher latency |

### Distance metrics supported

- **Cosine similarity** — angle between vectors (best for text embeddings)
- **Dot product** — for normalized vectors, equivalent to cosine
- **Euclidean (L2)** — straight-line distance (best for image embeddings)

### The full system architecture

```
┌─────────────────────────────────────────────────┐
│                  React Demo App                  │
│                                                  │
│  search box → query embedding → results + stats  │
│  parameter sliders (ef_search, k)                │
│  recall vs latency benchmark chart               │
└───────────────────┬─────────────────────────────┘
                    │ REST API
┌───────────────────▼─────────────────────────────┐
│               Fastify API Server                 │
│                                                  │
│  POST /index     → add vectors to index          │
│  POST /search    → query k nearest neighbors     │
│  GET  /stats     → index size, layer distribution│
│  POST /benchmark → run recall vs brute force     │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│            HNSW Engine (core)                    │
│                                                  │
│  HNSWIndex                                       │
│    ├── insert(vector, metadata)                  │
│    ├── search(queryVector, k, ef)                │
│    ├── layers: Node[][][]                        │
│    └── entryPoint: Node                          │
│                                                  │
│  Node                                            │
│    ├── id: string                                │
│    ├── vector: Float32Array                      │
│    ├── metadata: Record<string, unknown>         │
│    └── connections: Map<layer, Set<nodeId>>      │
│                                                  │
│  DistanceFunctions                               │
│    ├── cosine(a, b)                              │
│    ├── dotProduct(a, b)                          │
│    └── euclidean(a, b)                           │
└─────────────────────────────────────────────────┘
```

### What makes this impressive to talk about

- **The ef_construction vs ef_search distinction** — build quality and query quality are independently tunable. Most engineers who use vector DBs don't know this.
- **The exponential layer assignment** — why most nodes live at layer 0 (it's a deliberate probability distribution, not random)
- **Recall vs latency as a continuous dial** — you can show a live graph of this in the demo
- **Why cosine similarity works for text but L2 works better for images** — the geometry of embedding spaces

---

## 5. Requirements to Finish This Project

### Phase 1 — Core HNSW engine (Week 1)

The engine itself. No API, no demo. Just the algorithm working correctly in Python.

- [ ] `Node` dataclass — stores vector as `np.ndarray` of `float32`, metadata, and per-layer connection sets
- [ ] `HNSWIndex` class — manages the full graph, entry point, and layer assignment
- [ ] `insert(vector, metadata)` — add a new node, assign layers, connect to neighbors
- [ ] `_search_layer(query, entry_points, ef, layer)` — greedy beam search within one layer
- [ ] `search(query, k, ef)` — full multi-layer search returning top-k results
- [ ] `_select_neighbors(candidates, M)` — heuristic neighbor selection (simple and robust variants)
- [ ] Distance functions — cosine, dot product, euclidean in `distance.py`
- [ ] Layer assignment — exponential distribution sampling via `random.expovariate`
- [ ] Unit tests — insert 1000 vectors, verify search returns correct neighbors vs NumPy brute force baseline
- [ ] Recall measurement — `recall@k` = fraction of true top-k returned by HNSW

**Completion check:** HNSW recall@10 ≥ 0.90 on a 10,000 vector test set with default parameters.

---

### Phase 2 — Index persistence 

- [ ] `save(filepath)` — serialize the full graph to disk using `pickle`
- [ ] `load(filepath)` — deserialize and restore — search should work identically post-load
- [ ] Verify round-trip integrity — loaded index returns same results as in-memory index

---

### Phase 3 — FastAPI REST API 

- [ ] `POST /collections` — create a named index with config (M, ef_construction, distance metric)
- [ ] `POST /collections/{name}/vectors` — insert one or many vectors with metadata
- [ ] `POST /collections/{name}/search` — query with a vector, return top-k with distances
- [ ] `GET  /collections/{name}/stats` — node count, layer distribution, index config
- [ ] `POST /collections/{name}/benchmark` — run recall vs brute force, return results
- [ ] `DELETE /collections/{name}` — drop an index
- [ ] Request validation with Pydantic schemas
- [ ] Error handling — meaningful messages for malformed vectors, unknown collections

---

### Phase 4 — Dataset + embeddings 

- [ ] Download and preprocess Wikipedia Simple English (80k paragraphs) via HuggingFace `datasets`
- [ ] Generate embeddings using `sentence-transformers` — `all-MiniLM-L6-v2` (384 dimensions, no API key required)
- [ ] Ingest all embeddings into the index at startup
- [ ] Store original text alongside vectors as metadata so search results are human-readable

---

### Phase 5 — React demo app 

- [ ] Search input — user types a query, app calls `/search` via the FastAPI backend
- [ ] Results list — shows top-10 most similar paragraphs with similarity score and metadata
- [ ] Parameter controls — `ef_search` slider (10–200) and `k` slider (1–20), results update live
- [ ] Recall vs latency chart — run benchmark on demand, plot the tradeoff curve as ef_search varies using Recharts
- [ ] Index stats panel — total vectors, layer distribution, build time
- [ ] "Surprise me" button — picks a random paragraph and searches for its neighbors

---

### Phase 6 — Deployment + polish 

- [ ] Deploy FastAPI to Railway or Render (free tier)
- [ ] Deploy React app to Vercel
- [ ] README with: one-liner, architecture diagram, how to run locally, live demo link, benchmark results
- [ ] Benchmark table in README — recall@10 and query latency at different `ef_search` values
- [ ] Add "compared to brute force" framing — shows exactly what the index buys you

---

### Stretch goals (if time allows)

- [ ] Batch insert endpoint with progress streaming via Server-Sent Events
- [ ] 2D t-SNE visualization — plot all vectors, highlight where query lands and which results are returned
- [ ] Filtering — `search` with a metadata filter (e.g. only return results from a specific category)
- [ ] Multi-collection support with different distance metrics per collection
- [ ] Delete vector — removing a node from the graph (harder than it sounds — requires re-linking neighbors)

---

### Definition of done

The project is portfolio-ready when:

1. A recruiter can go to the live URL, type any phrase, and get semantically relevant results in under 100ms
2. The README explains what HNSW is, why it exists, and what you built — in plain English
3. You can explain the `ef_construction` vs `ef_search` distinction, the layer assignment probability, and the recall vs latency tradeoff without looking at your notes
4. The benchmark chart shows a clear recall/latency curve that makes the tradeoff tangible
5. The GitHub repo has a clean commit history that tells the story of how it was built

---
