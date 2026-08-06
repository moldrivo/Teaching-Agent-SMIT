import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.services.agent import TeachingAgent
from app.services.history import HistoryStore

router = APIRouter(prefix="/api", tags=["chat"])

agent = TeachingAgent()
store = HistoryStore()


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    history = [{"role": m.role, "content": m.content} for m in request.messages]

    async def event_stream():
        reply: list = []

        last = request.messages[-1]
        if last.role == "user":
            store.add_message(request.session_id, "user", last.content)

        async for event in agent.stream_chat(request.session_id, history):
            if event.get("type") == "text":
                reply.append(event.get("content", ""))
            yield f"data: {json.dumps(event)}\n\n"

        if reply:
            store.add_message(request.session_id, "assistant", "".join(reply))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
