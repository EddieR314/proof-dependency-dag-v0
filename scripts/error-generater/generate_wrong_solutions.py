#!/usr/bin/env python3
"""Generate wrong olympiad-style solutions as JSONL records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dag_build import build_dependency_dag, edges_from_spus
from error_injector import inject_error, load_error_taxonomy
from geometry_tables import geometry_tables
from quality_filter import validate_generated_sample
from sample_enrichment import (
    build_diff,
    build_first_break_detail,
    classify_difficulty,
    classify_variant,
    expected_feedback_for_error,
)
from spu_decompose import decompose_solution
from target_selector import critical_nodes, reachable_counts
from wrong_solution_writer import write_wrong_solution, write_wrong_solution_steps


DEFAULT_ERROR_TYPES = [
    "missing_dependency",
    "wrong_theorem",
    "wrong_dependency",
    "missing_case",
    "false_claim",
    "sign_error",
    "circular_reasoning",
    "overgeneralization",
    "domain_error",
    "quantifier_error",
    "unproved_existence",
    "case_overlap",
    "invalid_wlog",
    "diagram_assumption",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Bad JSON on line {line_no}: {exc}") from exc
    return records


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def generate_for_problem(
    record: dict[str, Any],
    num_samples: int,
    error_types: list[str],
    taxonomy: list[dict[str, Any]],
    keep_failed: bool = False,
    error_type_offset: int = 0,
) -> list[dict[str, Any]]:
    problem_id = str(record.get("problem_id") or record.get("sample_id") or "unknown")
    problem = record.get("problem", "")
    correct_solution = record.get("correct_solution", "")
    topic = record.get("topic", "")

    correct_spus = build_dependency_dag(
        decompose_solution(correct_solution, problem=problem, prefix="S")
    )
    correct_edges = edges_from_spus(correct_spus)
    reach = reachable_counts(correct_spus)
    crit = critical_nodes(correct_spus)

    samples = []
    attempts = 0
    max_attempts = max(num_samples * len(error_types) * 2, num_samples)

    while len(samples) < num_samples and attempts < max_attempts:
        error_type = error_types[(error_type_offset + attempts) % len(error_types)]
        attempts += 1
        try:
            mutation = inject_error(correct_spus, error_type, taxonomy=taxonomy)
        except ValueError:
            continue

        wrong_spus = mutation["wrong_spus"]
        wrong_solution = write_wrong_solution(problem, wrong_spus)
        wrong_steps = write_wrong_solution_steps(wrong_spus)
        diff = build_diff(correct_spus, wrong_spus)
        first_break_detail = build_first_break_detail(
            wrong_spus, mutation["first_break"], mutation["injected_error"]
        )
        expected_feedback = expected_feedback_for_error(
            first_break_detail, mutation["injected_error"]
        )
        error_type_name = mutation["injected_error"]["error_type"]
        variant = classify_variant(error_type_name)
        difficulty, error_subtlety = classify_difficulty(error_type_name, variant)
        sample_index = len(samples) + 1
        sample = {
            "sample_id": f"{problem_id}__wrong_{sample_index}",
            "problem_id": problem_id,
            "topic": topic,
            "problem": problem,
            "correct_solution": correct_solution,
            "wrong_solution": wrong_solution,
            "wrong_solution_steps": wrong_steps,
            "correct_spus": correct_spus,
            "wrong_spus": wrong_spus,
            "correct_edges": correct_edges,
            "wrong_edges": mutation["wrong_edges"],
            "first_break": mutation["first_break"],
            "first_break_detail": first_break_detail,
            "injected_error": mutation["injected_error"],
            "diff": diff,
            "difficulty": difficulty,
            "error_subtlety": error_subtlety,
            "expected_feedback": expected_feedback,
            "variant": variant,
            "metadata": {
                "generator": "generate_wrong_solutions.py",
                "spu_count": len(correct_spus),
                "correct_edge_count": len(correct_edges),
                "wrong_edge_count": len(mutation["wrong_edges"]),
                "critical_nodes": crit,
                "reachable_counts": reach,
            },
        }
        if topic.lower() == "geometry" or "geometry" in problem_id.lower():
            sample.update(geometry_tables(problem, correct_spus, wrong_spus))

        ok, quality_errors = validate_generated_sample(sample)
        sample["metadata"]["quality_ok"] = ok
        sample["metadata"]["quality_errors"] = quality_errors
        if ok or keep_failed:
            samples.append(sample)

    return samples


def parse_error_types(value: str) -> list[str]:
    if value == "auto":
        return DEFAULT_ERROR_TYPES[:]
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSONL with problem_id, problem, correct_solution.")
    parser.add_argument("--out", required=True, help="Output JSONL path.")
    parser.add_argument("--num-per-problem", type=int, default=1)
    parser.add_argument(
        "--error-types",
        default="auto",
        help="Comma-separated error types, or 'auto'.",
    )
    parser.add_argument(
        "--keep-failed",
        action="store_true",
        help="Save samples even if quality checks fail, with errors in metadata.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)
    taxonomy = load_error_taxonomy()
    error_types = parse_error_types(args.error_types)

    records = read_jsonl(input_path)
    generated = []
    for record_index, record in enumerate(records):
        generated.extend(
            generate_for_problem(
                record,
                num_samples=args.num_per_problem,
                error_types=error_types,
                taxonomy=taxonomy,
                keep_failed=args.keep_failed,
                error_type_offset=record_index * args.num_per_problem,
            )
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(generated, out_path)

    print(
        json.dumps(
            {
                "input_records": len(records),
                "generated_samples": len(generated),
                "output": str(out_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
