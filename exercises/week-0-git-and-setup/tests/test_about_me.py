"""Week 0 checks: starter/about_me.py is filled in. Run with `make check WEEK=0`."""

from collections.abc import Callable
from types import ModuleType

import pytest

ALLOWED_PRODUCTS = ("EDRMS", "QMS", "CRM", "CMMCS", "QA tool", "chatbot", "voice", "other")
MIN_IDEA_WORDS = 8


@pytest.fixture
def about_me(load_starter: Callable[[str], ModuleType]) -> ModuleType:
    return load_starter("about_me")


def _is_placeholder(value: object) -> bool:
    return not isinstance(value, str) or not value.strip() or "TODO" in value.upper()


def test_name_is_filled_in(about_me: ModuleType) -> None:
    assert not _is_placeholder(about_me.NAME), "Set NAME to your name in starter/about_me.py"


def test_product_is_from_allowed_list(about_me: ModuleType) -> None:
    assert about_me.PRODUCT_I_WORK_ON in ALLOWED_PRODUCTS, (
        f"PRODUCT_I_WORK_ON must be exactly one of {ALLOWED_PRODUCTS}, "
        f"got {about_me.PRODUCT_I_WORK_ON!r}"
    )


def test_ai_idea_is_filled_in(about_me: ModuleType) -> None:
    assert not _is_placeholder(about_me.AI_IDEA), "Write your AI_IDEA in starter/about_me.py"


def test_ai_idea_is_at_least_8_words(about_me: ModuleType) -> None:
    words = str(about_me.AI_IDEA).split()
    assert len(words) >= MIN_IDEA_WORDS, (
        f"AI_IDEA should be one full sentence of at least {MIN_IDEA_WORDS} words; "
        f"it has {len(words)}"
    )
