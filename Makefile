# Octech AI training - common commands.
# Works on Linux, macOS and Windows (make is optional; see README "Installing make").

ifeq ($(OS),Windows_NT)
VENV_BIN := .venv/Scripts
PYTHON ?= python
else
VENV_BIN := .venv/bin
endif

PYTHON ?= python3
PY := $(VENV_BIN)/python

.PHONY: setup run test fix ci samples check live

setup:
	$(PYTHON) -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

run:
	$(PY) -m uvicorn mini_edrms.app.main:app --reload

test:
	$(PY) -m pytest

fix:
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

ci:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	$(PY) -m pytest

samples:
	$(PY) mini_edrms/samples/build_samples.py

# One week's exercise tests (stubbed: never calls a model). Fails until you finish the TODOs.
# Trainer: add STARTER=solutions/week-<N> to check a reference solution instead.
check:
	$(if $(WEEK),,$(error Usage: make check WEEK=<N>   e.g. make check WEEK=1))
	$(PY) scripts/run_week.py check $(WEEK) $(if $(STARTER),--starter $(STARTER))

# Run one week's starter/live.py against real OpenRouter (needs OPENROUTER_API_KEY in .env).
live:
	$(if $(WEEK),,$(error Usage: make live WEEK=<N>   e.g. make live WEEK=0))
	$(PY) scripts/run_week.py live $(WEEK) $(if $(STARTER),--starter $(STARTER))
