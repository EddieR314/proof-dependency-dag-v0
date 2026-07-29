from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from run_algebra_scale_predictions import (
    validate_prediction,
    validate_schema_for_api,
)
from validate_algebra_scale_predictions import (
    validate_prediction as validate_frozen_prediction,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "algebra_scale_pilot_100_v0.1"
CURRICULUM = ROOT / "data" / "algebra_skill_curriculum"


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class ScalePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.statements = read_jsonl(OUTPUT / "statements_only.jsonl")
        cls.calibration = read_jsonl(CURRICULUM / "calibration.jsonl")
        cls.heldout = read_jsonl(CURRICULUM / "heldout.jsonl")

    def test_sample_is_unique_and_reference_free(self) -> None:
        self.assertEqual(len(self.statements), 100)
        self.assertEqual(
            len({row["problem_id"] for row in self.statements}), 100
        )
        self.assertEqual(
            len({row["normalized_hash"] for row in self.statements}), 100
        )
        self.assertTrue(
            all(
                "solution" not in row and "final_answer" not in row
                for row in self.statements
            )
        )

    def test_sample_does_not_overlap_calibration_or_heldout(self) -> None:
        excluded = self.calibration + self.heldout
        excluded_ids = {row["problem_id"] for row in excluded}
        excluded_hashes = {row["normalized_hash"] for row in excluded}
        self.assertFalse(
            {row["problem_id"] for row in self.statements} & excluded_ids
        )
        self.assertFalse(
            {row["normalized_hash"] for row in self.statements}
            & excluded_hashes
        )

    def test_double_review_templates_match(self) -> None:
        reviewer_a = read_jsonl(
            OUTPUT / "human_audit_30_reviewer_a.jsonl"
        )
        reviewer_b = read_jsonl(
            OUTPUT / "human_audit_30_reviewer_b.jsonl"
        )
        self.assertEqual(len(reviewer_a), 30)
        self.assertEqual(len(reviewer_b), 30)
        self.assertEqual(
            {row["problem_id"] for row in reviewer_a},
            {row["problem_id"] for row in reviewer_b},
        )

    def test_prediction_validator_and_audit_scorer_smoke(self) -> None:
        predictions = []
        for statement in self.statements:
            predictions.append(
                {
                    "problem_id": statement["problem_id"],
                    "pilot_id": statement["pilot_id"],
                    "prediction_status": "completed",
                    "routing": {
                        "primary_module": statement["source_bucket"],
                        "secondary_modules": [],
                        "confidence": "low",
                    },
                    "candidate_answer": "",
                    "proof_result": "failed",
                    "proof": "",
                    "unresolved_gap": "Synthetic smoke-test failure.",
                    "risk_flags": [],
                    "spu_outline": [],
                    "dag_lean_handoff_readiness": "blocked",
                    "component_status": {
                        "proof_review": "failed",
                        "dag": "not_run",
                        "formal_mapping": "not_run",
                        "lean_build": "not_run",
                    },
                }
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            prediction_path = temp / "predictions.jsonl"
            prediction_path.write_text(
                "".join(json.dumps(row) + "\n" for row in predictions),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_algebra_scale_predictions.py"),
                    "--statements",
                    str(OUTPUT / "statements_only.jsonl"),
                    "--predictions",
                    str(prediction_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "score_algebra_scale_audit.py"),
                    "--predictions",
                    str(prediction_path),
                    "--reviewer-a",
                    str(OUTPUT / "human_audit_30_reviewer_a.jsonl"),
                    "--reviewer-b",
                    str(OUTPUT / "human_audit_30_reviewer_b.jsonl"),
                    "--output",
                    str(temp / "score.json"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_api_schema_and_prediction_state_machine(self) -> None:
        schema = json.loads(
            (OUTPUT / "prediction.schema.json").read_text(encoding="utf-8")
        )
        validate_schema_for_api(schema)
        statement = self.statements[0]
        prediction = {
            "problem_id": statement["problem_id"],
            "pilot_id": statement["pilot_id"],
            "prediction_status": "completed",
            "routing": {
                "primary_module": "functional_equations",
                "secondary_modules": [],
                "confidence": "low",
            },
            "candidate_answer": "Candidate",
            "proof_result": "passed",
            "proof": "Complete candidate proof.",
            "unresolved_gap": "",
            "risk_flags": [],
            "spu_outline": [],
            "dag_lean_handoff_readiness": "candidate",
            "component_status": {
                "proof_review": "partial",
                "dag": "not_run",
                "formal_mapping": "not_run",
                "lean_build": "not_run",
            },
        }
        validate_prediction(prediction, statement)
        self.assertEqual(
            validate_frozen_prediction(
                prediction,
                statement["problem_id"],
                statement["pilot_id"],
            ),
            [],
        )
        prediction["unresolved_gap"] = "Contradictory gap."
        with self.assertRaisesRegex(ValueError, "nonempty unresolved_gap"):
            validate_prediction(prediction, statement)
        self.assertIn(
            "passed_with_gap",
            validate_frozen_prediction(
                prediction,
                statement["problem_id"],
                statement["pilot_id"],
            ),
        )


if __name__ == "__main__":
    unittest.main()
