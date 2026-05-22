"""FastAPI — local sessions (Postgres) + Agent Engine chat proxy."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import cors_origin_list
from backend.routers import chat, question_catalog, sessions

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Jaybel Sales Analytics API",
    description="Local API: Postgres sessions + Agent Engine SSE proxy",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(question_catalog.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
