"""Week 1: three prompt patterns. Replace each TODO, then run `make check WEEK=1`.

Every function calls the model through the shared helper:

    llm.ask(prompt, system=..., temperature=...)   one system prompt + one question
    llm.chat(messages, temperature=...)            a full list of messages

Read LESSON.md first. The tests fake the model, so `make check` costs no free requests;
`make live WEEK=1` runs these functions against real OpenRouter models.
"""

from __future__ import annotations

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
    raise NotImplementedError("TODO: explain()")


def classify(message: str) -> str:
    """Return exactly one of CATEGORIES for a customer ``message``.

    TODO:
      1. System prompt: list every category and say "reply with the category name only".
      2. Call the model with temperature=0 (same input -> same answer).
      3. Normalise the reply: strip spaces, quotes and full stops, lower-case it
         ("Loan_Enquiry." -> "loan_enquiry").
      4. If the result isn't in CATEGORIES, return "other". Never trust the model blindly.
    """
    raise NotImplementedError("TODO: classify()")


def extract(text: str) -> dict[str, Any]:
    """Pull customer details out of ``text`` as a dict.

    Returns exactly these keys:
        {"name": str | None, "phone": str | None, "issue": str,
         "urgency": "low" | "medium" | "high"}

    TODO:
      1. System prompt: describe the JSON shape and say "reply with JSON only, no markdown".
      2. Remove ```json ... ``` fences if the model adds them, then json.loads().
      3. Keep only the four keys; check urgency is in URGENCY_LEVELS.
      4. If parsing or checking fails, retry ONCE: send the conversation again plus a user
         message reminding the model to reply with JSON only.
      5. If the second reply is also bad, raise ValueError.
    """
    raise NotImplementedError("TODO: extract()")
