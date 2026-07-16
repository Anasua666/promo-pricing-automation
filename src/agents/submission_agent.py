"""Submission Agent: verifies uploaded pricing data against the merchant's
fiscal calendar + price files, then submits verified packages to the
pending/ folder for approval.
"""
from __future__ import annotations

from langchain_aws import ChatBedrock

from src.config import settings
from src.models.pricing import PricingSubmission, SubmissionStatus
from src.tools import excel_tools, file_tools

SYSTEM_PROMPT = """You are the pricing submission verification agent.
You are given a grouped pricing submission (one division/sub-division/sub \
number/channel for a fiscal week) plus a list of any mismatches found when \
comparing it against the merchant's fiscal calendar and price files.

Decide whether the submission is safe to auto-submit:
- If there are no mismatches, approve it for submission.
- If there are mismatches, explain in one or two sentences what's wrong and \
  whether it looks like a data entry error, a timing issue (wrong fiscal \
  week), or something that needs a human to look at.

Respond concisely. This explanation will be shown to the pricing team."""


def _get_llm() -> ChatBedrock:
    return ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.bedrock_region,
    )


def verify_and_submit(submission: PricingSubmission) -> PricingSubmission:
    """Run verification for one submission and, if clean, write it to the
    pending folder. Mutates and returns the submission with updated status.
    """
    fiscal_calendar = excel_tools.load_fiscal_calendar(settings.fiscal_calendar_xlsx)
    price_file = excel_tools.load_price_file(settings.price_file_xlsx)

    mismatches = excel_tools.verify_submission_against_files(
        submission, fiscal_calendar, price_file
    )

    if not mismatches:
        submission.status = SubmissionStatus.SUBMITTED
        file_tools.write_pending_submission(submission)
        return submission

    # TODO: decide your policy here. Options:
    #   1) Auto-flag and stop (current behavior below) — safest default.
    #   2) Ask the LLM (via _get_llm()) to classify severity and
    #      auto-submit only "minor/likely-timing" mismatches.
    submission.status = SubmissionStatus.FLAGGED
    submission.verification_notes = mismatches
    return submission
