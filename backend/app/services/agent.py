import re
from typing import AsyncIterator, Dict, List

from app.core.prompts import SYSTEM_PROMPT
from app.services.guardrails import Guardrails
from app.services.llm import BaseLLMProvider, get_llm
from app.services.rag import RAG

BEGINNER_MARKERS = [
    "don't understand",
    "do not understand",
    "too hard",
    "confusing",
    "confused",
    "i'm stuck",
    "i am stuck",
    "explain like i'm 5",
    "beginner",
    "new to",
    "start from scratch",
    "i don't get it",
    "i do not get it",
    "never coded",
    "first time",
]


def _infer_beginner(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in BEGINNER_MARKERS)


SCAFFOLD_PATTERN = re.compile(
    r"(complete\s+(backend|code|app|project|application)|"
    r"full\s+(app|project|backend|application|code)|"
    r"write\s+the\s+(entire|whole|complete)|"
    r"whole\s+(project|code|backend|app)|"
    r"entire\s+(backend|app|application|project)|"
    r"give\s+me\s+all\s+the\s+code|"
    r"end[ -]to[ -]end\s+(backend|app|project))",
    re.IGNORECASE,
)


def _is_scaffold_request(text: str) -> bool:
    return bool(SCAFFOLD_PATTERN.search(text))


class TeachingAgent:
    def __init__(self) -> None:
        self.llm: BaseLLMProvider = get_llm()
        self.guardrails = Guardrails()
        self.rag = RAG()

    async def stream_chat(
        self, session_id: str, messages: List[Dict[str, str]]
    ) -> AsyncIterator[Dict]:
        last = messages[-1]["content"]

        guard = self.guardrails.guard(last)
        if not guard["allowed"]:
            yield {"type": "guard", "action": guard["action"], "content": guard["message"]}
            yield {"type": "done"}
            return

        context = self.rag.retrieve(last, k=3)
        system = SYSTEM_PROMPT
        if context:
            system += (
                "\n\nRelevant course material (use it when applicable):\n"
                + "\n---\n".join(context)
            )

        if _infer_beginner(last):
            system += (
                "\n\n[DIRECTIVE]: The student is confused or frustrated. Follow this structure: "
                "Step 1 empathy, Step 2 a simple real-world analogy, Step 3 ONE tiny code snippet "
                "(max 5 lines). No jargon-heavy explanations until the student is ready."
            )

        if _is_scaffold_request(last):
            system += (
                "\n\n[SCAFFOLD MODE ACTIVE]: The student asked for a full project or complete code. "
                "REFUSE full code generation. Output ONLY: (1) a polite refusal, (2) an architectural "
                "directory/file tree with TODO comments, and (3) ONE small starter snippet — then ask "
                "the student to write the next function."
            )

        llm_messages = [{"role": "system", "content": system}, *messages]
        try:
            async for chunk in self.llm.stream(llm_messages):
                yield {"type": "text", "content": chunk}
        except Exception as exc:
            yield {"type": "error", "content": f"Model error: {exc}"}
        yield {"type": "done"}

    async def deep_review(self, code: str, language: str = "python") -> dict:
        prompt = (
            f"Analyze this {language} code strictly for semantic bugs, logic errors, and hidden "
            "performance risks.\n"
            f"Code:\n```{language}\n{code}\n```\n\n"
            "Return a JSON object with:\n"
            '{\n  "rating": number (1-10),\n'
            '  "bugs": [{"line": number, "issue": string, "explanation": string}],\n'
            '  "socraticHint": string (a hint to fix the main issue, DO NOT give the corrected code)\n}'
        )
        return await self.llm.complete_json(
            [{"role": "user", "content": prompt}], temperature=0.2
        )
