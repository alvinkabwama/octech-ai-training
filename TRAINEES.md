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
   git clone <repo-url>
   cd octech-ai-training
   make setup          # PowerShell: see README "Windows PowerShell"
   cp .env.example .env   # then paste your OpenRouter key into .env
   ```
3. Switch to your branch (it already exists):
   ```bash
   git checkout trainee/<your-name>
   ```

`make setup` also installs a safety hook that stops you pushing to `main` by accident.

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
   make test
   make ci
   ```
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

- Never open a PR into `main`. Never push to `main`.
- Never commit `.env`, API keys or real client data. Samples are synthetic only.
- Don't copy another person's branch. Reading their merged PRs to learn is fine.
- Stuck for more than 30 minutes? Push what you have, open the PR as a **draft**, and
  ask your question in it.

## How you're assessed each week

1. The week's tests pass (`make test`).
2. Every item in the week's "Show your work" checkpoint is done.
3. The trainer approves your PR after review.
4. Weeks 6-8: a short live demo.
