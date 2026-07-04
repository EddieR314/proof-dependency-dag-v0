#!/usr/bin/env python3
"""Analyze reviewed human-audit tasks."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from audit_utils import is_reviewed, read_audit_tasks, review_value


def rate(tasks: list[dict[str, Any]], field: str, positive: str = "yes") -> float:
    values = [review_value(task, field) for task in tasks if review_value(task, field)]
    if not values:
        return 0.0
    return sum(1 for value in values if value == positive) / len(values)


def average_score(tasks: list[dict[str, Any]], field: str) -> float:
    values: list[float] = []
    for task in tasks:
        raw = review_value(task, field)
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        values.append(value)
    return sum(values) / len(values) if values else 0.0


def grouped_accuracy(tasks: list[dict[str, Any]], group_field: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        groups[str(task.get(group_field, ""))].append(task)
    return {
        group: {
            "reviewed_samples": len(items),
            "first_break_valid_rate": rate(items, "first_break_valid"),
            "break_type_valid_rate": rate(items, "break_type_valid"),
            "single_error_valid_rate": rate(items, "single_error_valid"),
            "usable_as_gold_rate": rate(items, "usable_as_gold"),
        }
        for group, items in sorted(groups.items())
    }


def failure_modes(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for task in tasks:
        has_failure = False
        for field in ["first_break_valid", "break_type_valid", "single_error_valid"]:
            value = review_value(task, field)
            if value and value != "yes":
                counter[f"{field}:{value}"] += 1
                has_failure = True
        usable = review_value(task, "usable_as_gold")
        if usable and usable != "yes":
            counter[f"usable_as_gold:{usable}"] += 1
            has_failure = True
        note = review_value(task, "reviewer_notes")
        if note and has_failure:
            normalized = " ".join(note.lower().split())[:120]
            counter[f"reviewer_note:{normalized}"] += 1
    return [{"failure_mode": key, "count": count} for key, count in counter.most_common(20)]


def analyze(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    reviewed = [task for task in tasks if is_reviewed(task)]
    corrected_break_types = Counter(
        review_value(task, "correct_break_type")
        for task in reviewed
        if review_value(task, "correct_break_type")
    )

    return {
        "reviewed_samples": len(reviewed),
        "first_break_valid_rate": rate(reviewed, "first_break_valid"),
        "break_type_valid_rate": rate(reviewed, "break_type_valid"),
        "single_error_valid_rate": rate(reviewed, "single_error_valid"),
        "usable_as_gold_rate": rate(reviewed, "usable_as_gold"),
        "average_naturalness_score": average_score(
            reviewed, "solution_naturalness_1_to_5"
        ),
        "average_plausibility_before_break_score": average_score(
            reviewed, "mathematical_plausibility_before_break_1_to_5"
        ),
        "average_post_break_consistency_score": average_score(
            reviewed, "post_break_consistency_1_to_5"
        ),
        "accuracy_by_topic": grouped_accuracy(reviewed, "topic"),
        "accuracy_by_error_type": grouped_accuracy(reviewed, "error_type"),
        "accuracy_by_generator_name": grouped_accuracy(reviewed, "generator_name"),
        "most_common_corrected_break_types": [
            {"break_type": key, "count": count}
            for key, count in corrected_break_types.most_common(20)
        ],
        "most_common_failure_modes": failure_modes(reviewed),
    }


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Audit Summary",
        "",
        f"- reviewed_samples: {summary['reviewed_samples']}",
        f"- first_break_valid_rate: {summary['first_break_valid_rate']:.3f}",
        f"- break_type_valid_rate: {summary['break_type_valid_rate']:.3f}",
        f"- single_error_valid_rate: {summary['single_error_valid_rate']:.3f}",
        f"- usable_as_gold_rate: {summary['usable_as_gold_rate']:.3f}",
        f"- average_naturalness_score: {summary['average_naturalness_score']:.3f}",
        f"- average_plausibility_before_break_score: {summary['average_plausibility_before_break_score']:.3f}",
        f"- average_post_break_consistency_score: {summary['average_post_break_consistency_score']:.3f}",
        "",
    ]
    for section, group_key in [
        ("Accuracy By Topic", "accuracy_by_topic"),
        ("Accuracy By Error Type", "accuracy_by_error_type"),
        ("Accuracy By Generator", "accuracy_by_generator_name"),
    ]:
        lines.extend([f"## {section}", ""])
        groups = summary[group_key]
        if not groups:
            lines.append("_No reviewed samples._")
        else:
            lines.append(
                "| group | n | first_break | break_type | single_error | usable_as_gold |"
            )
            lines.append("|---|---:|---:|---:|---:|---:|")
            for group, metrics in groups.items():
                lines.append(
                    f"| {group} | {metrics['reviewed_samples']} | "
                    f"{metrics['first_break_valid_rate']:.3f} | "
                    f"{metrics['break_type_valid_rate']:.3f} | "
                    f"{metrics['single_error_valid_rate']:.3f} | "
                    f"{metrics['usable_as_gold_rate']:.3f} |"
                )
        lines.append("")

    lines.extend(["## Corrected Break Types", ""])
    for item in summary["most_common_corrected_break_types"] or []:
        lines.append(f"- {item['break_type']}: {item['count']}")
    if not summary["most_common_corrected_break_types"]:
        lines.append("_None._")

    lines.extend(["", "## Failure Modes", ""])
    for item in summary["most_common_failure_modes"] or []:
        lines.append(f"- {item['failure_mode']}: {item['count']}")
    if not summary["most_common_failure_modes"]:
        lines.append("_None._")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-json", default="audit_summary.json")
    parser.add_argument("--out-md", default="audit_summary.md")
    args = parser.parse_args()

    summary = analyze(read_audit_tasks(args.input))
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown(summary, Path(args.out_md))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
