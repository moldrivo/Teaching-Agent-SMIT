from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat, code, history, ingest
from app.services.rag import RAG

app = FastAPI(
    title="Smit Teaching Agent API",
    description="Socratic AI coding tutor: streaming chat, code rating, complexity analysis, bug hunting, RAG + guardrails.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (chat, code, ingest, history):
    app.include_router(module.router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "rag_documents": RAG().count(),
    }
