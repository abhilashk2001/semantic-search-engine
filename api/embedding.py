"""Query-time text embedding.

The API embeds incoming query text into the same 384-dim space as the indexed
corpus. We use fastembed (ONNX ``all-MiniLM-L6-v2``) rather than
sentence-transformers so the server stays light enough for free-tier hosting —
no PyTorch. The corpus (built offline) must use this exact model.

``fastembed`` is imported lazily inside the constructor so that importing this
module — and running unit tests with a stub embedder — never pulls in the model.
"""

from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384


class Embedder(Protocol):
    """Anything that turns text into vectors. Lets tests inject a stub."""

    dim: int

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return a ``(len(texts), dim)`` float32 array."""
        ...


class FastEmbedEmbedder:
    """Embedder backed by fastembed's ONNX ``all-MiniLM-L6-v2``."""

    def __init__(self, model_name: str = MODEL_NAME, dim: int = EMBED_DIM) -> None:
        from fastembed import TextEmbedding  # lazy: avoids import at module load

        self._model = TextEmbedding(model_name=model_name)
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        vectors = list(self._model.embed(list(texts)))
        return np.asarray(vectors, dtype=np.float32)
