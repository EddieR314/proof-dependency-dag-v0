#!/usr/bin/env python3
"""Create stratified human-audit tasks from synthetic wrong-solution samples."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from audit_utils import (
    HUMAN_REVIEW_FIELDS,
    field_value,
    first_break_spu,
    is_warning_sample,
    make_audit_task,
    proof_length,
    read_jsonl,
    write_jsonl,
)


DEFAULT_STRATA_FIELDS = [
    "topic",
    "error_type",
    "break_type",
    "generator_name",
    "difficulty",
    "structural_error_type",
    "warning_flag",
]


def parse_strata(values: list[str]) -> list[tuple[str, int]]:
    strata: list[tuple[str, int]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"Bad --stratify value {value!r}; expected FIELD=K")
        field, raw_k = value.split("=", 1)
        field = field.strip()
        if not field:
            raise ValueError(f"Bad --stratify value {value!r}; empty field")
        strata.append((field, int(raw_k)))
    return strata


def add_by_stratum(
    selected: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
    field: str,
    k: int,
    rng: random.Random,
) -> None:
    if k <= 0:
        return
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = field_value(record, field)
        if key:
            groups[key].append(record)

    for key in sorted(groups):
        candidates = groups[key][:]
        rng.shuffle(candidates)
        selected_problem_ids = {
            str(record.get("problem_id", ""))
            for record in selected.values()
            if record.get("problem_id") is not None
        }
        fresh_problem = [
            record
            for record in candidates
            if str(record.get("problem_id", "")) not in selected_problem_ids
        ]
        ordered = fresh_problem + [
            record
            for record in candidates
            if str(record.get("problem_id", "")) in selected_problem_ids
        ]
        already_in_group = sum(
            1
            for record in selected.values()
            if field_value(record, field) == key
        )
        needed = max(0, k - already_in_group)
        for record in ordered:
            if needed <= 0:
                break
            sample_id = str(record.get("sample_id"))
            if sample_id in selected:
                continue
            selected[sample_id] = record
            needed -= 1


def add_focus_records(
    selected: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
    predicate,
    k: int,
    rng: random.Random,
) -> None:
    if k <= 0:
        return
    candidates = [record for record in records if predicate(record)]
    rng.shuffle(candidates)
    selected_problem_ids = {
        str(record.get("problem_id", ""))
        for record in selected.values()
        if record.get("problem_id") is not None
    }
    candidates.sort(
        key=lambda record: str(record.get("problem_id", "")) in selected_problem_ids
    )
    added = 0
    for record in candidates:
        if added >= k:
            break
        sample_id = str(record.get("sample_id"))
        if sample_id in selected:
            continue
        selected[sample_id] = record
        added += 1


def sample_records(
    records: list[dict[str, Any]],
    strata: list[tuple[str, int]],
    include_warnings: bool,
    seed: int,
    max_samples: int | None = None,
    focus_error_types: list[str] | None = None,
    focus_topics: list[str] | None = None,
    first_break_spu_types: list[str] | None = None,
    include_long_proofs: bool = False,
    focus_quality_warnings: bool = False,
    long_proof_min_spus: int = 30,
    per_focus: int = 0,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    selected: dict[str, dict[str, Any]] = {}

    if include_warnings:
        warning_records = [record for record in records if is_warning_sample(record)]
        rng.shuffle(warning_records)
        for record in warning_records:
            selected[str(record.get("sample_id"))] = record

    focus_error_types = focus_error_types or []
    focus_topics = focus_topics or []
    first_break_spu_types = first_break_spu_types or []
    for error_type in focus_error_types:
        add_focus_records(
            selected,
            records,
            lambda record, error_type=error_type: field_value(record, "error_type") == error_type,
            per_focus,
            rng,
        )
    for topic in focus_topics:
        add_focus_records(
            selected,
            records,
            lambda record, topic=topic: field_value(record, "topic") == topic,
            per_focus,
            rng,
        )
    for spu_type in first_break_spu_types:
        add_focus_records(
            selected,
            records,
            lambda record, spu_type=spu_type: first_break_spu(record).get("type") == spu_type,
            per_focus,
            rng,
        )
    if include_long_proofs:
        add_focus_records(
            selected,
            records,
            lambda record: proof_length(record) >= long_proof_min_spus,
            per_focus,
            rng,
        )
    if focus_quality_warnings:
        add_focus_records(
            selected,
            records,
            lambda record: bool(record_quality_warnings(record)),
            per_focus,
            rng,
        )

    for field, k in strata:
        add_by_stratum(selected, records, field, k, rng)

    sampled = list(selected.values())
    rng.shuffle(sampled)
    if max_samples is not None:
        warning_ids = {
            str(record.get("sample_id"))
            for record in sampled
            if include_warnings and is_warning_sample(record)
        }
        warnings = [record for record in sampled if str(record.get("sample_id")) in warning_ids]
        non_warnings = [record for record in sampled if str(record.get("sample_id")) not in warning_ids]
        sampled = (warnings + non_warnings)[:max_samples]
    return sampled


def write_csv(tasks: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "problem_id",
        "topic",
        "error_type",
        "break_type",
        "generator_name",
        "difficulty",
        "structural_error_type",
        "first_break_spu_type",
        "proof_spu_count",
        "problem",
        "correct_solution",
        "wrong_solution",
        "wrong_solution_steps_json",
        "generated_first_break_json",
        "injected_error_json",
        "evaluator_result_json",
        *HUMAN_REVIEW_FIELDS,
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            review = task.get("human_review", {})
            row = {
                "sample_id": task.get("sample_id", ""),
                "problem_id": task.get("problem_id", ""),
                "topic": task.get("topic", ""),
                "error_type": task.get("error_type", ""),
                "break_type": task.get("break_type", ""),
                "generator_name": task.get("generator_name", ""),
                "difficulty": task.get("difficulty", ""),
                "structural_error_type": task.get("structural_error_type", ""),
                "first_break_spu_type": task.get("first_break_spu_type", ""),
                "proof_spu_count": task.get("proof_spu_count", ""),
                "problem": task.get("problem", ""),
                "correct_solution": task.get("correct_solution", ""),
                "wrong_solution": task.get("wrong_solution", ""),
                "wrong_solution_steps_json": json.dumps(
                    task.get("wrong_solution_steps", []), ensure_ascii=False
                ),
                "generated_first_break_json": json.dumps(
                    task.get("generated_first_break", {}), ensure_ascii=False
                ),
                "injected_error_json": json.dumps(task.get("injected_error", {}), ensure_ascii=False),
                "evaluator_result_json": json.dumps(
                    task.get("evaluator_result", {}), ensure_ascii=False
                ),
            }
            for field in HUMAN_REVIEW_FIELDS:
                row[field] = review.get(field, "")
            writer.writerow(row)


def write_cards(tasks: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Audit Cards", ""]
    for index, task in enumerate(tasks, 1):
        fb = task.get("generated_first_break", {})
        lines.extend(
            [
                f"## {index}. {task.get('sample_id', '')}",
                "",
                f"- topic: {task.get('topic', '')}",
                f"- error_type: {task.get('error_type', '')}",
                f"- difficulty: {task.get('difficulty', '')}",
                "",
                "### Problem",
                "",
                str(task.get("problem", "")),
                "",
                "### Wrong Solution Steps",
                "",
            ]
        )
        for step in task.get("wrong_solution_steps", []):
            sid = step.get("spu_id", "")
            if sid == fb.get("spu_id"):
                lines.append(
                    f">>> GENERATED FIRST BREAK: {sid} | {fb.get('break_type', '')}"
                )
            lines.append(
                f"- {sid} [{step.get('type', '')}; depends_on={step.get('depends_on', [])}]: "
                f"{step.get('text', '')}"
            )
        lines.extend(
            [
                "",
                "### Generated Explanation",
                "",
                str(fb.get("why_wrong", "")),
                "",
                "### Human Review",
                "",
            ]
        )
        for field in HUMAN_REVIEW_FIELDS:
            lines.append(f"- {field}: ")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_quality_warnings(record: dict[str, Any]) -> list[dict[str, Any]]:
    from audit_utils import evaluator_result

    return evaluator_result(record).get("quality_warnings", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-jsonl", default="audit_tasks.jsonl")
    parser.add_argument("--out-csv", default="audit_tasks.csv")
    parser.add_argument("--out-md", default="audit_cards.md")
    parser.add_argument("--per-topic", type=int, default=0)
    parser.add_argument("--per-error-type", type=int, default=0)
    parser.add_argument("--per-break-type", type=int, default=0)
    parser.add_argument("--per-generator", type=int, default=0)
    parser.add_argument("--per-difficulty", type=int, default=0)
    parser.add_argument("--per-structural-error-type", type=int, default=0)
    parser.add_argument("--per-warning-flag", type=int, default=0)
    parser.add_argument("--focus-error-type", action="append", default=[])
    parser.add_argument("--focus-topic", action="append", default=[])
    parser.add_argument(
        "--focus-first-break-spu-type",
        action="append",
        default=[],
        help="Prioritize samples whose generated first_break lands on this SPU type.",
    )
    parser.add_argument("--include-long-proofs", action="store_true")
    parser.add_argument(
        "--focus-quality-warnings",
        action="store_true",
        help="Add focused samples with SPU text quality warnings.",
    )
    parser.add_argument("--long-proof-min-spus", type=int, default=30)
    parser.add_argument(
        "--per-focus",
        type=int,
        default=0,
        help="Number of extra samples to add for each focus group.",
    )
    parser.add_argument(
        "--stratify",
        action="append",
        default=[],
        help="Additional generic stratum as FIELD=K, for example generator_name=2.",
    )
    parser.add_argument("--include-warnings", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-samples", type=int)
    args = parser.parse_args()

    records = read_jsonl(args.input)
    strata = [
        ("topic", args.per_topic),
        ("error_type", args.per_error_type),
        ("break_type", args.per_break_type),
        ("generator_name", args.per_generator),
        ("difficulty", args.per_difficulty),
        ("structural_error_type", args.per_structural_error_type),
        ("warning_flag", args.per_warning_flag),
    ]
    strata.extend(parse_strata(args.stratify))

    sampled = sample_records(
        records,
        strata,
        args.include_warnings,
        args.seed,
        args.max_samples,
        focus_error_types=args.focus_error_type,
        focus_topics=args.focus_topic,
        first_break_spu_types=args.focus_first_break_spu_type,
        include_long_proofs=args.include_long_proofs,
        focus_quality_warnings=args.focus_quality_warnings,
        long_proof_min_spus=args.long_proof_min_spus,
        per_focus=args.per_focus,
    )
    tasks = [make_audit_task(record, i) for i, record in enumerate(sampled, 1)]

    write_jsonl(tasks, args.out_jsonl)
    write_csv(tasks, Path(args.out_csv))
    write_cards(tasks, Path(args.out_md))

    print(
        json.dumps(
            {
                "input_samples": len(records),
                "audit_samples": len(tasks),
                "out_jsonl": args.out_jsonl,
                "out_csv": args.out_csv,
                "out_md": args.out_md,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
