import re
from typing import Tuple

OFF_TOPIC_TERMS = [
    # politics / current affairs
    "politics",
    "politician",
    "election",
    "president",
    "voting",
    "campaign",
    "parliament",
    "congress",
    "prime minister",
    "senate",
    "referendum",
    # religion / belief
    "religion",
    "god",
    "prayer",
    "temple",
    "church",
    "mosque",
    "astrology",
    "horoscope",
    "palm reading",
    # entertainment / lifestyle
    "celebrity",
    "gossip",
    "tabloid",
    "movie review",
    "tv show",
    "reality show",
    "netflix series",
    "soap opera",
    "song lyrics",
    "music album",
    "concert",
    "fashion advice",
    "recipe",
    "cooking",
    "biryani",
    "pizza recipe",
    "cake recipe",
    "workout plan",
    "diet plan",
    # sports
    "super bowl",
    "world cup",
    "cricket",
    "football match",
    "sports score",
    "betting",
    "lottery",
    "sports odds",
    "fantasy league",
    # weather / general trivia
    "weather forecast",
    "horoscope today",
    "fun fact",
    "joke",
    "riddle",
    "pickup line",
]

INJECTION_RESPONSE = (
    "I am the Smit Teaching Agent, focused exclusively on helping you learn coding. "
    "How can I help with your code today?"
)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|earlier).{0,30}instructions",
    r"ignore\s+(the\s+)?(above|system\s+prompt)",
    r"disregard\s+(your|the).{0,20}(instructions|prompt|rules)",
    r"forget\s+(your|the)\s+(role|instructions|prompt|rules)",
    r"reveal\s+(your|the)\s+(system\s+)?prompt",
    r"reveal\s+(your\s+)?(hidden\s+)?(instructions|rules)",
    r"show\s+(me\s+)?(your|the)\s+(system\s+)?prompt",
    r"print\s+your\s+(system\s+)?prompt",
    r"output\s+your.{0,30}(system\s+)?prompt",
    r"dump\s+your\s+(system\s+)?prompt",
    r"initial\s+(system\s+)?prompt",
    r"hidden\s+instructions?",
    r"operational\s+rules",
    r"your\s+(real\s+)?purpose",
    r"real\s+(identity|persona)",
    r"you\s+are\s+now\s+(not\s+)?(a|coding|an\w*)\b.{0,40}",
    r"pretend\s+you\s+are\s+not\b",
    r"pretend\s+you\s+have\s+no\s+rules",
    r"pretend\s+you.{0,20}no\s+(rules|limits|constraints|guardrails)",
    r"no\s+(rules|limits|constraints|guardrails)\s+for\s+you",
    r"you\s+can\s+say\s+anything",
    r"jailbreak",
    r"do\s+whatever\s+it\s+takes",
    r"your\s+instructions?\s+are\s+now\b",
    r"bypass\s+(your|the)\s+(guardrails|filters|rules)",
    r"switch\s+out\s+of\s+your\s+role",
    r"nevermind\s+your\s+role",
]


class Guardrails:
    """Lightweight topic filter + prompt-injection detector.

    Swap this out for NVIDIA NeMo Guardrails / Llama Guard later — keep the
    same interface (guard(text) -> dict) so nothing else changes.
    """

    def check_topic(self, text: str) -> Tuple[bool, str]:
        low = text.lower()
        hits = [t for t in OFF_TOPIC_TERMS if t in low]
        if hits:
            return False, (
                "I am the Smit Teaching Agent, focused exclusively on helping you learn coding. "
                "That topic is outside my lane — let's redirect to programming: what are you building?"
            )
        return True, ""

    def check_injection(self, text: str) -> Tuple[bool, str]:
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, INJECTION_RESPONSE
        return True, ""

    def guard(self, text: str) -> dict:
        ok_topic, topic_msg = self.check_topic(text)
        if not ok_topic:
            return {"allowed": False, "action": "redirect", "message": topic_msg}
        ok_injection, injection_msg = self.check_injection(text)
        if not ok_injection:
            return {"allowed": False, "action": "block", "message": injection_msg}
        return {"allowed": True, "action": "pass", "message": ""}
