"""Week 1 live run: your prompts.py against real OpenRouter models.

Run with `make live WEEK=1` (PowerShell: .venv\\Scripts\\python scripts\\run_week.py live 1).
Uses about 5 of your 50 free requests for today. All messages are made up.
"""

import sys

from prompts import classify, explain, extract

from exercises.common.llm import LLMError

MESSAGES = (
    "My debit card was swallowed by the ATM this morning.",
    "How much can I borrow for a small business loan?",
    "The mobile app logs me out every time I open it.",
)
CUSTOMER_NOTE = (
    "Hi, this is Amina Testperson on 0700 000 001. I was charged twice for the same "
    "transfer yesterday and I need the money back today, please help."
)


def main() -> int:
    try:
        print("explain():")
        print(explain("what an API is", "a records clerk who has never programmed"))
        print("\nclassify():")
        for message in MESSAGES:
            print(f"  {classify(message):<15} <- {message}")
        print("\nextract():")
        print(f"  {extract(CUSTOMER_NOTE)}")
    except NotImplementedError as error:
        print(f"Not done yet: {error}. Finish starter/prompts.py first.", file=sys.stderr)
        return 1
    except LLMError as error:
        print(f"Live call failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
