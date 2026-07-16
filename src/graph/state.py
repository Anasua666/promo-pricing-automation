"""Shared state passed between nodes in the LangGraph workflow."""
from __future__ import annotations

from typing import TypedDict

from src.models.pricing import PricingSubmission


class CycleState(TypedDict, total=False):
    fiscal_week: str
    quarter: str
    submissions: list[PricingSubmission]
    flagged: list[PricingSubmission]
    approved: list[PricingSubmission]
    rejected: list[PricingSubmission]
    pending: list[PricingSubmission]
