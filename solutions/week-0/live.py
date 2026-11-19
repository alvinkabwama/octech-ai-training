"""Week 0 live check: one real OpenRouter call.

This file is the same as `exercises/week-0-git-and-setup/starter/live.py`. You did not need
to change it in week 0; it is copied here (with comments) so the trainer can run the whole
reference solution with:
    make live WEEK=0 STARTER=solutions/week-0

Needs OPENROUTER_API_KEY in .env. Uses 1 of your 50 free requests for today.
"""

# sys gives us sys.stderr (where error messages go) and sys.exit (the exit code).
import sys

# The shared helper. Every exercise talks to models through it, never directly.
from exercises.common import llm


def main() -> int:
    """Ask one question, print the reply, and return 0 on success or 1 on failure."""
    try:
        # llm.ask() reads the key from .env, sends one user message to OpenRouter (trying
        # the free fallback models in turn and waiting on rate limits) and returns the text.
        reply = llm.ask("Say hello in Luganda")
    except llm.LLMError as error:
        # LLMError covers a missing key, every model failing, or a bad response. Print a
        # readable message to stderr instead of a long traceback, and return 1 (failure).
        print(f"Live call failed: {error}", file=sys.stderr)
        return 1
    print(reply)
    # 0 means "success" to the terminal and to scripts that run this one.
    return 0


# This block only runs when the file is executed directly (python live.py), not when
# another file imports it. sys.exit() passes main()'s return value back as the exit code.
if __name__ == "__main__":
    sys.exit(main())
