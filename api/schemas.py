"""Pydantic request/response schemas for the VecLite API."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class SearchRequest(BaseModel):
    query: str | None = Field(
        default=None, description="Natural-language query text to embed and search."
    )
    vector: list[float] | None = Field(
        default=None, description="A precomputed query vector (alternative to text)."
    )
    k: int = Field(default=10, ge=1, le=100, description="Number of results to return.")
    ef_search: int = Field(
        default=50, ge=1, le=1000, description="Layer-0 candidate-list size."
    )

    @model_validator(mode="after")
    def exactly_one_input(self) -> "SearchRequest":
        has_query = self.query is not None and self.query.strip() != ""
        has_vector = self.vector is not None
        if has_query == has_vector:
            raise ValueError("Provide exactly one of 'query' or 'vector'.")
        return self


class SearchResultItem(BaseModel):
    id: int
    text: str | None = None
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    latency_ms: float
    k: int
    ef_search: int


class StatsResponse(BaseModel):
    node_count: int
    layer_distribution: dict[int, int]
    build_time_ms: float | None
    config: dict


class BenchmarkRequest(BaseModel):
    n_queries: int = Field(default=10, ge=1, le=100)


class BenchmarkResponse(BaseModel):
    recall_at_k: float
    k: int
    n_queries: int
    sample_latency_ms: float
