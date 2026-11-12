# Octech AI training - common commands.
# Works on Linux, macOS and Git Bash on Windows.

ifeq ($(OS),Windows_NT)
VENV_BIN := .venv/Scripts
else
VENV_BIN := .venv/bin
endif

PYTHON ?= python3
PY := $(VENV_BIN)/python

.PHONY: setup run test fix ci samples

setup:
	$(PYTHON) -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"
	git config core.hooksPath scripts/hooks

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
