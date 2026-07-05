#!/usr/bin/env python3
"""Promote reviewed audit tasks into silver, rejected, and revision queues."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_utils import (
    generated_first_break,
    read_audit_tasks,
    read_jsonl,
    review_value,
    write_jsonl,
)


def status_for_review(task: dict[str, Any]) -> str | None:
    usable = review_value(task, "usable_as_gold")
    single_error = review_value(task, "single_error_valid")
    if usable == "no" or single_error == "no":
        return "rejected"
    if usable == "revise":
        return "needs_revision"
    if (
        review_value(task, "first_break_valid") == "yes"
        and review_value(task, "break_type_valid") == "yes"
        and single_error == "yes"
        and usable == "yes"
    ):
        return "silver_verified"
    return None


def apply_review(
    original: dict[str, Any],
    task: dict[str, Any],
    label_status: str,
    reviewer_id: str,
    reviewed_at: str,
) -> dict[str, Any]:
    promoted = copy.deepcopy(original)
    review = task.get("human_review", {})
    promoted["label_status"] = label_status
    promoted["review_status"] = "reviewed"
    promoted["reviewer_id"] = reviewer_id or task.get("reviewer_id", "")
    promoted["reviewed_at"] = reviewed_at or task.get("reviewed_at", "")
    promoted["human_review"] = review

    if "generated_first_break" not in promoted:
        promoted["generated_first_break"] = task.get("generated_first_break") or generated_first_break(original)

    corrected_spu = review_value(task, "correct_first_break_spu_id")
    corrected_type = review_value(task, "correct_break_type")
    if corrected_spu or corrected_type:
        promoted["human_corrected_first_break"] = {
            "spu_id": corrected_spu,
            "break_type": corrected_type,
        }
    return promoted


def promote(
    originals: list[dict[str, Any]],
    reviewed_tasks: list[dict[str, Any]],
    reviewer_id: str,
    reviewed_at: str,
) -> dict[str, list[dict[str, Any]]]:
    originals_by_id = {
        str(record.get("sample_id")): record
        for record in originals
        if record.get("sample_id") is not None
    }
    outputs = {
        "silver_verified": [],
        "rejected": [],
        "needs_revision": [],
    }

    for task in reviewed_tasks:
        status = status_for_review(task)
        if status is None:
            continue
        sample_id = str(task.get("sample_id"))
        original = originals_by_id.get(sample_id)
        if original is None:
            original = task
        promoted = apply_review(original, task, status, reviewer_id, reviewed_at)
        outputs[status].append(promoted)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", required=True)
    parser.add_argument("--reviewed", required=True)
    parser.add_argument("--out-silver", default="wrong_solutions_silver.jsonl")
    parser.add_argument("--out-rejected", default="wrong_solutions_rejected.jsonl")
    parser.add_argument("--out-needs-revision", default="wrong_solutions_needs_revision.jsonl")
    parser.add_argument("--reviewer-id", default="")
    parser.add_argument(
        "--reviewed-at",
        default=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    args = parser.parse_args()

    outputs = promote(
        read_jsonl(args.synthetic),
        read_audit_tasks(args.reviewed),
        args.reviewer_id,
        args.reviewed_at,
    )
    write_jsonl(outputs["silver_verified"], args.out_silver)
    write_jsonl(outputs["rejected"], args.out_rejected)
    write_jsonl(outputs["needs_revision"], args.out_needs_revision)

    print(
        json.dumps(
            {
                "silver_verified": len(outputs["silver_verified"]),
                "rejected": len(outputs["rejected"]),
                "needs_revision": len(outputs["needs_revision"]),
                "out_silver": args.out_silver,
                "out_rejected": args.out_rejected,
                "out_needs_revision": args.out_needs_revision,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
