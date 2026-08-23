"""
Tests for validation.review: needs_review() and the HumanReview record.
"""
import pytest
from monsterforge.config import validation_settings
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview, needs_review


@pytest.mark.parametrize("confidence, always_on, expected", [
    (0.9, False, False),  # high confidence, not forced -> no review
    (0.5, False, True),   # low confidence, not forced -> review
    (0.9, True, True),    # high confidence, forced -> review
    (0.5, True, True),    # low confidence, forced -> review
])
def test_needs_review_combinations(monkeypatch, confidence, always_on, expected):
    monkeypatch.setattr(validation_settings, "CONFIDENCE_THRESHOLD", 0.7)
    monkeypatch.setattr(validation_settings, "ALWAYS_ON", always_on)

    assert needs_review(confidence=confidence) is expected


def test_human_review_optional_fields_default_to_none():
    review = HumanReview(status=ValidationStatus.REJECTED, result=None)

    assert review.assigned_llm_score is None
    assert review.edit_note is None
