"""Smoke test: exercises the models + file_tools plumbing with mock data,
without needing a real DB or Bedrock credentials.
"""
from datetime import date

from src.models.pricing import (
    Channel,
    PricingLineItem,
    PricingSubmission,
    SubmissionStatus,
    week_status,
)


def make_mock_submission() -> PricingSubmission:
    line_item = PricingLineItem(
        sub_number="6650",
        brand="Example Brand",
        division="Mens",
        sub_division="Mens Active",
        channel=Channel.BOTH,
        start_date=date.today(),
        end_date=date.today().replace(day=28),
        price=19.99,
        was_price=29.99,
    )
    return PricingSubmission(
        submission_id="2026-W29-6650-BOTH",
        fiscal_week="2026-W29",
        quarter="Q3",
        division="Mens",
        sub_division="Mens Active",
        sub_number="6650",
        channel=Channel.BOTH,
        line_items=[line_item],
        status=SubmissionStatus.VERIFIED,
    )


def test_week_status_current_week_is_red():
    assert week_status(date.today()).value == "RED"


def test_submission_model_roundtrip():
    submission = make_mock_submission()
    as_json = submission.model_dump_json()
    restored = PricingSubmission.model_validate_json(as_json)
    assert restored.sub_number == "6650"
    assert restored.line_items[0].price == 19.99


if __name__ == "__main__":
    test_week_status_current_week_is_red()
    test_submission_model_roundtrip()
    print("All smoke tests passed.")
