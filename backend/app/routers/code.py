from fastapi import APIRouter

from app.models.schemas import CodeRequest
from app.services.analyzer import estimate_complexity, find_bugs, rate_code
from app.services.agent import TeachingAgent

router = APIRouter(prefix="/api/code", tags=["code"])

agent = TeachingAgent()


@router.post("/rate")
def rate(request: CodeRequest) -> dict:
    return rate_code(request.code)


@router.post("/analyze")
def analyze(request: CodeRequest) -> dict:
    return estimate_complexity(request.code)


@router.post("/bugs")
def bugs(request: CodeRequest) -> dict:
    return find_bugs(request.code)


@router.post("/deep-review")
async def deep_review(request: CodeRequest) -> dict:
    return await agent.deep_review(request.code, request.language or "python")
