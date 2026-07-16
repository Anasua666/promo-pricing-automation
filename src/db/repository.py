"""Data access layer. Replace the stub bodies with real queries against your
pricing DB (the one your CSV upload scheduler job populates).
"""
from __future__ import annotations

from datetime import date

from src.models.pricing import Channel, PricingLineItem, PricingSubmission


class PricingRepository:
    """Stub repository. Swap this out for real SQL (e.g. SQLAlchemy) once
    you point it at your actual tables (subs, brands, groups, divisions,
    start/end dates).
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # TODO: create real DB engine/session here, e.g.:
        # self.engine = create_engine(connection_string)

    def get_uploaded_line_items(
        self, fiscal_week: str, division: str | None = None
    ) -> list[PricingLineItem]:
        """Return all uploaded pricing rows for a fiscal week, optionally
        filtered by division. Replace with a real query.
        """
        # TODO: replace with real query, e.g.
        # SELECT * FROM pricing_uploads WHERE fiscal_week = :fiscal_week
        raise NotImplementedError(
            "Wire this up to your real pricing DB (see TODO in db/repository.py)"
        )

    def group_into_submissions(
        self, fiscal_week: str, quarter: str, line_items: list[PricingLineItem]
    ) -> list[PricingSubmission]:
        """Group raw line items into one PricingSubmission per
        division/sub-division/sub-number/channel, mirroring how the
        verification team currently groups rows before reviewing them.
        """
        groups: dict[tuple, list[PricingLineItem]] = {}
        for item in line_items:
            key = (item.division, item.sub_division, item.sub_number, item.channel)
            groups.setdefault(key, []).append(item)

        submissions = []
        for (division, sub_division, sub_number, channel), items in groups.items():
            submissions.append(
                PricingSubmission(
                    submission_id=f"{fiscal_week}-{sub_number}-{channel.value}",
                    fiscal_week=fiscal_week,
                    quarter=quarter,
                    division=division,
                    sub_division=sub_division,
                    sub_number=sub_number,
                    channel=channel,
                    line_items=items,
                )
            )
        return submissions
