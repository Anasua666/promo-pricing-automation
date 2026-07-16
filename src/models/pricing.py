"""Core domain models for the pricing/promotion submission & approval cycle."""
from __future__ import annotations

from datetime import date, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Channel(str, Enum):
    """Derived from the sub number: STORE-only, DIRECT(.com)-only, or BOTH."""

    STORE = "STORE"
    DIRECT = "DIRECT"
    BOTH = "BOTH"


class SubmissionStatus(str, Enum):
    UPLOADED = "UPLOADED"          # raw row landed in DB, not yet verified
    VERIFIED = "VERIFIED"          # matched against fiscal calendar/price files
    FLAGGED = "FLAGGED"            # mismatch found, needs review
    SUBMITTED = "SUBMITTED"        # written to pending/ folder
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING_REVIEW = "PENDING_REVIEW"


class WeekStatus(str, Enum):
    """UI color coding for how far out a price point's week is."""

    CURRENT = "RED"        # current week
    NEAR = "PINK"          # +1-2 weeks out
    MID = "GREEN"          # +3 weeks out
    FAR = "YELLOW"         # +4-5 weeks out


def week_status(item_start_date: date, today: Optional[date] = None) -> WeekStatus:
    """Map a price point's start date to the same color coding used in the UI."""
    today = today or date.today()
    weeks_out = (item_start_date - today).days // 7

    if weeks_out <= 0:
        return WeekStatus.CURRENT
    if weeks_out <= 2:
        return WeekStatus.NEAR
    if weeks_out == 3:
        return WeekStatus.MID
    return WeekStatus.FAR


class PricingLineItem(BaseModel):
    """A single row of uploaded pricing data."""

    sub_number: str = Field(..., description="e.g. '6650'")
    brand: str
    division: str
    sub_division: Optional[str] = None
    channel: Channel
    start_date: date
    end_date: date
    price: float
    was_price: Optional[float] = None

    @property
    def status_color(self) -> WeekStatus:
        return week_status(self.start_date)


class PricingSubmission(BaseModel):
    """A verified weekly package for one sub/brand, ready for the approval queue."""

    submission_id: str
    fiscal_week: str  # e.g. "2026-W29"
    quarter: str
    division: str
    sub_division: Optional[str] = None
    sub_number: str
    channel: Channel
    line_items: list[PricingLineItem]
    status: SubmissionStatus = SubmissionStatus.UPLOADED
    verification_notes: list[str] = Field(default_factory=list)
    submitted_at: Optional[date] = None
    reviewed_at: Optional[date] = None
    rejection_reason: Optional[str] = None
