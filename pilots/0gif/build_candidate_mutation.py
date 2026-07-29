"""Create one controlled missing-premise mutation for the 0gif DAG."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPT_DIR = ROOT / "skills" / "proof-dag-lean" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from dag_core import evaluate_graph
from check_artifact import check_mutation


def main() -> None:
    reference = json.loads((HERE / "reference_dag.json").read_text(encoding="utf-8"))
    candidate = copy.deepcopy(reference)
    candidate["graph_kind"] = "candidate"
    candidate["graph_id"] = "0gif-candidate-missing-bound-v0.1"

    inference = next(item for item in candidate["inferences"] if item["id"] == "I9")
    before_count = len(inference["input_bindings"])
    inference["input_bindings"] = [
        binding
        for binding in inference["input_bindings"]
        if not (
            binding["fact_id"] == "F13"
            and binding["premise_role"] == "bounded_even_sum"
        )
    ]
    if len(inference["input_bindings"]) != before_count - 1:
        raise ValueError("expected exactly one F13 -> I9 binding to be removed")

    candidate["mutation"] = {
        "base_graph_id": reference["graph_id"],
        "operation": "remove_required_premise",
        "primary_site": {"type": "edge", "id": "F13->I9"},
        "injection_anchor": {"type": "inference", "id": "I9"},
        "declared_expected_first_break": {"type": "inference", "id": "I9"},
        "before": {
            "input_fact_id": "F13",
            "consumer_inference_id": "I9",
            "premise_role": "bounded_even_sum",
            "mathematical_content": (
                "For every N>=1, the even-indexed drop sum is bounded above by x_0."
            ),
        },
        "after": {
            "edge_removed": True,
            "remaining_claim": (
                "Nonnegative and nondecreasing drops are asserted to vanish "
                "without any boundedness premise."
            ),
        },
        "graph_changed": True,
        "target_effect": "target_breaking",
        "seed": 0,
        "provenance": {
            "generator": "pilots/0gif/build_candidate_mutation.py",
            "intent": "single realistic missing-dependency error",
            "source_reference_graph": reference["graph_id"],
        },
    }
    candidate["provenance"] = {
        "source": f"controlled mutation of {reference['graph_id']}",
        "current_annotation_level": "synthetic",
        "requested_target_level": "silver_verified",
        "achieved_annotation_level": "pending",
        "promotion_profile": "algebra-candidate-mutation-v0.1",
        "reference_dag_semantics": {
            "method": "human",
            "status": "passed",
            "evidence": "dag_semantic_review.md",
        },
        "mutation_realism": {
            "method": "human",
            "status": "passed",
            "reviewer": "Ruan Haochen (Eddie)",
            "review_date": "2026-07-28",
            "evidence": "mutation_review.md",
        },
    }

    evaluation = evaluate_graph(candidate)
    (HERE / "candidate_graph.json").write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (HERE / "candidate_evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (HERE / "mutation_check.json").write_text(
        json.dumps(check_mutation(candidate), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
