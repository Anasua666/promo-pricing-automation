"""Move submission JSON packages between pending/approved/rejected folders,
mirroring the current physical-folder-path workflow.
"""
from __future__ import annotations

import json
import os
import shutil

from src.config import settings
from src.models.pricing import PricingSubmission


def _week_dir(stage: str, fiscal_week: str, channel: str) -> str:
    path = os.path.join(settings.submissions_root, stage, fiscal_week, channel)
    os.makedirs(path, exist_ok=True)
    return path


def write_pending_submission(submission: PricingSubmission) -> str:
    """Write a verified submission to the pending/ folder, split by channel
    (STORE vs DIRECT approval screens)."""
    directory = _week_dir("pending", submission.fiscal_week, submission.channel.value)
    file_path = os.path.join(directory, f"{submission.submission_id}.json")
    with open(file_path, "w") as f:
        f.write(submission.model_dump_json(indent=2, default=str))
    return file_path


def move_to_approved(submission: PricingSubmission, current_path: str) -> str:
    dest_dir = _week_dir("approved", submission.fiscal_week, submission.channel.value)
    dest_path = os.path.join(dest_dir, os.path.basename(current_path))
    shutil.move(current_path, dest_path)
    return dest_path


def move_to_rejected(submission: PricingSubmission, current_path: str) -> str:
    dest_dir = _week_dir("rejected", submission.fiscal_week, submission.channel.value)
    dest_path = os.path.join(dest_dir, os.path.basename(current_path))
    shutil.move(current_path, dest_path)
    return dest_path


def list_pending_submissions(fiscal_week: str, channel: str) -> list[str]:
    directory = _week_dir("pending", fiscal_week, channel)
    return [
        os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".json")
    ]


def load_submission(file_path: str) -> PricingSubmission:
    with open(file_path) as f:
        data = json.load(f)
    return PricingSubmission(**data)
