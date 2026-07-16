"""Compare the merchant-supplied fiscal calendar / price Excel files against
the pricing data already uploaded to the DB. This is what the verification
team does manually today.
"""
from __future__ import annotations

import pandas as pd

from src.models.pricing import PricingSubmission


def load_fiscal_calendar(path: str) -> pd.DataFrame:
    """Load the fiscal calendar sheet: which dates map to which fiscal week,
    and whether that week's prices apply to ECOM, STORE, or BOTH.
    """
    return pd.read_excel(path)


def load_price_file(path: str) -> pd.DataFrame:
    """Load the merchant price file: expected price points per
    division/sub-division/sub-number for the week."""
    return pd.read_excel(path)


def verify_submission_against_files(
    submission: PricingSubmission,
    fiscal_calendar: pd.DataFrame,
    price_file: pd.DataFrame,
) -> list[str]:
    """Compare a grouped submission's line items against the expected values
    in the merchant-supplied files. Returns a list of mismatch notes — empty
    list means everything matched.

    NOTE: the exact column names below are placeholders. Update them to match
    your real fiscal_calendar.xlsx / price_file.xlsx column headers.
    """
    notes: list[str] = []

    expected_rows = price_file[
        (price_file["division"] == submission.division)
        & (price_file["sub_number"] == submission.sub_number)
    ]

    if expected_rows.empty:
        notes.append(
            f"No matching rows found in price file for division="
            f"{submission.division}, sub_number={submission.sub_number}"
        )
        return notes

    for item in submission.line_items:
        match = expected_rows[
            (expected_rows["start_date"] == pd.Timestamp(item.start_date))
            & (expected_rows["price"] == item.price)
        ]
        if match.empty:
            notes.append(
                f"Line item start_date={item.start_date} price={item.price} "
                f"not found in price file for sub_number={submission.sub_number}"
            )

    week_rows = fiscal_calendar[fiscal_calendar["fiscal_week"] == submission.fiscal_week]
    if week_rows.empty:
        notes.append(f"Fiscal week {submission.fiscal_week} not found in fiscal calendar")

    return notes
