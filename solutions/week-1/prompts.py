"""Week 1 reference solution: three prompt patterns (explain, classify, extract).

Compare this with your own `exercises/week-1-calling-a-model/starter/prompts.py`.
Every function talks to the model through the shared helper `exercises/common/llm.py`:

    llm.ask(prompt, system=..., temperature=...)   one system prompt + one question
    llm.chat(messages, temperature=...)            a full list of messages (a conversation)

Check it against the week 1 tests (no model calls, no free requests used):
    make check WEEK=1 STARTER=solutions/week-1
    PowerShell: .venv\\Scripts\\python scripts\\run_week.py check 1 --starter solutions/week-1
"""

# Lets us write type hints such as `dict[str, Any]` and `str | None` on Python 3.10
# without them being evaluated at import time.
from __future__ import annotations

import json  # turns the model's JSON text into a Python dict (json.loads)
import re  # regular expressions, used to cut ```json ... ``` fences off a reply
from typing import Any  # "any type": the dict values can be str or None

from exercises.common import llm

# ---------------------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------------------
# Values the code checks against live in one place, in CAPITALS, so the prompt and the
# validation can never disagree. If you add a category here, the prompt and the check
# both pick it up automatically.

# The only labels classify() may return. A tuple, not a list, because it never changes.
CATEGORIES = ("card_issue", "loan_enquiry", "mobile_banking", "complaint", "other")

# The only urgency values extract() accepts.
URGENCY_LEVELS = ("low", "medium", "high")

# The exact keys extract() returns. Anything else the model adds is dropped.
EXTRACT_FIELDS = ("name", "phone", "issue", "urgency")

# ---------------------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------------------
# The system prompt holds the rules (tone, length, output format). The developer writes
# it; the user can't change it. The user message only carries the thing to work on.

# Pattern 1: sets the tone ("plain words, no jargon") and the length limit.
EXPLAIN_SYSTEM = (
    "You are a patient teacher at a software company. Explain the topic so the given "
    "audience understands it. Use plain words, no jargon, and answer in 3 sentences or fewer."
)

# Pattern 2: lists every allowed label (built from CATEGORIES) and asks for the label only,
# so the reply is easy to check. ", ".join(...) turns the tuple into "a, b, c".
CLASSIFY_SYSTEM = (
    "Classify the customer message into exactly one of these categories: "
    f"{', '.join(CATEGORIES)}. Reply with the category name only, nothing else."
)

# Pattern 3: describes the exact JSON shape, says what to do with missing details (null),
# and asks for JSON only. Being this specific makes a parseable reply far more likely.
EXTRACT_SYSTEM = (
    "Extract these fields from the customer message and reply with JSON only, no markdown, "
    'no explanation: {"name": string or null, "phone": string or null, '
    '"issue": string, "urgency": "low" or "medium" or "high"}. '
    "Use null when the name or phone number is not given."
)

# Sent on the retry, after the model's bad reply, so it knows what to fix.
JSON_REMINDER = "Your last reply was not valid JSON. Reply with the JSON object only."


# ---------------------------------------------------------------------------------------
# Pattern 1: explain
# ---------------------------------------------------------------------------------------
def explain(topic: str, audience: str) -> str:
    """Explain ``topic`` so ``audience`` understands it, in 3 sentences or fewer."""
    # The topic and audience change on every call, so they go in the USER message.
    # The rules (tone, 3 sentences) never change, so they stay in the SYSTEM prompt.
    # No temperature is passed: a little variety in wording is fine for an explanation.
    return llm.ask(f"Explain {topic} to {audience}.", system=EXPLAIN_SYSTEM)


# ---------------------------------------------------------------------------------------
# Pattern 2: classify
# ---------------------------------------------------------------------------------------
def _normalise_label(reply: str) -> str:
    """Turn a raw model reply into one of CATEGORIES, or "other" if it isn't one.

    The leading underscore marks this as a helper used only inside this file.
    """
    # Models add noise: spaces, quotes, a full stop, capitals. Clean it in this order:
    #   .strip()               remove spaces/newlines at both ends:   ' "Loan_Enquiry". '
    #   .strip("\"'`.!")       remove quotes AND punctuation together: 'Loan_Enquiry'
    #   .strip()               remove any space that was inside the quotes
    #   .lower()               'loan_enquiry'
    #   .replace(" ", "_")     'mobile banking' -> 'mobile_banking'
    # Stripping quotes and the full stop in ONE call matters: strip() removes any mix of
    # those characters from the ends, so '"loan_enquiry".' is cleaned whatever the order.
    # Stripping quotes first and the full stop second would leave the closing quote behind.
    label = reply.strip().strip("\"'`.!").strip().lower().replace(" ", "_")
    # Never trust the model blindly: only a label from our own list gets through.
    return label if label in CATEGORIES else "other"


def classify(message: str) -> str:
    """Return exactly one of CATEGORIES for a customer ``message``."""
    # temperature=0 makes the model pick its most likely answer every time, so the same
    # message always gets the same label. That's what you want when choosing from a list.
    reply = llm.ask(message, system=CLASSIFY_SYSTEM, temperature=0)
    return _normalise_label(reply)


# ---------------------------------------------------------------------------------------
# Pattern 3: extract
# ---------------------------------------------------------------------------------------
def _strip_fences(reply: str) -> str:
    """Return the JSON inside ```json ... ``` fences, or the whole reply if there are none."""
    # Many models wrap JSON in a markdown code block even when told not to.
    #   ```          the opening fence
    #   (?:json)?    an optional "json" label (?: means "group, but don't capture")
    #   \s*          any spaces or newlines after it
    #   (.*?)        the JSON itself, as little as possible (captured as group 1)
    #   \s*```       the closing fence
    # re.DOTALL lets "." match newlines too, because the JSON usually spans several lines.
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", reply, re.DOTALL)
    return match.group(1) if match else reply.strip()


def _parse_extract(reply: str) -> dict[str, Any]:
    """Parse and check one model reply. Return the clean dict or raise ValueError."""
    # json.loads raises json.JSONDecodeError on bad JSON. JSONDecodeError is a subclass of
    # ValueError, so the caller only has to catch ValueError for every kind of bad reply.
    data = json.loads(_strip_fences(reply))

    # Valid JSON can still be the wrong shape, e.g. a list or a number. We need an object.
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")

    # Keep exactly the four keys we promised, in a new dict. Extra keys the model invents
    # are dropped; missing keys become None (dict.get returns None when a key is absent).
    result = {field: data.get(field) for field in EXTRACT_FIELDS}

    # Check the values, not just the keys. Urgency must be one of our three words...
    if result["urgency"] not in URGENCY_LEVELS:
        raise ValueError(f"urgency must be one of {URGENCY_LEVELS}, got {result['urgency']!r}")
    # ...and issue must be real text. The lesson says issue is a str, never null, and an
    # empty issue is no use to whoever picks up the ticket.
    if not isinstance(result["issue"], str) or not result["issue"].strip():
        raise ValueError("issue must be a non-empty string")

    # name and phone may be a string or None (the customer may not give them).
    for field in ("name", "phone"):
        if result[field] is not None and not isinstance(result[field], str):
            raise ValueError(f"{field} must be a string or null")

    return result


def extract(text: str) -> dict[str, Any]:
    """Pull customer details out of ``text`` as a dict.

    Returns exactly these keys:
        {"name": str | None, "phone": str | None, "issue": str,
         "urgency": "low" | "medium" | "high"}

    Raises ValueError if the model still gives a bad reply after one retry.
    """
    # Build the conversation as a list of messages. We use llm.chat (not llm.ask) because
    # on a retry we need to send the whole conversation, including the model's own reply.
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": EXTRACT_SYSTEM},
        {"role": "user", "content": text},
    ]
    # temperature=0: we want the most predictable, format-following answer.
    reply = llm.chat(messages, temperature=0)

    try:
        return _parse_extract(reply)
    except ValueError:  # bad JSON, wrong shape or a bad value
        # Retry ONCE. The model has no memory between calls, so we send the conversation
        # again, PLUS its bad reply (as "assistant") and a reminder (as "user"). Including
        # the bad reply shows the model exactly what it got wrong.
        messages += [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": JSON_REMINDER},
        ]
        # No try/except this time: if the second reply is also bad, _parse_extract raises
        # ValueError and it goes straight to the caller, which is what the task asks for.
        return _parse_extract(llm.chat(messages, temperature=0))
