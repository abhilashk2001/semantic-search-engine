"""Hierarchical Navigable Small World (HNSW) approximate nearest-neighbor index.

A from-scratch implementation following Malkov & Yashunin (2016). The graph is a
stack of layers: layer 0 holds every node with dense, short-range connections;
higher layers hold progressively fewer nodes with longer-range connections.
Search enters at the top layer and greedily descends toward the query, yielding
approximate nearest neighbors in roughly O(log N).

Only ``numpy`` and the standard library are used — no vector-search libraries.
"""

from __future__ import annotations

import heapq
import math
import pickle
import random

import numpy as np

from .distance import METRICS, get_distance, prepare_vector
from .node import Node

# Bump when the serialized layout changes incompatibly.
FORMAT_VERSION = 1


class HNSWIndex:
    """An in-memory HNSW index over fixed-dimensional ``float32`` vectors.

    Args:
        dim: Vector dimensionality. All inserts and queries must match.
        metric: One of ``"cosine"``, ``"dot"``, ``"euclidean"``.
        M: Target number of connections per node on layers above 0.
            Layer 0 allows up to ``2*M``.
        ef_construction: Candidate-list size used while building the graph.
            Larger values improve graph quality at the cost of build time.
        seed: Seed for the layer-assignment RNG, making builds reproducible.
    """

    def __init__(
        self,
        dim: int,
        metric: str = "cosine",
        M: int = 16,
        ef_construction: int = 200,
        seed: int = 42,
        heuristic: bool = True,
    ) -> None:
        if dim <= 0:
            raise ValueError(f"dim must be positive, got {dim}.")
        if metric not in METRICS:
            raise ValueError(f"Unknown metric {metric!r}; expected one of {METRICS}.")

        self.dim = dim
        self.metric = metric
        self.M = M
        self.M_max = M  # max connections per node on layers > 0
        self.M_max0 = 2 * M  # max connections on layer 0
        self.ef_construction = ef_construction
        self.seed = seed
        self.heuristic = heuristic

        self._mL = 1.0 / math.log(M) if M > 1 else 1.0
        self._distance = get_distance(metric)
        self._rng = random.Random(seed)

        self.nodes: dict[int, Node] = {}
        self.entry_point: int | None = None
        self.max_layer: int = 0
        self._next_id: int = 0
        # Optional: wall-clock build time, set by the offline build script and
        # persisted so /stats can report it after a load.
        self.build_time_ms: float | None = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def layer_distribution(self) -> dict[int, int]:
        """Map of layer -> number of nodes present on that layer."""
        dist: dict[int, int] = {}
        for node in self.nodes.values():
            for layer in range(node.level + 1):
                dist[layer] = dist.get(layer, 0) + 1
        return dict(sorted(dist.items()))

    def insert(self, vector, metadata: dict | None = None) -> int:
        """Add a vector to the index and return its assigned id."""
        vec = self._coerce(vector)
        vec = prepare_vector(self.metric, vec)

        node_id = self._next_id
        self._next_id += 1
        level = self._random_level()
        node = Node(id=node_id, vector=vec, metadata=metadata or {}, level=level)
        for layer in range(level + 1):
            node.connections[layer] = set()
        self.nodes[node_id] = node

        # First node becomes the entry point.
        if self.entry_point is None:
            self.entry_point = node_id
            self.max_layer = level
            return node_id

        ep = self.entry_point
        top = self.max_layer

        # Descend from the top layer to just above the new node's level,
        # greedily moving the entry point closer to the query.
        for layer in range(top, level, -1):
            ep = self._greedy_closest(vec, ep, layer)

        # From the new node's level down to 0, connect it into the graph.
        entry_points = [ep]
        for layer in range(min(level, top), -1, -1):
            candidates = self._search_layer(vec, entry_points, self.ef_construction, layer)
            m = self.M_max0 if layer == 0 else self.M_max
            neighbor_ids = self._select(candidates, self.M)
            self._connect(node_id, neighbor_ids, layer, m)
            entry_points = [nid for _, nid in candidates]

        if level > self.max_layer:
            self.max_layer = level
            self.entry_point = node_id

        return node_id

    def search(self, query, k: int = 10, ef: int = 50) -> list[tuple[int, float, dict]]:
        """Return the ``k`` nearest neighbors as ``(id, distance, metadata)``.

        ``ef`` is the layer-0 candidate-list size; larger values raise recall
        and latency. It is clamped up to ``k`` so at least ``k`` are explored.
        """
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}.")

        vec = self._coerce(query)
        vec = prepare_vector(self.metric, vec)

        if self.entry_point is None:
            return []

        ep = self.entry_point
        for layer in range(self.max_layer, 0, -1):
            ep = self._greedy_closest(vec, ep, layer)

        candidates = self._search_layer(vec, [ep], max(ef, k), 0)
        candidates.sort(key=lambda pair: pair[0])
        results = []
        for dist, nid in candidates[:k]:
            results.append((nid, dist, self.nodes[nid].metadata))
        return results

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def save(self, filepath) -> None:
        """Serialize the full index to ``filepath`` via pickle.

        Stores a plain dict (config, nodes, graph state, RNG state) rather than
        the live object directly, so the artifact is inspectable and guarded by
        a format version. A loaded index returns identical search results.
        """
        state = {
            "format_version": FORMAT_VERSION,
            "config": {
                "dim": self.dim,
                "metric": self.metric,
                "M": self.M,
                "ef_construction": self.ef_construction,
                "seed": self.seed,
                "heuristic": self.heuristic,
            },
            "entry_point": self.entry_point,
            "max_layer": self.max_layer,
            "next_id": self._next_id,
            "build_time_ms": self.build_time_ms,
            "rng_state": self._rng.getstate(),
            "nodes": {
                nid: {
                    "id": node.id,
                    "vector": node.vector,
                    "metadata": node.metadata,
                    "level": node.level,
                    "connections": node.connections,
                }
                for nid, node in self.nodes.items()
            },
        }
        with open(filepath, "wb") as fh:
            pickle.dump(state, fh, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, filepath) -> "HNSWIndex":
        """Reconstruct an index previously written by :meth:`save`.

        Raises ``FileNotFoundError`` if the path is missing and ``ValueError``
        if the file is corrupt or written by an incompatible format version.
        """
        try:
            with open(filepath, "rb") as fh:
                state = pickle.load(fh)
        except FileNotFoundError:
            raise
        except (pickle.UnpicklingError, EOFError, OSError) as exc:
            raise ValueError(f"Could not read index file {filepath!r}: {exc}") from exc

        if not isinstance(state, dict) or "format_version" not in state:
            raise ValueError(f"{filepath!r} is not a valid VecLite index file.")
        version = state["format_version"]
        if version != FORMAT_VERSION:
            raise ValueError(
                f"Index format version {version} is not supported "
                f"(expected {FORMAT_VERSION})."
            )

        index = cls(**state["config"])
        index.entry_point = state["entry_point"]
        index.max_layer = state["max_layer"]
        index._next_id = state["next_id"]
        index.build_time_ms = state.get("build_time_ms")
        index._rng.setstate(state["rng_state"])
        index.nodes = {
            nid: Node(
                id=raw["id"],
                vector=raw["vector"],
                metadata=raw["metadata"],
                level=raw["level"],
                connections=raw["connections"],
            )
            for nid, raw in state["nodes"].items()
        }
        return index

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _coerce(self, vector) -> np.ndarray:
        vec = np.asarray(vector, dtype=np.float32)
        if vec.ndim != 1:
            raise ValueError(f"Expected a 1-D vector, got shape {vec.shape}.")
        if vec.shape[0] != self.dim:
            raise ValueError(
                f"Vector has dimension {vec.shape[0]}, expected {self.dim}."
            )
        return vec

    def _random_level(self) -> int:
        # Exponentially-decaying layer assignment: most nodes land on layer 0.
        return int(math.floor(-math.log(self._rng.random()) * self._mL))

    def _greedy_closest(self, query: np.ndarray, entry: int, layer: int) -> int:
        """Greedily walk ``layer`` from ``entry`` to the node closest to query."""
        best = entry
        best_dist = self._distance(query, self.nodes[entry].vector)
        improved = True
        while improved:
            improved = False
            for nid in self.nodes[best].neighbors(layer):
                d = self._distance(query, self.nodes[nid].vector)
                if d < best_dist:
                    best_dist, best, improved = d, nid, True
        return best

    def _search_layer(
        self, query: np.ndarray, entry_points: list[int], ef: int, layer: int
    ) -> list[tuple[float, int]]:
        """Beam search within one layer; returns up to ``ef`` ``(dist, id)``."""
        visited: set[int] = set()
        candidates: list[tuple[float, int]] = []  # min-heap by distance
        results: list[tuple[float, int]] = []  # max-heap via negated distance

        for ep in entry_points:
            d = self._distance(query, self.nodes[ep].vector)
            heapq.heappush(candidates, (d, ep))
            heapq.heappush(results, (-d, ep))
            visited.add(ep)

        while candidates:
            d_c, c = heapq.heappop(candidates)
            furthest = -results[0][0]
            if d_c > furthest:
                break
            for e in self.nodes[c].neighbors(layer):
                if e in visited:
                    continue
                visited.add(e)
                d_e = self._distance(query, self.nodes[e].vector)
                furthest = -results[0][0]
                if d_e < furthest or len(results) < ef:
                    heapq.heappush(candidates, (d_e, e))
                    heapq.heappush(results, (-d_e, e))
                    if len(results) > ef:
                        heapq.heappop(results)

        return [(-neg_d, nid) for neg_d, nid in results]

    def _select(self, candidates: list[tuple[float, int]], M: int) -> list[int]:
        """Dispatch to the heuristic or simple selector based on config."""
        if self.heuristic:
            return self._select_neighbors_heuristic(candidates, M)
        return self._select_neighbors(candidates, M)

    def _select_neighbors(
        self, candidates: list[tuple[float, int]], M: int
    ) -> list[int]:
        """Simple selection: the ``M`` closest candidates.

        Kept behind the :meth:`_select` dispatch so the diversity heuristic
        (:meth:`_select_neighbors_heuristic`) can be swapped in without
        touching call sites.
        """
        ordered = sorted(candidates, key=lambda pair: pair[0])
        return [nid for _, nid in ordered[:M]]

    def _select_neighbors_heuristic(
        self, candidates: list[tuple[float, int]], M: int
    ) -> list[int]:
        """Malkov's diversity heuristic: prefer a spread of neighbors.

        A candidate is kept only if it is closer to the new node than to any
        already-selected neighbor, which avoids clustered "islands" and tends
        to improve recall on real embedding data.
        """
        ordered = sorted(candidates, key=lambda pair: pair[0])
        selected: list[tuple[float, int]] = []
        for d_cand, cand in ordered:
            if len(selected) >= M:
                break
            keep = True
            for _, sel in selected:
                d_between = self._distance(
                    self.nodes[cand].vector, self.nodes[sel].vector
                )
                if d_between < d_cand:
                    keep = False
                    break
            if keep:
                selected.append((d_cand, cand))
        return [nid for _, nid in selected]

    def _connect(
        self, node_id: int, neighbor_ids: list[int], layer: int, m_max: int
    ) -> None:
        """Add bidirectional edges, then prune over-full neighbors back to m_max."""
        node = self.nodes[node_id]
        for nid in neighbor_ids:
            if nid == node_id:
                continue
            node.neighbors(layer).add(nid)
            self.nodes[nid].neighbors(layer).add(node_id)

        for nid in neighbor_ids:
            neighbor = self.nodes[nid]
            conns = neighbor.neighbors(layer)
            if len(conns) <= m_max:
                continue
            scored = [
                (self._distance(neighbor.vector, self.nodes[o].vector), o)
                for o in conns
            ]
            kept = self._select(scored, m_max)
            neighbor.connections[layer] = set(kept)
