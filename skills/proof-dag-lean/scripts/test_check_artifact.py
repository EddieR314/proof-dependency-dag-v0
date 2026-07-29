"""Regression tests for v0.4 DAG-to-Lean mapping checks."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

from check_artifact import check_formal_mapping, check_mutation
from dag_core import read_graph


class ArtifactCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = REPO_ROOT / "pilots" / "functional_inequality_p5"
        cls.graph = read_graph(cls.project / "correct_dag.json")
        cls.candidate = read_graph(cls.project / "mutated_graph.json")
        cls.mapping = json.loads(
            (cls.project / "formal_mapping.json").read_text(encoding="utf-8")
        )

    def test_complete_mapping_passes_without_rebuilding(self) -> None:
        result = check_formal_mapping(
            self.graph, self.mapping, self.project, run_build=False
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["inference_coverage"], 1.0)

    def test_missing_inference_mapping_is_rejected(self) -> None:
        mapping = copy.deepcopy(self.mapping)
        mapping["mapping"] = [
            item for item in mapping["mapping"] if item["inference_id"] != "I10"
        ]
        result = check_formal_mapping(
            self.graph, mapping, self.project, run_build=False
        )
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("leaves Inferences unmapped" in error for error in result["errors"])
        )

    def test_wrong_output_mapping_is_rejected(self) -> None:
        mapping = copy.deepcopy(self.mapping)
        target = next(
            item for item in mapping["mapping"] if item["inference_id"] == "I10"
        )
        target["output_fact_id"] = "F13"
        result = check_formal_mapping(
            self.graph, mapping, self.project, run_build=False
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("output mapping" in error for error in result["errors"]))

    def test_candidate_mutation_passes(self) -> None:
        result = check_mutation(self.candidate)
        self.assertTrue(result["passed"])
        self.assertTrue(result["first_break_match"])


if __name__ == "__main__":
    unittest.main()
