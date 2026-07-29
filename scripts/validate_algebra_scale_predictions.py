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


def validate_prediction(
    row: dict, expected_id: str, expected_pilot_id: str
) -> list[str]:
    errors: list[str] = []
    if row.get("problem_id") != expected_id:
        errors.append("problem_id_mismatch")
    if row.get("pilot_id") != expected_pilot_id:
        errors.append("pilot_id_mismatch")
    if row.get("prediction_status") != "completed":
        errors.append("prediction_not_completed")
    if not json.dumps(row, ensure_ascii=False).isascii():
        errors.append("non_ascii_prediction")

    routing = row.get("routing", {})
    if routing.get("primary_module") not in MODULES:
        errors.append("invalid_primary_module")
    secondary = routing.get("secondary_modules", [])
    if any(module not in MODULES for module in secondary):
        errors.append("invalid_secondary_module")
    if len(secondary) != len(set(secondary)):
        errors.append("duplicate_secondary_module")
    if routing.get("confidence") not in CONFIDENCE:
        errors.append("invalid_confidence")

    proof_result = row.get("proof_result")
    if proof_result not in PROOF_RESULTS:
        errors.append("invalid_proof_result")
    if not isinstance(row.get("risk_flags"), list):
        errors.append("risk_flags_not_list")
    if not isinstance(row.get("spu_outline"), list):
        errors.append("spu_outline_not_list")
    if proof_result == "passed" and not row.get("proof", "").strip():
        errors.append("passed_without_proof")
    unresolved_gap = row.get("unresolved_gap", "").strip()
    if proof_result == "passed" and unresolved_gap:
        errors.append("passed_with_gap")
    if proof_result in {"blocked", "failed"} and not unresolved_gap:
        errors.append("blocked_without_gap")

    readiness = row.get("dag_lean_handoff_readiness")
    if readiness not in READINESS:
        errors.append("invalid_handoff_readiness")
    components = row.get("component_status", {})
    proof_review = components.get("proof_review")
    if proof_review not in PROOF_STATUS:
        errors.append("invalid_proof_review_status")
    if components.get("dag") not in DAG_STATUS:
        errors.append("invalid_dag_status")
    if components.get("formal_mapping") not in FORMAL_STATUS:
        errors.append("invalid_formal_status")
    if components.get("lean_build") not in LEAN_STATUS:
        errors.append("invalid_lean_status")
    if proof_result == "passed":
        if proof_review != "partial":
            errors.append("passed_without_partial_review")
        if readiness != "candidate":
            errors.append("passed_without_candidate_handoff")
    elif proof_result == "blocked":
        if proof_review not in {"partial", "not_run"}:
            errors.append("blocked_with_invalid_review")
        if readiness != "blocked":
            errors.append("blocked_without_blocked_handoff")
    elif proof_result == "failed":
        if proof_review != "failed":
            errors.append("failed_without_failed_review")
        if readiness != "blocked":
            errors.append("failed_without_blocked_handoff")
    if components.get("dag") != "not_run":
        errors.append("model_run_claims_dag_validation")
    if components.get("formal_mapping") != "not_run":
        errors.append("model_run_claims_formal_validation")
    if components.get("lean_build") != "not_run":
        errors.append("model_run_claims_lean_build")
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
    expected_by_id = {row["problem_id"]: row for row in statements}
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
        expected = expected_by_id[problem_id]
        errors = validate_prediction(
            prediction, problem_id, expected["pilot_id"]
        )
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
