from fastapi import APIRouter

from app.services.history import HistoryStore

router = APIRouter(prefix="/api", tags=["history"])

store = HistoryStore()


@router.get("/history/{session_id}")
def get_history(session_id: str) -> dict:
    return {"session_id": session_id, "messages": store.get_history(session_id)}


@router.get("/sessions")
def list_sessions() -> dict:
    return {"sessions": store.list_sessions()}
