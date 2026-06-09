"""FastAPI app exposing the VecLite engine over a focused demo API.

Endpoints:
    POST /search     — text-first (or raw vector) nearest-neighbor search
    GET  /stats      — index size, layer distribution, config
    POST /benchmark  — small live recall check
    GET  /health     — liveness/wake probe

On startup the app loads the pre-built ``index.pkl`` once and instantiates the
query embedder once (decision #4). Tests inject a ready-made service instead, so
they never load the model.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from engine import HNSWIndex

from . import schemas
from .search_service import SearchService

DEFAULT_INDEX_PATH = "index.pkl"


def _build_service_from_env() -> SearchService:
    index_path = os.environ.get("VECLITE_INDEX_PATH", DEFAULT_INDEX_PATH)
    try:
        index = HNSWIndex.load(index_path)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Index artifact not found at {index_path!r}. Build it first "
            f"(scripts/build_index.py) or set VECLITE_INDEX_PATH."
        ) from exc

    from .embedding import FastEmbedEmbedder  # lazy: keep model load off import path

    return SearchService(index, FastEmbedEmbedder())


def create_app(service: SearchService | None = None) -> FastAPI:
    """Build the app. Pass ``service`` to inject a test double; otherwise the
    index and embedder are loaded from the environment on startup."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service if service is not None else _build_service_from_env()
        yield

    app = FastAPI(title="VecLite", version="0.1.0", lifespan=lifespan)

    origins = [
        o.strip()
        for o in os.environ.get("VECLITE_CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_service(request: Request) -> SearchService:
        return request.app.state.service

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/search", response_model=schemas.SearchResponse)
    def search(req: schemas.SearchRequest, request: Request):
        service = get_service(request)
        try:
            return service.search(
                query=req.query, vector=req.vector, k=req.k, ef_search=req.ef_search
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/stats", response_model=schemas.StatsResponse)
    def stats(request: Request):
        return get_service(request).stats()

    @app.post("/benchmark", response_model=schemas.BenchmarkResponse)
    def benchmark(req: schemas.BenchmarkRequest, request: Request):
        return get_service(request).benchmark(n_queries=req.n_queries)

    return app


# Module-level app for `uvicorn api.main:app`.
app = create_app()
