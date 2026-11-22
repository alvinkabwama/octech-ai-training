"""Week 1: three prompt patterns. Replace each TODO, then run `make check WEEK=1`.

Every function calls the model through the shared helper:

    llm.ask(prompt, system=..., temperature=...)   one system prompt + one question
    llm.chat(messages, temperature=...)            a full list of messages

Read LESSON.md first. The tests fake the model, so `make check` costs no free requests;
`make live WEEK=1` runs these functions against real OpenRouter models.
"""

from __future__ import annotations

import json
from typing import Any

from exercises.common import llm  # noqa: F401  (you'll use llm.ask / llm.chat below)

CATEGORIES = ("card_issue", "loan_enquiry", "mobile_banking", "complaint", "other")
URGENCY_LEVELS = ("low", "medium", "high")


def explain(topic: str, audience: str) -> str:
    """Explain ``topic`` so ``audience`` understands it, in 3 sentences or fewer.

    TODO:
      1. Write a system prompt that sets the tone (plain words, no jargon) and says
         "answer in 3 sentences or fewer".
      2. Put the topic and the audience in the user message.
      3. Return the reply from llm.ask(...).
    """
    system_prompt = (
        "You are a patient teacher. Use plain words, avoid technical jargon, "
        "and answer in 3 sentences or fewer."
    )

    user_message = f"Explain {topic} to {audience}."

    return llm.ask(user_message, system=system_prompt)


def classify(message: str) -> str:
    """Return exactly one of CATEGORIES for a customer ``message``.

    TODO:
      1. System prompt: list every category and say "reply with the category name only".
      2. Call the model with temperature=0 (same input -> same answer).
      3. Normalise the reply: strip spaces, quotes and full stops, lower-case it
         ("Loan_Enquiry." -> "loan_enquiry").
      4. If the result isn't in CATEGORIES, return "other". Never trust the model blindly.
    """
    system_prompt = (
        f"You are a customer support classifier. "
        f"Classify the message into exactly one of these categories: "
        f"{', '.join(CATEGORIES)}. "
        f"Reply with the category name only."
    )

    reply = llm.ask(message, system=system_prompt, temperature=0)

    label = reply.strip().strip("\"'.").lower()

    if label in CATEGORIES:
        return label

    return "other"


def extract(text: str) -> dict[str, Any]:
    """Pull customer details out of text as a dict."""

    system_prompt = (
        "Extract the customer's details from the message. "
        "Return a JSON object with these four keys: "
        '"name" (string or null), '
        '"phone" (string or null), '
        '"issue" (string), '
        '"urgency" (low, medium, or high). '
        "Reply with JSON only, no markdown."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    def parse_response(raw: str) -> dict[str, Any]:
        raw = raw.strip()

        # Remove markdown code fences if present.
        if raw.startswith("```"):
            raw = raw.removeprefix("```json").removeprefix("```")
            raw = raw.removesuffix("```").strip()

        data = json.loads(raw)

        if not isinstance(data, dict):
            raise ValueError("Response must be a JSON object")

        keys = ("name", "phone", "issue", "urgency")

        if any(key not in data for key in keys):
            raise ValueError("Missing required fields")

        result = {key: data[key] for key in keys}

        if result["urgency"] not in URGENCY_LEVELS:
            raise ValueError("Invalid urgency level")

        return result

    raw = llm.chat(messages, temperature=0)

    try:
        return parse_response(raw)

    except (ValueError, TypeError):
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Reply with the JSON object only."},
        ]

        retry_raw = llm.chat(retry_messages, temperature=0)

        try:
            return parse_response(retry_raw)
        except (ValueError, TypeError) as error:
            raise ValueError("Model returned invalid JSON after retry") from error
