"""
Shared fixtures and test helpers for ui/ tests.

client/RAW_ATTACK_FORM/make_semantic_result()/extract_hidden_field()/
extract_semantic_result_json()/extract_review_ids() were promoted here
from test_app.py once ui/app.py's own routes started splitting into
ui/routes/ (see tests/ui/routes/), so more than one test module needs
them -- same promotion pattern already used for
tests/pipeline/conftest.py.
"""
import html
import re
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.structured_data.dnd.v3x.enums import MoveType
from monsterforge.ui.app import app
from monsterforge.ui.dependencies import get_db_session

client = TestClient(app)

RAW_ATTACK_FORM = {"name": "Bite", "modifier": "+5", "attack_type": "melee", "attack_effect": "1d6+3"}

TEMPLATE_NAME = "attacks/classify_attack.jinja2"

REVIEW_HIDDEN_BASE = {
    "raw_attack_name": "Bite", "raw_attack_modifier": "+5",
    "raw_attack_attack_type": "melee", "raw_attack_attack_effect": "1d6+3",
    "template_name": TEMPLATE_NAME,
}


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious bite.",
        move_type=MoveType.PHYSICAL,
        move_range=None,
        confidence=0.4,
        rationale="test rationale",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


def extract_hidden_field(page_html: str, field_name: str) -> str:
    """
    Matches a hidden input's value in either of its two rendered forms:
    single-quoted and raw (review_form.html.jinja2) or double-quoted and
    HTML-entity-escaped (move_card_with_edit.html.jinja2, which escapes
    it to keep an embedded value's own quotes from breaking the
    attribute). html.unescape() is a no-op on already-plain text, so
    it's safe to apply unconditionally regardless of which form matched.
    """
    match = re.search(rf"name=\"{field_name}\" value=(['\"])(.*?)\1", page_html)
    assert match is not None, f"page did not include the expected hidden field {field_name!r}"
    return html.unescape(match.group(2))


def extract_semantic_result_json(page_html: str) -> str:
    return extract_hidden_field(page_html, "semantic_result_json")


def extract_review_ids(page_html: str) -> dict:
    """raw_field_id/classification_event_id, needed on every /review and
    /review/edit POST since the database wiring — extracted from a prior
    /convert (or /review) response the same way semantic_result_json is."""
    return {
        "raw_field_id": extract_hidden_field(page_html, "raw_field_id"),
        "classification_event_id": extract_hidden_field(page_html, "classification_event_id"),
    }


def review_page_html(confidence=0.3, **result_overrides):
    """POST /convert with a low (or forced) confidence to land on
    review_form.html.jinja2, returning its rendered HTML -- the setup
    sequence most /review and library/reopen tests need at least once.
    Promoted here from test_app.py once tests/ui/routes/test_review.py
    needed it too, same reasoning as the other helpers above."""
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(
            confidence=confidence, **result_overrides)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    return response.text


@pytest.fixture(autouse=True)
def _override_db_session(seeded_db_session):
    """Replace the app's real database dependency with the isolated,
    already-seeded in-memory session for every test in this package —
    autouse so the 41+ existing route tests don't each need to opt in
    individually. Real lifespan()/get_session() are never touched."""
    def _yield_test_session():
        yield seeded_db_session

    app.dependency_overrides[get_db_session] = _yield_test_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _mock_llm_client():
    """record_llm_run() reads get_llm_client().model_name for logging —
    unlike classify_attack() (mocked per test), this is a real call the
    existing tests never anticipated, and it tries to build a real
    GeminiClient requiring a real GEMINI_API_KEY. Autouse so none of the
    41+ existing tests need their own patch for a call they don't
    otherwise care about.

    get_llm_client is imported separately into ui.routes.review
    (review()'s rerun branch) and ui.routes.convert (convert()) —
    patch, being a name-binding replacement rather than a global one,
    has to target each import site on its own, so both are patched
    here."""
    with (
        patch("monsterforge.ui.routes.review.get_llm_client") as mock_get_client_review,
        patch("monsterforge.ui.routes.convert.get_llm_client") as mock_get_client_convert,
    ):
        mock_get_client_review.return_value.model_name = "test-model"
        mock_get_client_convert.return_value.model_name = "test-model"
        yield
