import asyncio
import json
import re
from typing import AsyncIterator, Dict, List

from app.config import settings


class BaseLLMProvider:
    async def stream(
        self, messages: List[Dict[str, str]], temperature: float = 0.5
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    async def complete(
        self, messages: List[Dict[str, str]], temperature: float = 0.2
    ) -> str:
        parts = []
        async for chunk in self.stream(messages, temperature=temperature):
            parts.append(chunk)
        return "".join(parts)

    async def complete_json(
        self, messages: List[Dict[str, str]], temperature: float = 0.2
    ) -> dict:
        raise NotImplementedError


class MockProvider(BaseLLMProvider):
    """Deterministic offline provider so the app runs without any API key."""

    _script = (
        "Great question. Let's work through it together. "
        "Step one: describe the problem in your own words. "
        "What input does your function receive, and what output should it produce? "
        "Step two: pick the simplest example you can solve by hand and write down the expected result. "
        "Step three: if you are stuck, try drawing a small table or diagram of your data. "
        "Now, what is the first idea that comes to mind for a solution? "
        "Tell me your approach and I will help you refine it."
    )

    async def stream(self, messages, temperature=0.5):
        words = self._script.split(" ")
        for i in range(0, len(words), 4):
            yield " ".join(words[i : i + 4]) + " "
            await asyncio.sleep(0.015)

    async def complete_json(self, messages, temperature=0.2):
        return {
            "rating": 5,
            "bugs": [
                {"line": 1, "issue": "Mock provider — no real analysis", "explanation": "Set LLM_PROVIDER=opencode to enable the LLM deep review."}
            ],
            "socraticHint": "I can't analyze without a real model. Configure an LLM provider first.",
        }


class OpenAICompatibleProvider(BaseLLMProvider):
    """Streaming client for any OpenAI-compatible endpoint (OpenAI, OpenCode Zen, etc.)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        from openai import AsyncOpenAI

        self._model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url or None)

    async def stream(self, messages, temperature=0.5):
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                yield content

    async def complete(self, messages, temperature=0.2):
        response = await self._client.chat.completions.create(
            model=self._model, messages=messages, temperature=temperature
        )
        return response.choices[0].message.content or ""

    async def complete_json(self, messages, temperature=0.2):
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content or "{}")
        except Exception:
            text = await self.complete(messages, temperature=temperature)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {"error": text[:500]}
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"error": text[:500]}


def get_llm() -> BaseLLMProvider:
    provider = settings.llm_provider.lower()

    if provider == "openai" and settings.openai_api_key:
        return OpenAICompatibleProvider(
            settings.openai_api_key, None, settings.openai_model
        )

    if provider == "opencode" and settings.opencode_api_key and "your_" not in settings.opencode_api_key:
        return OpenAICompatibleProvider(
            settings.opencode_api_key, settings.opencode_base_url, settings.opencode_model
        )

    return MockProvider()
