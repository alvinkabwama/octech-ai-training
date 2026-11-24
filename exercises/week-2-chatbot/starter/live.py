"""Week 2 live run: a 3-turn conversation with your chatbot against real OpenRouter models.

Run with `make live WEEK=2` (PowerShell: .venv\\Scripts\\python scripts\\run_week.py live 2).
Uses 3 of your 50 free requests for today. The person below is made up.

Turn 3 only works if the bot remembers turn 1: that's the memory you built.
"""

import sys

from chatbot import new_session, reply, reply_stream

from exercises.common.llm import LLMError

TURNS = (
    "Hi, I'm Amina Testperson and I work in the registry team.",
    "In one sentence, what is a file plan?",
    "What's my name, and which team do I work in?",
)


def main() -> int:
    try:
        session = new_session()
        for number, text in enumerate(TURNS[:-1], start=1):
            print(f"\nYou ({number}): {text}")
            print(f"Bot: {reply(session, text)}")
        print(f"\nYou ({len(TURNS)}): {TURNS[-1]}")
        print("Bot (streamed): ", end="", flush=True)
        for piece in reply_stream(session, TURNS[-1]):
            print(piece, end="", flush=True)
        print()
    except NotImplementedError as error:
        print(f"Not done yet: {error}. Finish starter/chatbot.py first.", file=sys.stderr)
        return 1
    except LLMError as error:
        print(f"Live call failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
