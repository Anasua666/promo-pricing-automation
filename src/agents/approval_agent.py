"""Approval Agent: reviews submitted packages per channel (STORE vs DIRECT),
decides approve/reject/pending, moves files accordingly, and emails
merchants on rejection.
"""
from __future__ import annotations

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import settings
from src.models.pricing import Channel, PricingSubmission, SubmissionStatus
from src.tools import email_tools, file_tools

SYSTEM_PROMPT = """You are the pricing approval agent, reviewing a verified \
weekly pricing submission for a single sub number/channel.

Review the submission's line items (price, was_price, start/end dates) for \
red flags: prices that look like data entry errors (e.g. a decimal point \
error causing a 10x price jump), end dates before start dates, or price \
increases during a promo period that should be decreases.

Respond with exactly one of:
APPROVE
REJECT: <one sentence reason a merchant would understand>
PENDING: <one sentence reason more info/human review is needed>
"""


def _get_llm() -> ChatBedrock:
    return ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.bedrock_region,
    )


def _submission_summary(submission: PricingSubmission) -> str:
    lines = [
        f"Fiscal week: {submission.fiscal_week}, Division: {submission.division}, "
        f"Sub number: {submission.sub_number}, Channel: {submission.channel.value}"
    ]
    for item in submission.line_items:
        lines.append(
            f"  - {item.start_date} to {item.end_date}: price={item.price} "
            f"(was={item.was_price})"
        )
    return "\n".join(lines)


def review_submission(submission: PricingSubmission) -> PricingSubmission:
    """Ask the LLM to review one submission and act on its decision."""
    llm = _get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_submission_summary(submission)),
        ]
    )
    decision_text = response.content.strip()

    if decision_text.upper().startswith("APPROVE"):
        submission.status = SubmissionStatus.APPROVED
    elif decision_text.upper().startswith("REJECT"):
        submission.status = SubmissionStatus.REJECTED
        submission.rejection_reason = decision_text.split(":", 1)[-1].strip()
    else:
        submission.status = SubmissionStatus.PENDING_REVIEW

    return submission


def apply_decision(submission: PricingSubmission, file_path: str, merchant_email: str) -> None:
    """Move the file and send notifications based on submission.status."""
    if submission.status == SubmissionStatus.APPROVED:
        file_tools.move_to_approved(submission, file_path)
        notify_inference_job(submission)
    elif submission.status == SubmissionStatus.REJECTED:
        file_tools.move_to_rejected(submission, file_path)
        email_tools.send_rejection_email(submission, merchant_email)
    # PENDING_REVIEW: leave file in place for another pass / human escalation


def notify_inference_job(submission: PricingSubmission) -> None:
    """Hook for triggering the downstream per-channel inference job once a
    submission is approved. Wire this up to whatever mechanism you use
    (SQS message, HTTP webhook, Airflow trigger, etc.) — out of scope here.
    """
    # TODO: implement real trigger
    print(
        f"[approval_agent] Approved {submission.submission_id} "
        f"({submission.channel.value}) — ready for inference job."
    )


def review_pending_queue(fiscal_week: str, channel: Channel, merchant_email_lookup) -> list[PricingSubmission]:
    """Process every pending submission for a given channel's approval screen.

    merchant_email_lookup: callable(sub_number: str) -> str, so you can plug
    in your real merchant contact lookup.
    """
    results = []
    for file_path in file_tools.list_pending_submissions(fiscal_week, channel.value):
        submission = file_tools.load_submission(file_path)
        submission = review_submission(submission)
        merchant_email = merchant_email_lookup(submission.sub_number)
        apply_decision(submission, file_path, merchant_email)
        results.append(submission)
    return results
