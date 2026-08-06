from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(default="default")
    messages: List[ChatMessage]


class CodeRequest(BaseModel):
    code: str
    language: Optional[str] = "python"


class RatingResponse(BaseModel):
    overall: int
    readability: int
    performance: int
    security: int
    breakdown: str


class ComplexityResponse(BaseModel):
    time_complexity: str
    space_complexity: str
    explanation: str


class BugFinding(BaseModel):
    severity: str
    line: int
    message: str
    hint: str


class BugReport(BaseModel):
    bugs: List[BugFinding]


class IngestRequest(BaseModel):
    documents: List[str]
    source: str = Field(default="generic")
