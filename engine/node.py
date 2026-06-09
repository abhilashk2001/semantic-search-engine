"""The graph node stored by :class:`~engine.hnsw.HNSWIndex`."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Node:
    """A single vector in the HNSW graph.

    Attributes:
        id: Stable integer identifier assigned at insert time.
        vector: The stored vector as ``float32`` (unit-normalized for cosine).
        metadata: Arbitrary payload travelling with the vector (e.g. source text).
        level: The node's top layer; it exists on layers ``0..level``.
        connections: Per-layer adjacency, ``{layer: set(neighbor_id)}``.
    """

    id: int
    vector: np.ndarray
    metadata: dict = field(default_factory=dict)
    level: int = 0
    connections: dict[int, set[int]] = field(default_factory=dict)

    def neighbors(self, layer: int) -> set[int]:
        """Return the neighbor ids at ``layer`` (empty set if none)."""
        return self.connections.setdefault(layer, set())
