"""Distance metrics for the HNSW engine.

Every metric returns a value where **smaller means closer**, so the search and
neighbor-selection logic can stay metric-agnostic.

Supported metrics:
    - "cosine"    : 1 - cosine_similarity. Vectors are normalized on insert
                    (see ``prepare_vector``), so this reduces to ``1 - dot``.
    - "dot"       : negative dot product (larger raw dot -> smaller distance).
    - "euclidean" : squared L2 distance (monotonic in true L2, cheaper).
"""

from __future__ import annotations

import numpy as np

METRICS = ("cosine", "dot", "euclidean")


def normalize(vector: np.ndarray) -> np.ndarray:
    """Return ``vector`` scaled to unit length. Zero vectors are returned as-is."""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def prepare_vector(metric: str, vector: np.ndarray) -> np.ndarray:
    """Normalize the vector for cosine; pass through otherwise.

    Storing unit vectors lets cosine distance be computed as ``1 - dot``.
    """
    if metric == "cosine":
        return normalize(vector)
    return vector


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    # Assumes both vectors are already unit length (see prepare_vector).
    return 1.0 - float(np.dot(a, b))


def dot_distance(a: np.ndarray, b: np.ndarray) -> float:
    return -float(np.dot(a, b))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    diff = a - b
    return float(np.dot(diff, diff))


_DISPATCH = {
    "cosine": cosine_distance,
    "dot": dot_distance,
    "euclidean": euclidean_distance,
}


def get_distance(metric: str):
    """Return the distance callable for ``metric``."""
    try:
        return _DISPATCH[metric]
    except KeyError:
        raise ValueError(
            f"Unknown metric {metric!r}; expected one of {METRICS}."
        ) from None
