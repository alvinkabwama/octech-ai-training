"""Week 1: three prompt patterns. Replace each TODO, then run `make check WEEK=1`.

Every function calls the model through the shared helper:

    llm.ask(prompt, system=..., temperature=...)   one system prompt + one question
    llm.chat(messages, temperature=...)            a full list of messages

Read LESSON.md first. The tests fake the model, so `make check` costs no free requests;
`make live WEEK=1` runs these functions against real OpenRouter models.
"""

from __future__ import annotations

import json
import re
from typing import Any

from exercises.common import llm  # noqa: F401  (you'll use llm.ask / llm.chat below)

CATEGORIES = ("card_issue", "loan_enquiry", "mobile_banking", "complaint", "other")
URGENCY_LEVELS = ("low", "medium", "high")


def explain(topic: str, audience: str) -> str:
    """Explain ``topic`` so ``audience`` understands it, in 3 sentences or fewer."""
    system = (
        "You are a patient teacher. Use plain words and no jargon. Answer in 3 sentences or fewer."
    )
    user = f"Explain {topic} to {audience}."
    return llm.ask(user, system=system)


def classify(message: str) -> str:
    """Return exactly one of CATEGORIES for a customer ``message``."""
    system = (
        f"Classify the customer message into one of: {', '.join(CATEGORIES)}. "
        "Reply with the category name only."
    )
    reply = llm.ask(message, system=system, temperature=0)
    label = reply.strip().strip("\"'.").lower()
    return label if label in CATEGORIES else "other"


def _parse_extraction(raw: str) -> dict[str, Any]:
    """Turn a model reply into a checked dict, or raise ValueError."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    data = json.loads(cleaned)  # JSONDecodeError is a ValueError
    if not isinstance(data, dict):
        raise ValueError("reply is not a JSON object")
    result = {
        "name": data.get("name"),
        "phone": data.get("phone"),
        "issue": data.get("issue"),
        "urgency": data.get("urgency"),
    }
    if result["urgency"] not in URGENCY_LEVELS:
        raise ValueError(f"bad urgency: {result['urgency']!r}")
    return result


def extract(text: str) -> dict[str, Any]:
    """Pull customer details out of ``text`` as a dict."""
    system = (
        "Extract customer details from the text. Reply with JSON only, no markdown, "
        'in exactly this shape: {"name": string or null, "phone": string or null, '
        '"issue": short string, "urgency": "low" or "medium" or "high"}. '
        "Use null when the name or phone is not given."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    raw = llm.chat(messages, temperature=0)
    try:
        return _parse_extraction(raw)
    except ValueError:
        # Show the model its bad reply and ask again, once.
        messages += [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Reply with the JSON object only."},
        ]
        return _parse_extraction(llm.chat(messages, temperature=0))  # raises if still bad
