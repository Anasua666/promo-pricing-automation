"""Notify merchants by email when their submission is rejected."""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from src.config import settings
from src.models.pricing import PricingSubmission


def send_rejection_email(submission: PricingSubmission, merchant_email: str) -> None:
    """Send a rejection notice to the merchant. Wire up real SMTP/SES creds
    in .env before using this in production.
    """
    body = (
        f"Your pricing submission for fiscal week {submission.fiscal_week} "
        f"(division: {submission.division}, sub number: {submission.sub_number}, "
        f"channel: {submission.channel.value}) was rejected.\n\n"
        f"Reason: {submission.rejection_reason}\n\n"
        f"Please correct the data and resubmit."
    )
    msg = MIMEText(body)
    msg["Subject"] = f"Pricing submission rejected — {submission.fiscal_week} / {submission.sub_number}"
    msg["From"] = settings.email_from
    msg["To"] = merchant_email

    if not settings.smtp_host:
        # No SMTP configured yet — log instead of failing, so local/dev runs
        # don't crash before the real mail provider is wired up.
        print(f"[email_tools] SMTP not configured. Would send:\n{msg}")
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.email_from, [merchant_email], msg.as_string())
