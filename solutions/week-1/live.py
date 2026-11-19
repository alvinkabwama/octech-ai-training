"""Week 1 live run: prompts.py against real OpenRouter models.

This file is the same as `exercises/week-1-calling-a-model/starter/live.py`. You did not
need to change it; it is copied here (with comments) so the trainer can run the reference
solution against real models with:
    make live WEEK=1 STARTER=solutions/week-1

Uses about 5 of your 50 free requests for today. All messages are made up.
"""

import sys

# `prompts` is the prompts.py next to this file. scripts/run_week.py puts this folder on
# the import path, so the same live.py works with your starter or with this solution.
from prompts import classify, explain, extract

# The helper's error type for "the model call failed" (no key, all models down, ...).
from exercises.common.llm import LLMError

# Three made-up customer messages, one for each of three different categories.
MESSAGES = (
    "My debit card was swallowed by the ATM this morning.",
    "How much can I borrow for a small business loan?",
    "The mobile app logs me out every time I open it.",
)

# A made-up note with every field extract() should find: a name, a phone number, an issue
# and clear urgency ("today"). "Testperson" and 0700 000 001 are deliberately fake.
CUSTOMER_NOTE = (
    "Hi, this is Amina Testperson on 0700 000 001. I was charged twice for the same "
    "transfer yesterday and I need the money back today, please help."
)


def main() -> int:
    """Run each pattern once against real models. Return 0 on success, 1 on failure."""
    try:
        # Pattern 1: 1 request.
        print("explain():")
        print(explain("what an API is", "a records clerk who has never programmed"))

        # Pattern 2: 3 requests. :<15 pads the label to 15 characters so the arrows line up.
        print("\nclassify():")
        for message in MESSAGES:
            print(f"  {classify(message):<15} <- {message}")

        # Pattern 3: 1 request, or 2 if the first reply needed the retry.
        print("\nextract():")
        print(f"  {extract(CUSTOMER_NOTE)}")
    except NotImplementedError as error:
        # The starter functions raise NotImplementedError until they are written.
        print(f"Not done yet: {error}. Finish starter/prompts.py first.", file=sys.stderr)
        return 1
    except LLMError as error:
        # A failed model call: show the reason without a traceback.
        print(f"Live call failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
