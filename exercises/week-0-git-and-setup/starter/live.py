"""Week 0 live check: one real OpenRouter call. Run with `make live WEEK=0`.

Needs OPENROUTER_API_KEY in .env (copy .env.example to .env first).
Uses 1 of your 50 free requests for today.
"""

import sys

from exercises.common import llm


def main() -> int:
    try:
        reply = llm.ask("Say hello in Luganda")
    except llm.LLMError as error:
        print(f"Live call failed: {error}", file=sys.stderr)
        return 1
    print(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
