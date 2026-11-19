"""Week 0 reference solution: about_me.py.

Compare this with your own `exercises/week-0-git-and-setup/starter/about_me.py`.
The tests (`exercises/week-0-git-and-setup/tests/test_about_me.py`) only check the shape of
each value, so your NAME, product and idea will be different. That's expected.

Check this file against the week 0 tests with:
    make check WEEK=0 STARTER=solutions/week-0
    PowerShell: .venv\\Scripts\\python scripts\\run_week.py check 0 --starter solutions/week-0
"""

# NAME: your first name as a plain string.
# The test only checks that it is not empty and no longer starts with "TODO".
NAME = "Trainer"

# PRODUCT_I_WORK_ON: must match one of the allowed values EXACTLY, including capitals and
# spaces ("QA tool", not "qa tool" or "QA Tool"). Code that compares strings is strict, so
# copy the value from the list in the starter instead of retyping it.
PRODUCT_I_WORK_ON = "EDRMS"

# AI_IDEA: one sentence, at least 8 words, describing an AI feature for that product.
# A good idea names WHO it helps, WHAT the AI does and WHEN it happens. This one says the
# AI suggests a category and a department (what) for every scanned letter (when), which
# saves the registry clerk (who) from reading and sorting each letter by hand.
# Wrapping a long string in brackets lets Python join the two lines into one string
# without a "+" and keeps each line under the 100-character limit that ruff enforces.
AI_IDEA = (
    "Suggest a file-plan category and a routing department for every scanned letter "
    "as soon as it is uploaded, so the registry clerk only has to confirm it."
)
