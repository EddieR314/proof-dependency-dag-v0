from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


MODULES = {
    "functional_equations",
    "inequalities",
    "polynomials",
    "recurrences_sequences",
    "complex_algebra",
    "discrete_algebra",
}
CONFIDENCE = {"low", "medium", "high"}
PROOF_RESULTS = {"passed", "blocked", "failed"}
READINESS = {"blocked", "candidate", "reviewed"}
PROOF_STATUS = {"not_run", "passed", "failed", "partial"}
DAG_STATUS = {"not_run", "candidate", "validated"}
FORMAL_STATUS = {"not_run", "candidate", "validated"}
LEAN_STATUS = {"not_run", "passed", "failed"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_prediction(row: dict, expected_id: str) -> list[str]:
    errors: list[str] = []
    if row.get("problem_id") != expected_id:
        errors.append("problem_id_mismatch")
    if row.get("prediction_status") != "completed":
        errors.append("prediction_not_completed")

    routing = row.get("routing", {})
    if routing.get("primary_module") not in MODULES:
        errors.append("invalid_primary_module")
    if any(module not in MODULES for module in routing.get("secondary_modules", [])):
        errors.append("invalid_secondary_module")
    if routing.get("confidence") not in CONFIDENCE:
        errors.append("invalid_confidence")

    if row.get("proof_result") not in PROOF_RESULTS:
        errors.append("invalid_proof_result")
    if not isinstance(row.get("risk_flags"), list):
        errors.append("risk_flags_not_list")
    if not isinstance(row.get("spu_outline"), list):
        errors.append("spu_outline_not_list")
    if row.get("proof_result") == "passed" and not row.get("proof", "").strip():
        errors.append("passed_without_proof")
    if row.get("proof_result") == "blocked" and not row.get(
        "unresolved_gap", ""
    ).strip():
        errors.append("blocked_without_gap")

    if row.get("dag_lean_handoff_readiness") not in READINESS:
        errors.append("invalid_handoff_readiness")
    components = row.get("component_status", {})
    if components.get("proof_review") not in PROOF_STATUS:
        errors.append("invalid_proof_review_status")
    if components.get("dag") not in DAG_STATUS:
        errors.append("invalid_dag_status")
    if components.get("formal_mapping") not in FORMAL_STATUS:
        errors.append("invalid_formal_status")
    if components.get("lean_build") not in LEAN_STATUS:
        errors.append("invalid_lean_status")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--statements", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    statements = read_jsonl(args.statements)
    predictions = read_jsonl(args.predictions)
    expected_ids = [row["problem_id"] for row in statements]
    prediction_by_id = {
        row.get("problem_id"): row
        for row in predictions
        if row.get("problem_id")
    }

    duplicate_ids = [
        problem_id
        for problem_id, count in Counter(
            row.get("problem_id") for row in predictions
        ).items()
        if problem_id and count > 1
    ]
    missing_ids = [
        problem_id
        for problem_id in expected_ids
        if problem_id not in prediction_by_id
    ]
    unexpected_ids = sorted(set(prediction_by_id) - set(expected_ids))

    row_errors: dict[str, list[str]] = {}
    for problem_id in expected_ids:
        prediction = prediction_by_id.get(problem_id)
        if prediction is None:
            continue
        errors = validate_prediction(prediction, problem_id)
        if errors:
            row_errors[problem_id] = errors

    valid_count = len(expected_ids) - len(missing_ids) - len(row_errors)
    summary = {
        "expected_count": len(expected_ids),
        "prediction_count": len(predictions),
        "valid_count": valid_count,
        "complete": (
            not duplicate_ids
            and not missing_ids
            and not unexpected_ids
            and not row_errors
        ),
        "duplicate_ids": duplicate_ids,
        "missing_ids": missing_ids,
        "unexpected_ids": unexpected_ids,
        "row_errors": row_errors,
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if summary["complete"] else 1)


if __name__ == "__main__":
    main()
