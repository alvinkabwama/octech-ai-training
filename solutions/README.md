# Reference solutions

How each exercise should have been done, with every part of the code commented. A week
appears here only after its pull requests have been reviewed.

| Week | Code | Checkpoint answers and review notes |
|---|---|---|
| 0 | [week-0/about_me.py](week-0/about_me.py) | [week-0/ANSWERS.md](week-0/ANSWERS.md) |
| 1 | [week-1/prompts.py](week-1/prompts.py) | [week-1/ANSWERS.md](week-1/ANSWERS.md) |

Each `live.py` is the same as the starter's; it's here so the whole folder can be run.

## Using them

- **Do your own version first.** Read a solution after your PR is reviewed, not before.
  Copying it into your starter defeats the point, and the trainer will spot it.
- **Compare, don't replace.** Put the solution next to your file and look for anything
  you missed: a check, a retry, a comment.
- **Run the week's tests against a solution** (no model calls):
  ```bash
  make check WEEK=1 STARTER=solutions/week-1
  # PowerShell: .venv\Scripts\python scripts\run_week.py check 1 --starter solutions/week-1
  ```

## How solutions are published (trainer)

- Solutions are written on the long-lived `solutions` branch and reach `main` only through
  a pull request from `solutions` into `main`.
- `.gitignore` ignores everything in `solutions/` except the weeks listed there. A new
  week's solution stays on the trainer's machine until its line is added to `.gitignore`
  in that week's solutions PR.
