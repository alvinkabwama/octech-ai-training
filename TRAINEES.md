# How you work in this repo

Everyone works in this one repo. You never change `main`; only the trainer does.
You each have your own branch, and you hand in each week's work as a pull request (PR)
into **your own branch**.

```
main                       <- trainer only: lessons, exercises, mini-EDRMS
trainee/rachel             <- Rachel's approved work
trainee/rachel-week-1      <- where Rachel does week 1 (deleted after merge)
trainee/tracy
trainee/owen
trainee/simon
```

## Day 1 (once)

1. Accept the GitHub invitation to the repo.
2. Clone it and set it up:
   ```bash
   git clone https://github.com/alvinkabwama/octech-ai-training.git
   cd octech-ai-training
   make setup          # PowerShell: see README "Windows PowerShell"
   cp .env.example .env   # then paste your OpenRouter key into .env
   ```
3. Switch to your branch (it already exists):
   ```bash
   git checkout trainee/<your-name>
   ```

### Installing make (optional)

`make` is optional. Every `make` command has a PowerShell equivalent (see README), so
Windows users can skip installing it.

- Windows: `winget install ezwinports.make`, then close and reopen the terminal
- macOS: `xcode-select --install`
- Ubuntu/Debian: `sudo apt install make`

Check it worked with `make --version`.

## Every week

1. **Get the new week from `main`** into your branch:
   ```bash
   git checkout trainee/<your-name>
   git pull                      # your branch, in case the trainer merged your last PR
   git fetch origin
   git merge origin/main         # brings in the new week's lesson and exercise
   git push
   ```
2. **Start a week branch** from your branch:
   ```bash
   git checkout -b trainee/<your-name>-week-<N>
   ```
3. **Do the work.** Read `exercises/week-<N>-*/LESSON.md`, then do the assignment.
   Commit often with clear messages (`feat: add memory to chatbot`).
4. **Check it** before you hand in:
   ```bash
   make check WEEK=<N>   # this week's exercise tests (they fail until your work is done)
   make ci               # lint, format check and the main test suite
   make live WEEK=<N>    # run your code against real OpenRouter models
   ```
   Windows PowerShell (no `make`):
   ```powershell
   .venv\Scripts\python scripts\run_week.py check <N>
   .venv\Scripts\python -m ruff check . ; .venv\Scripts\python -m ruff format --check . ; .venv\Scripts\python -m pytest
   .venv\Scripts\python scripts\run_week.py live <N>
   ```
   `make check` never calls a model, so it never uses your free OpenRouter requests.
5. **Push** your week branch:
   ```bash
   git push -u origin trainee/<your-name>-week-<N>
   ```
6. **Open the PR on GitHub.** Click "Compare & pull request", then **change the base**:
   - **base: `trainee/<your-name>`**  <- GitHub picks `main` by default. Change it.
   - **compare: `trainee/<your-name>-week-<N>`**

   Fill in the template (it has the checkpoint list) and click "Create pull request".
7. **Respond to review.** The trainer comments on your PR. Push more commits to the same
   week branch to answer comments; the PR updates itself.
8. **Approved?** The trainer merges it into `trainee/<your-name>`. You can delete the
   week branch.

## Rules

- Never open a PR into `main`.
- Never push to main. Nothing technically stops you, so check your branch with
  `git branch --show-current` before every push. If you push to main by mistake, tell
  the trainer straight away. Don't try to fix it yourself.
- Never commit `.env`, API keys or real client data. Samples are synthetic only.
- Don't copy another person's branch. Reading their merged PRs to learn is fine.
- Stuck for more than 30 minutes? Push what you have, open the PR as a **draft**, and
  ask your question in it.

## How you're assessed each week

1. The week's tests pass (`make check WEEK=<N>`) and `make ci` is clean.
2. Every item in the week's "Show your work" checkpoint is done.
3. The trainer approves your PR after review.
4. Weeks 6-8: a short live demo.
