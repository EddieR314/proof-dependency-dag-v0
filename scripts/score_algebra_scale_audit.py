from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def cohen_kappa(left: list[str], right: list[str]) -> float | None:
    if len(left) != len(right) or not left:
        return None
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    labels = set(left_counts) | set(right_counts)
    expected = sum(
        (left_counts[label] / len(left)) * (right_counts[label] / len(right))
        for label in labels
    )
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def decided(rows: list[dict], field: str) -> dict[str, str]:
    pending = {"", "pending", "not_opened", "not_checked"}
    return {
        row["problem_id"]: row[field]
        for row in rows
        if row.get(field, "") not in pending
    }


def agreement(left: dict[str, str], right: dict[str, str]) -> dict:
    common = sorted(set(left) & set(right))
    left_values = [left[key] for key in common]
    right_values = [right[key] for key in common]
    return {
        "common_decisions": len(common),
        "raw_agreement": (
            sum(a == b for a, b in zip(left_values, right_values)) / len(common)
            if common
            else None
        ),
        "cohen_kappa": cohen_kappa(left_values, right_values),
        "disagreements": [
            {
                "problem_id": key,
                "reviewer_a": left[key],
                "reviewer_b": right[key],
            }
            for key in common
            if left[key] != right[key]
        ],
    }


def rate(rows: list[dict], field: str, positive: set[str]) -> dict:
    values = [
        row[field]
        for row in rows
        if row.get(field, "") not in {"", "pending", "not_opened", "not_checked"}
    ]
    return {
        "decided": len(values),
        "positive": sum(value in positive for value in values),
        "rate": (
            sum(value in positive for value in values) / len(values)
            if values
            else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--reviewer-a", type=Path, required=True)
    parser.add_argument("--reviewer-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    predictions = {
        row["problem_id"]: row for row in read_jsonl(args.predictions)
    }
    reviewer_a = read_jsonl(args.reviewer_a)
    reviewer_b = read_jsonl(args.reviewer_b)
    ids_a = {row["problem_id"] for row in reviewer_a}
    ids_b = {row["problem_id"] for row in reviewer_b}
    if ids_a != ids_b:
        raise ValueError("Reviewer files do not contain the same problem IDs")

    combined = reviewer_a + reviewer_b
    false_positive_records = []
    for review in combined:
        prediction = predictions.get(review["problem_id"], {})
        if (
            prediction.get("proof_result") == "passed"
            and review.get("proof_decision") == "failed"
        ):
            false_positive_records.append(
                {
                    "problem_id": review["problem_id"],
                    "reviewer_slot": review["reviewer_slot"],
                }
            )

    result = {
        "reviewed_problem_count": len(ids_a),
        "reviewer_a_named": all(row.get("reviewer") for row in reviewer_a),
        "reviewer_b_named": all(row.get("reviewer") for row in reviewer_b),
        "routing": {
            "reviewer_a": rate(reviewer_a, "routing_decision", {"correct"}),
            "reviewer_b": rate(reviewer_b, "routing_decision", {"correct"}),
            "agreement": agreement(
                decided(reviewer_a, "routing_decision"),
                decided(reviewer_b, "routing_decision"),
            ),
        },
        "proof": {
            "reviewer_a": rate(
                reviewer_a, "proof_decision", {"passed", "different_valid"}
            ),
            "reviewer_b": rate(
                reviewer_b, "proof_decision", {"passed", "different_valid"}
            ),
            "agreement": agreement(
                decided(reviewer_a, "proof_decision"),
                decided(reviewer_b, "proof_decision"),
            ),
            "serious_false_positive_reviews": len(false_positive_records),
            "serious_false_positive_records": false_positive_records,
        },
        "spu": {
            "reviewer_a": rate(reviewer_a, "spu_decision", {"passed"}),
            "reviewer_b": rate(reviewer_b, "spu_decision", {"passed"}),
        },
        "risk_flags": {
            "reviewer_a": rate(
                reviewer_a, "risk_flags_decision", {"passed"}
            ),
            "reviewer_b": rate(
                reviewer_b, "risk_flags_decision", {"passed"}
            ),
        },
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
