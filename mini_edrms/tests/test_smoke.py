"""Smoke test: the package is importable."""

import importlib


def test_package_imports() -> None:
    module = importlib.import_module("mini_edrms.app")
    assert module is not None
