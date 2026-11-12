# Octech AI training

Practice repo for the Octech AI training programme. Contains the **mini-EDRMS**
practice app (no AI) that later weeks add AI features to, plus weekly exercises.

## Setup

Requires Python 3.10+.

```bash
make setup        # creates .venv and installs the project with dev tools
cp .env.example .env   # then add your OpenRouter key
```

## Commands

| Command        | What it does                                   |
|----------------|------------------------------------------------|
| `make run`     | Start the mini-EDRMS API on http://127.0.0.1:8000 |
| `make test`    | Run the tests                                  |
| `make fix`     | Format and auto-fix lint issues                |
| `make ci`      | Lint, format check and tests (what CI runs)   |
| `make samples` | Regenerate the synthetic sample documents      |
