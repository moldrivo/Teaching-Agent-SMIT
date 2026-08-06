from fastapi import APIRouter

from app.models.schemas import IngestRequest
from app.services.rag import RAG

router = APIRouter(prefix="/api", tags=["rag"])

rag = RAG()


@router.post("/ingest")
def ingest(request: IngestRequest) -> dict:
    count = rag.ingest(request.documents, source=request.source)
    return {"ingested": count, "source": request.source}


@router.get("/ingest/count")
def count() -> dict:
    return {"count": rag.count()}
