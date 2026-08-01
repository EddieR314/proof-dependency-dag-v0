from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)


def valid_prediction(problem_id: str) -> dict:
    return {"problem_id": problem_id, "screening_version": "dag-suitability-v0.1", "algebra_module": "polynomials", "input_quality": {"statement_readable": True, "proof_present": True, "proof_integrity": "clean"}, "scores": {"source_integrity": 2, "proof_completeness": 2, "atomic_decomposability": 2, "dependency_explicitness": 2, "scope_traceability": 2, "external_context_burden": 2, "structural_richness": 1}, "estimated_inference_count": 6, "structure_flags": {"has_case_scope": False, "has_multi_premise_inference": True, "has_alternative_path": False}, "decision": "suitable", "reason_codes": ["complete_proof", "clear_inference_units", "clean_linear_proof"], "repair_actions": ["none"], "confidence": "high", "human_review_status": "not_reviewed", "notes": "test"}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "source.jsonl"
        prepared = tmp_path / "prepared.jsonl"
        predictions = tmp_path / "predictions.jsonl"
        audit = tmp_path / "audit.csv"
        source.write_text(json.dumps({"problem_id": "p1", "proof_domain_bucket": "algebra", "domain": "Algebra > Polynomials", "statement": "Prove x=x.", "solution": "Let x be arbitrary. By reflexivity, x=x." * 8, "has_solution": True}) + "\n", encoding="utf-8")
        result = run("scripts/prepare_screening_batch.py", "--input", str(source), "--output", str(prepared))
        assert result.returncode == 0, result.stderr
        predictions.write_text(json.dumps(valid_prediction("p1")) + "\n", encoding="utf-8")
        result = run("scripts/validate_screening_results.py", "--input", str(predictions), "--expected", str(prepared))
        assert result.returncode == 0, result.stdout + result.stderr
        result = run("scripts/make_stratified_audit.py", "--records", str(prepared), "--predictions", str(predictions), "--output", str(audit), "--per-stratum", "1")
        assert result.returncode == 0 and audit.exists(), result.stdout + result.stderr
        bad = valid_prediction("p1")
        bad["human_review_status"] = "confirmed"
        predictions.write_text(json.dumps(bad) + "\n", encoding="utf-8")
        result = run("scripts/validate_screening_results.py", "--input", str(predictions))
        assert result.returncode != 0 and "model_claims_human_review" in result.stdout
        bad = valid_prediction("p1")
        bad["decision"] = "borderline"
        bad["input_quality"]["proof_integrity"] = "suspect"
        bad["repair_actions"] = ["normalize_notation"]
        predictions.write_text(json.dumps(bad) + "\n", encoding="utf-8")
        result = run("scripts/validate_screening_results.py", "--input", str(predictions))
        assert result.returncode != 0 and "non_suitable_without_risk_reason" in result.stdout
    print("dag suitability screening tests passed")


if __name__ == "__main__":
    main()
