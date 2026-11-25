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

from exercises.common import llm

CATEGORIES = ("card_issue", "loan_enquiry", "mobile_banking", "complaint", "other")
URGENCY_LEVELS = ("low", "medium", "high")


def explain(topic: str, audience: str) -> str:
    return llm.ask(
        f"Explain {topic} to {audience}.",
        system="Use plain words and no jargon. Answer in 3 sentences or fewer.",
    )


def classify(message: str) -> str:
    categories = ", ".join(CATEGORIES)
    reply = llm.ask(
        message,
        system=f"Classify the customer message into one of these categories: "
        f"{categories}. Reply with the category name only.",
        temperature=0,
    )
    result = reply.strip().strip("\"'").rstrip(".").lower()
    return result if result in CATEGORIES else "other"


def extract(text: str) -> dict[str, Any]:
    system = (
        "Extract the customer details as JSON with exactly these fields: "
        '"name" (string or null), "phone" (string or null), "issue" (string), '
        '"urgency" ("low", "medium", or "high"). Reply with JSON only, no markdown.'
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]

    for attempt in range(2):
        if attempt == 1:
            messages.append(
                {"role": "user", "content": "Please reply with JSON only, with no markdown."}
            )

        reply = llm.chat(messages)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", reply.strip(), flags=re.IGNORECASE)

        try:
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")

            result = {
                "name": data.get("name"),
                "phone": data.get("phone"),
                "issue": data.get("issue"),
                "urgency": data.get("urgency"),
            }

            if result["name"] is not None and not isinstance(result["name"], str):
                raise ValueError("name must be a string or null")
            if result["phone"] is not None and not isinstance(result["phone"], str):
                raise ValueError("phone must be a string or null")
            if not isinstance(result["issue"], str):
                raise ValueError("issue must be a string")
            if result["urgency"] not in URGENCY_LEVELS:
                raise ValueError("unknown urgency")

            return result
        except (json.JSONDecodeError, ValueError) as error:
            if attempt == 1:
                raise ValueError("The model did not return valid customer details JSON") from error
    raise ValueError("The model did not return valid customer details JSON")
