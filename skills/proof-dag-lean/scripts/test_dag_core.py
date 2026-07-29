"""Regression tests for proof-dag-schema-v0.4 semantics."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

from dag_core import evaluate_criticality, evaluate_graph, read_graph, validate_graph


def add_scope(graph: dict, scope_id: str, parent_id: str, kind: str = "case") -> None:
    graph["scopes"].append(
        {"id": scope_id, "parent_id": parent_id, "kind": kind}
    )


class DagCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pilot = REPO_ROOT / "pilots" / "functional_inequality_p5"
        cls.correct = read_graph(pilot / "correct_dag.json")
        cls.candidate = read_graph(pilot / "mutated_graph.json")

    def test_reference_graph_derives_goal(self) -> None:
        self.assertEqual(validate_graph(self.correct), [])
        result = evaluate_graph(self.correct)
        self.assertTrue(result["all_targets_derivable"])
        self.assertIsNone(result["computed_first_break"])

    def test_static_nodes_do_not_store_dynamic_state(self) -> None:
        forbidden = {
            "support_status",
            "availability_status",
            "validation_status",
            "invalid_reason_codes",
            "lean_declaration",
        }
        for node in [*self.correct["facts"], *self.correct["inferences"]]:
            self.assertFalse(forbidden.intersection(node))

    def test_source_order_is_total_and_contiguous(self) -> None:
        orders = [
            inference["source_order"] for inference in self.correct["inferences"]
        ]
        self.assertEqual(sorted(orders), list(range(1, len(orders) + 1)))

    def test_candidate_recomputes_first_break_and_propagation(self) -> None:
        self.assertEqual(validate_graph(self.candidate), [])
        result = evaluate_graph(self.candidate)
        self.assertEqual(
            result["computed_first_break"],
            {"type": "inference", "id": "I10"},
        )
        self.assertTrue(result["first_break_match"])
        self.assertFalse(result["all_targets_derivable"])
        evaluations = {
            item["inference_id"]: item
            for item in result["inference_evaluations"]
        }
        self.assertEqual(evaluations["I10"]["intrinsic_status"], "invalid")
        self.assertEqual(evaluations["I11"]["intrinsic_status"], "valid")
        self.assertEqual(evaluations["I11"]["effective_status"], "blocked")

    def test_criticality_excludes_target_itself(self) -> None:
        result = evaluate_criticality(self.correct, "F22")
        self.assertEqual(result["critical_status"], "not_evaluable")
        self.assertEqual(result["reason"], "candidate_is_target")

    def test_equality_inference_is_critical_for_goal(self) -> None:
        result = evaluate_criticality(self.correct, "I10")
        self.assertEqual(result["critical_status"], "critical")
        self.assertFalse(result["blocked_target_status"]["F22"])

    def test_alternative_producer_makes_inference_noncritical(self) -> None:
        graph = copy.deepcopy(self.correct)
        alternative = copy.deepcopy(
            next(item for item in graph["inferences"] if item["id"] == "I10")
        )
        alternative["id"] = "I10_alt"
        alternative["spu_id"] = "SPU10_alt"
        alternative["source_order"] = 11
        for inference in graph["inferences"]:
            if inference["source_order"] >= 11:
                inference["source_order"] += 1
        graph["inferences"].append(alternative)
        self.assertEqual(validate_graph(graph), [])
        result = evaluate_criticality(graph, "I10")
        self.assertEqual(result["critical_status"], "noncritical")

    def test_child_scope_can_read_global_facts(self) -> None:
        graph = copy.deepcopy(self.correct)
        add_scope(graph, "global/case_1", "global")
        inference = graph["inferences"][0]
        inference["scope"] = "global/case_1"
        graph["facts"][4]["scope"] = "global/case_1"
        result = evaluate_graph(graph)
        evaluation = result["inference_evaluations"][0]
        self.assertEqual(evaluation["effective_status"], "executable")

    def test_sibling_scope_reference_is_rejected(self) -> None:
        graph = copy.deepcopy(self.correct)
        add_scope(graph, "global/case_1", "global")
        add_scope(graph, "global/case_2", "global")
        graph["facts"][0]["scope"] = "global/case_1"
        graph["inferences"][0]["scope"] = "global/case_2"
        result = evaluate_graph(graph)
        evaluation = result["inference_evaluations"][0]
        self.assertIn("scope_violation", evaluation["reason_codes"])

    def test_reference_cycle_is_rejected(self) -> None:
        graph = copy.deepcopy(self.correct)
        graph["inferences"][0]["input_bindings"].append(
            {"fact_id": "F22", "premise_role": "future_goal"}
        )
        errors = validate_graph(graph)
        self.assertIn("reference graph contains a directed cycle", errors)

    def test_candidate_cycle_is_representable_and_evaluated(self) -> None:
        graph = copy.deepcopy(self.candidate)
        graph["inferences"][0]["input_bindings"].append(
            {"fact_id": "F22", "premise_role": "future_goal"}
        )
        self.assertNotIn(
            "reference graph contains a directed cycle", validate_graph(graph)
        )
        result = evaluate_graph(graph)
        evaluations = {
            item["inference_id"]: item
            for item in result["inference_evaluations"]
        }
        self.assertIn("cyclic_dependency", evaluations["I1"]["reason_codes"])


if __name__ == "__main__":
    unittest.main()
