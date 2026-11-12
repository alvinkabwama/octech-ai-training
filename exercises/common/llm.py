"""Shared OpenRouter helper: every exercise calls a model through this module.

OpenRouter speaks the OpenAI Chat Completions format, so we use the ``openai`` SDK
pointed at OpenRouter's URL. The key comes from ``OPENROUTER_API_KEY`` (environment
or the repo's ``.env`` file).

Typical use::

    from exercises.common import llm

    print(llm.ask("Explain an API in one sentence."))
    reply = llm.chat([
        {"role": "system", "content": "Answer in 3 sentences or fewer."},
        {"role": "user", "content": "What is a records retention schedule?"},
    ], temperature=0)

Free models are rate-limited (20 requests/minute, 50/day without credits) and can
disappear, so every call sends a fallback list and retries briefly on HTTP 429.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import openai
from dotenv import load_dotenv

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

DEFAULT_MODELS: list[str] = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
]
MAX_MODELS = 3
MAX_ATTEMPTS = 3
# Wait before retry 1, 2, 3. With 3 attempts only 5s and 10s are used: sleeping after the
# last failed attempt would just delay the error.
BACKOFF_SECONDS = (5, 10, 20)
REQUEST_TIMEOUT_SECONDS = 60.0


class LLMError(RuntimeError):
    """The helper could not get a usable reply (no key, rate-limited, empty reply)."""


@lru_cache(maxsize=1)
def get_client() -> openai.OpenAI:
    """Return an OpenAI SDK client pointed at OpenRouter (created once, then reused).

    Raises:
        LLMError: If ``OPENROUTER_API_KEY`` is not set in the environment or ``.env``.
    """
    load_dotenv(ENV_FILE, override=False)
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise LLMError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and paste your "
            "OpenRouter key after OPENROUTER_API_KEY= (get one at https://openrouter.ai/keys)."
        )
    return openai.OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=0,  # chat() does its own 429 retries; don't stack the SDK's on top
    )


def fallback_models(model: str | None = None) -> list[str]:
    """The models to try, in order: ``model`` (if given), then the defaults.

    ``OPENROUTER_MODEL`` (from the environment or ``.env``) replaces the first default.
    Duplicates are dropped and the list is capped at MAX_MODELS.
    """
    load_dotenv(ENV_FILE, override=False)
    defaults = list(DEFAULT_MODELS)
    env_model = os.environ.get("OPENROUTER_MODEL", "").strip()
    if env_model:
        defaults[0] = env_model
    ordered = [model, *defaults] if model else defaults
    unique = list(dict.fromkeys(ordered))
    return unique[:MAX_MODELS]


def chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.3,
    **kwargs: Any,
) -> str:
    """Send ``messages`` to OpenRouter and return the reply text.

    Args:
        messages: Chat messages, e.g. ``[{"role": "user", "content": "Hi"}]``.
        model: Preferred model; the default fallbacks are tried after it.
        temperature: 0 for consistent answers, higher for more variety.
        **kwargs: Passed to ``chat.completions.create`` (e.g. ``max_tokens=200``).

    Raises:
        LLMError: Still rate-limited after MAX_ATTEMPTS tries, or the reply was empty.
        openai.APIError: Any other API failure (bad key, unknown model, ...).
    """
    models = fallback_models(model)
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = get_client().chat.completions.create(
                model=models[0],
                messages=messages,
                temperature=temperature,
                extra_body={"models": models},
                **kwargs,
            )
            break
        except openai.RateLimitError as error:
            if attempt == MAX_ATTEMPTS - 1:
                raise LLMError(
                    f"OpenRouter rate limit: gave up after {MAX_ATTEMPTS} tries. Free models "
                    "allow 20 requests/minute and 50/day; wait a minute or try again tomorrow."
                ) from error
            time.sleep(BACKOFF_SECONDS[attempt])

    content = response.choices[0].message.content
    if not content:
        raise LLMError("The model returned an empty reply. Try again or use another model.")
    return str(content)


def ask(prompt: str, system: str | None = None, **kwargs: Any) -> str:
    """One-question shortcut over :func:`chat`: optional system prompt + one user message."""
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages, **kwargs)
