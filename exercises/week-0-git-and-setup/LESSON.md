# Week 0: Git, your branch, and your first model call

This week has no AI theory. You set up your machine, learn how work moves through this
repo, get an OpenRouter key, and hand in your first (tiny) pull request. Every later
week depends on this going smoothly, so take your time.

## What you'll learn

- What a git branch is, and how this repo uses branches so four people can work
  without stepping on each other.
- Why `main` is off limits to you, and how to check your branch before you push.
- How to set up the repo on Windows (PowerShell) and on macOS/Linux.
- How to get a free OpenRouter API key and keep it safe.
- How to open a pull request into **your own branch**, never into `main`.

## Concepts

### Branches in one minute

A **commit** is a saved snapshot of the files. A **branch** is just a movable label
that points at a commit. When you commit on a branch, the label moves forward to the
new commit. Other branches don't change.

```
main                 A---B---C                 (trainer adds lessons here)
                              \
trainee/amina                  C---D---E       (Amina's approved work)
                                        \
trainee/amina-week-0                     E---F (this week's work, in a PR)
```

**Merging** brings the commits from one branch into another. A **pull request (PR)**
is a GitHub page that says "please merge my branch into that branch", where someone
can review the changes first.

### How this repo works

| Branch | Who writes to it | What's on it |
|---|---|---|
| `main` | Trainer only | Lessons, exercises, the mini-EDRMS |
| `trainee/<name>` | Trainer merges your approved PRs | Your finished work, week by week |
| `trainee/<name>-week-<N>` | You | This week's work, until it's approved |

Each week you:

1. Merge `origin/main` into `trainee/<name>` to get the new lesson.
2. Create `trainee/<name>-week-<N>` from it and do the work there.
3. Open a PR with **base `trainee/<name>`** and **compare `trainee/<name>-week-<N>`**.

> Why `trainee/amina-week-0` and not `trainee/amina/week-0`? Git stores branch names
> like file paths, so it can't have both a branch `trainee/amina` and a "folder"
> `trainee/amina/...`. A dash avoids the clash.

### Never push to `main`

Never push to main. Nothing technically stops you, so check your branch with
`git branch --show-current` before every push. If you push to main by mistake, tell
the trainer straight away. Don't try to fix it yourself.

### OpenRouter: one key, many models

From week 1 you call AI models through **OpenRouter**, one API in front of hundreds of
models. Models whose ID ends in `:free` cost nothing. You need an OpenRouter key (free,
no credit card), not an OpenAI or Google key.

The free tier allows **20 requests per minute and 50 per day**. That's plenty for
learning if you don't run calls in a loop.

Full guide: [docs/reference/openrouter-getting-started.md](../../docs/reference/openrouter-getting-started.md).
Read sections 1 to 3 now.

Two rules that never bend:

1. **Never commit your key.** It lives in `.env`, which git ignores. If a key leaks,
   delete it at <https://openrouter.ai/keys> straight away and create a new one.
2. **Never send real client data to a free model.** Free providers may keep your
   prompts. Use made-up names, numbers and documents only, like the samples in this repo.

## Code walkthrough

### 1. Set up the repo

**macOS / Linux / Git Bash:**

```bash
git clone https://github.com/alvinkabwama/octech-ai-training.git
cd octech-ai-training
make setup                 # creates .venv and installs everything
cp .env.example .env       # then open .env and paste your key after OPENROUTER_API_KEY=
git checkout trainee/<your-name>
```

**Windows PowerShell** (no `make`):

```powershell
git clone https://github.com/alvinkabwama/octech-ai-training.git
cd octech-ai-training
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e ".[dev]"
Copy-Item .env.example .env
git checkout trainee/<your-name>
```

Check it worked: `make test` (PowerShell: `.venv\Scripts\python -m pytest`) should end
with `passed`.

### 2. Get your OpenRouter key

1. Sign up at <https://openrouter.ai>.
2. **Settings → Privacy:** allow free model endpoints. Skip this and every call fails with
   `No endpoints found matching your data policy`.
3. **Keys → Create Key**, name it `octech-training-<your-name>`, and copy it (it is shown once).
4. Paste it into `.env`:

```
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/free
```

### 3. Your first model call

Every exercise talks to models through one small helper, `exercises/common/llm.py`.
The week 0 live script is three lines of real work:

```python
from exercises.common import llm

reply = llm.ask("Say hello in Luganda")
print(reply)
```

`llm.ask()` reads your key from `.env`, sends the question to OpenRouter with a list of
free fallback models, waits and retries if you hit the rate limit, and returns the reply
text. Run it:

```bash
make live WEEK=0
# PowerShell: .venv\Scripts\python scripts\run_week.py live 0
```

If the key is missing you get a message telling you exactly which variable to set.

### 4. How your homework is checked

Open `starter/about_me.py`. It has three values set to `TODO`. The tests in
`tests/test_about_me.py` load your file and check each value, for example:

```python
def test_ai_idea_is_at_least_8_words(about_me):
    words = str(about_me.AI_IDEA).split()
    assert len(words) >= 8
```

Run them with:

```bash
make check WEEK=0
# PowerShell: .venv\Scripts\python scripts\run_week.py check 0
```

Right now they fail. That's expected: tests that fail until the work is done tell you
when you're finished. Exercise tests never call a real model, so they never use your
free requests.

## Assignment (homework)

1. Set up the repo and your `.env` (steps 1 and 2 above).
2. Get this week's lesson into your branch and start your week branch:
   ```bash
   git checkout trainee/<your-name>
   git fetch origin
   git merge origin/main
   git checkout -b trainee/<your-name>-week-0
   ```
3. Edit `exercises/week-0-git-and-setup/starter/about_me.py`:
   - `NAME`: your first name.
   - `PRODUCT_I_WORK_ON`: exactly one of `"EDRMS"`, `"QMS"`, `"CRM"`, `"CMMCS"`,
     `"QA tool"`, `"chatbot"`, `"voice"`, `"other"`.
   - `AI_IDEA`: one sentence (8+ words) describing an AI feature for that product.
4. Run `make check WEEK=0` until it passes, and `make ci` until it's clean.
5. Run `make live WEEK=0` and keep the reply for your PR.
6. Commit, push and open the PR:
   ```bash
   git add exercises/week-0-git-and-setup/starter/about_me.py
   git commit -m "feat: week 0 about me"
   git push -u origin trainee/<your-name>-week-0
   ```
   On GitHub, **change the base to `trainee/<your-name>`** before you click
   "Create pull request".

## Show your work (checkpoint)

Copy this list into your PR description and tick each item:

- [ ] PR base is `trainee/<my-name>` (not `main`), compare is `trainee/<my-name>-week-0`
- [ ] `make check WEEK=0` passes (paste the last line of the output)
- [ ] `make ci` is clean
- [ ] OpenRouter key works: `make live WEEK=0` printed a Luganda greeting (paste it)
- [ ] `.env` is not in the PR's "Files changed"
- [ ] I can explain in one sentence why we never push to `main`

## Stretch

- Run `git log --oneline --graph --all` and find your week branch, your trainee branch
  and `main` in the picture.
- Change `OPENROUTER_MODEL` in `.env` to `google/gemma-4-31b-it:free`, run
  `make live WEEK=0` again, and compare the greeting.

## How the real chatbot does this

> The production chatbot is several services (an API gateway, the AI pipeline, a vector
> store, a mock core-banking system and a web frontend) that start together with one
> `docker compose up` command. A single `ENVIRONMENT` setting in `.env` switches between
> local, dev and production configuration. Its model keys come from a secret store, never
> from the code, and every change reaches the main branch only through a reviewed PR.
> Same habits as this week, at a bigger scale.
