from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


SCORES = {"source_integrity", "proof_completeness", "atomic_decomposability", "dependency_explicitness", "scope_traceability", "external_context_burden", "structural_richness"}
DECISIONS = {"suitable", "borderline", "unsuitable"}
CONFIDENCE = {"low", "medium", "high"}
REASONS = {"complete_proof", "clear_inference_units", "traceable_dependencies", "scope_clear", "case_structure", "multi_premise_merge", "alternative_paths", "clean_linear_proof", "missing_solution", "answer_only", "proof_corrupted", "proof_truncated", "source_mojibake", "excessive_repetition", "image_required", "unresolved_reference", "opaque_large_jump", "pure_computation", "scope_ambiguous", "too_short_for_dag", "too_long_unstructured", "non_proof_content"}
REPAIRS = {"none", "recover_source", "recover_image", "remove_repetition", "resolve_reference", "expand_omitted_step", "clarify_scope", "normalize_notation", "human_math_review"}
HARD_REASONS = {"missing_solution", "answer_only", "proof_corrupted", "proof_truncated", "image_required", "non_proof_content"}
RISK_REASONS = {"missing_solution", "answer_only", "proof_corrupted", "proof_truncated", "source_mojibake", "excessive_repetition", "image_required", "unresolved_reference", "opaque_large_jump", "pure_computation", "scope_ambiguous", "too_short_for_dag", "too_long_unstructured", "non_proof_content"}
MODULES = {"functional_equations", "inequalities", "polynomials", "recurrences_sequences", "complex_algebra", "discrete_algebra", "unclassified_algebra"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate(row: dict, model_output: bool) -> list[str]:
    errors: list[str] = []
    if not row.get("problem_id"):
        errors.append("missing_problem_id")
    if row.get("screening_version") != "dag-suitability-v0.1":
        errors.append("invalid_version")
    if row.get("algebra_module") not in MODULES:
        errors.append("invalid_algebra_module")
    scores = row.get("scores", {})
    if set(scores) != SCORES or any(not isinstance(v, int) or v not in {0, 1, 2} for v in scores.values()):
        errors.append("invalid_scores")
    if row.get("decision") not in DECISIONS:
        errors.append("invalid_decision")
    if row.get("confidence") not in CONFIDENCE:
        errors.append("invalid_confidence")
    reasons = row.get("reason_codes", [])
    repairs = row.get("repair_actions", [])
    if not reasons or len(reasons) != len(set(reasons)) or any(x not in REASONS for x in reasons):
        errors.append("invalid_reason_codes")
    if not repairs or len(repairs) != len(set(repairs)) or any(x not in REPAIRS for x in repairs):
        errors.append("invalid_repair_actions")
    if "none" in repairs and len(repairs) > 1:
        errors.append("none_mixed_with_repairs")
    if row.get("decision") == "suitable" and HARD_REASONS.intersection(reasons):
        errors.append("suitable_with_hard_failure")
    if row.get("decision") in {"borderline", "unsuitable"} and not RISK_REASONS.intersection(reasons):
        errors.append("non_suitable_without_risk_reason")
    quality = row.get("input_quality", {})
    if set(quality) != {"statement_readable", "proof_present", "proof_integrity"}:
        errors.append("invalid_input_quality_fields")
    elif (
        not isinstance(quality["statement_readable"], bool)
        or not isinstance(quality["proof_present"], bool)
        or quality["proof_integrity"] not in {"clean", "suspect", "corrupt"}
    ):
        errors.append("invalid_input_quality_values")
    if row.get("decision") == "suitable" and (not quality.get("statement_readable") or not quality.get("proof_present") or quality.get("proof_integrity") != "clean"):
        errors.append("suitable_failed_input_gate")
    if not isinstance(row.get("estimated_inference_count"), int) or row.get("estimated_inference_count", -1) < 0:
        errors.append("invalid_inference_count")
    flags = row.get("structure_flags", {})
    if set(flags) != {"has_case_scope", "has_multi_premise_inference", "has_alternative_path"} or any(not isinstance(v, bool) for v in flags.values()):
        errors.append("invalid_structure_flags")
    if model_output and row.get("human_review_status") != "not_reviewed":
        errors.append("model_claims_human_review")
    if not isinstance(row.get("notes"), str):
        errors.append("invalid_notes")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected")
    parser.add_argument("--allow-human-status", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    duplicate_ids = sorted(k for k, v in Counter(r.get("problem_id") for r in rows).items() if k and v > 1)
    row_errors = {r.get("problem_id", "<missing>"): e for r in rows if (e := validate(r, not args.allow_human_status))}
    expected_errors: list[str] = []
    if args.expected:
        expected_ids = {r["problem_id"] for r in read_jsonl(Path(args.expected))}
        actual_ids = {r.get("problem_id") for r in rows}
        expected_errors = sorted(expected_ids.symmetric_difference(actual_ids))
    summary = {"num_rows": len(rows), "valid": not duplicate_ids and not row_errors and not expected_errors, "decision_counts": dict(Counter(r.get("decision") for r in rows)), "duplicate_ids": duplicate_ids, "id_set_difference": expected_errors, "row_errors": row_errors}
    payload = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if summary["valid"] else 1)


if __name__ == "__main__":
    main()
