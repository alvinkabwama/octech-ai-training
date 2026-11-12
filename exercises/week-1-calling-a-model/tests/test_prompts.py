"""Week 1 checks for starter/prompts.py. Run with `make check WEEK=1`.

The model is faked (fake_llm): each test queues the reply the "model" will give, then
checks what your function sent and what it returned. No real calls, no free requests used.
"""

import json
import re
from collections.abc import Callable
from types import ModuleType

import pytest

from exercises.common.testing import FakeClient

CATEGORIES = ("card_issue", "loan_enquiry", "mobile_banking", "complaint", "other")
GOOD_EXTRACT = {
    "name": "Amina Testperson",
    "phone": "0700 000 001",
    "issue": "ATM kept her card",
    "urgency": "high",
}


@pytest.fixture
def prompts(load_starter: Callable[[str], ModuleType]) -> ModuleType:
    return load_starter("prompts")


def _all_text(fake: FakeClient, call: int = 0) -> str:
    return "\n".join(str(m["content"]) for m in fake.calls[call]["messages"])


# --- explain ------------------------------------------------------------------


def test_explain_returns_model_reply(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("An API lets two programs talk.")

    assert prompts.explain("APIs", "a records clerk") == "An API lets two programs talk."


def test_explain_sends_system_prompt_with_length_rule(
    prompts: ModuleType, fake_llm: FakeClient
) -> None:
    fake_llm.queue("ok")

    prompts.explain("APIs", "a records clerk")

    messages = fake_llm.calls[0]["messages"]
    assert messages[0]["role"] == "system", "the first message should be the system prompt"
    assert re.search(r"\b(3|three)\s+sentences\b", messages[0]["content"], re.IGNORECASE), (
        "the system prompt should say: 3 sentences or fewer"
    )


def test_explain_includes_topic_and_audience(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("ok")

    prompts.explain("retention schedules", "a new registry assistant")

    text = _all_text(fake_llm)
    assert "retention schedules" in text
    assert "a new registry assistant" in text


# --- classify -----------------------------------------------------------------


def test_categories_constant(prompts: ModuleType) -> None:
    assert tuple(prompts.CATEGORIES) == CATEGORIES


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("Loan_Enquiry.", "loan_enquiry"),
        ("banana", "other"),
        ("  card_issue\n", "card_issue"),
        ('"complaint"', "complaint"),
    ],
)
def test_classify_normalises_reply(
    prompts: ModuleType, fake_llm: FakeClient, reply: str, expected: str
) -> None:
    fake_llm.queue(reply)

    assert prompts.classify("I want a loan for school fees") == expected


def test_classify_uses_temperature_zero(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("complaint")

    prompts.classify("You charged me twice!")

    assert fake_llm.calls[0]["temperature"] == 0


def test_classify_prompt_lists_every_category(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("other")

    prompts.classify("Hello")

    text = _all_text(fake_llm)
    for category in CATEGORIES:
        assert category in text, f"the prompt should list {category!r}"
    assert "Hello" in text


def test_classify_makes_one_call(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("mobile_banking")

    prompts.classify("My app won't log in")

    assert len(fake_llm.calls) == 1


# --- extract ------------------------------------------------------------------


def test_extract_parses_fenced_json(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue(f"```json\n{json.dumps(GOOD_EXTRACT)}\n```")

    assert prompts.extract("Amina here, 0700 000 001, the ATM kept my card!") == GOOD_EXTRACT


def test_extract_parses_plain_json(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue(json.dumps(GOOD_EXTRACT))

    assert prompts.extract("...") == GOOD_EXTRACT


def test_extract_allows_null_name_and_phone(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue(json.dumps({"name": None, "phone": None, "issue": "Fees", "urgency": "low"}))

    result = prompts.extract("Why are my fees so high?")

    assert result["name"] is None and result["phone"] is None
    assert result["urgency"] == "low"


def test_extract_returns_only_the_four_fields(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue(json.dumps({**GOOD_EXTRACT, "mood": "angry"}))

    assert set(prompts.extract("...")) == {"name", "phone", "issue", "urgency"}


def test_extract_retries_once_on_bad_json(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("Sure! The customer is Amina and she is upset.", json.dumps(GOOD_EXTRACT))

    result = prompts.extract("Amina here, the ATM kept my card!")

    assert result == GOOD_EXTRACT
    assert len(fake_llm.calls) == 2
    retry_text = _all_text(fake_llm, call=1).lower()
    assert "json" in retry_text, "the retry should remind the model to reply with JSON only"


def test_extract_raises_after_second_failure(prompts: ModuleType, fake_llm: FakeClient) -> None:
    fake_llm.queue("not json", "still not json")

    with pytest.raises(ValueError):
        prompts.extract("...")

    assert len(fake_llm.calls) == 2, "retry exactly once, then give up"


def test_extract_rejects_unknown_urgency(prompts: ModuleType, fake_llm: FakeClient) -> None:
    bad = json.dumps({**GOOD_EXTRACT, "urgency": "critical"})
    fake_llm.queue(bad, bad)

    with pytest.raises(ValueError):
        prompts.extract("...")
