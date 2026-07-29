"""Create one missing-extreme-degree-premise mutation for 00q2."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPT_DIR = ROOT / "skills" / "proof-dag-lean" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from check_artifact import check_mutation
from dag_core import evaluate_graph


def main() -> None:
    reference = json.loads((HERE / "reference_dag.json").read_text(encoding="utf-8"))
    candidate = copy.deepcopy(reference)
    candidate["graph_kind"] = "candidate"
    candidate["graph_id"] = "00q2-candidate-missing-extreme-degree-v0.1"

    target = next(item for item in candidate["inferences"] if item["id"] == "I5")
    before = list(target["input_bindings"])
    target["input_bindings"] = [
        binding
        for binding in target["input_bindings"]
        if not (
            binding["fact_id"] == "F6"
            and binding["premise_role"] == "decomposition"
        )
    ]
    if len(target["input_bindings"]) != len(before) - 1:
        raise ValueError("expected exactly one F6 -> I5 edge to be removed")

    candidate["mutation"] = {
        "base_graph_id": reference["graph_id"],
        "operation": "remove_required_premise",
        "primary_site": {"type": "edge", "id": "F6->I5"},
        "injection_anchor": {"type": "inference", "id": "I5"},
        "declared_expected_first_break": {"type": "inference", "id": "I5"},
        "before": {
            "input_fact_id": "F6",
            "consumer_inference_id": "I5",
            "premise_role": "decomposition",
            "mathematical_content": (
                "For n>1, f_n has distinct nonzero lowest and highest "
                "homogeneous components of degrees 2 and 2n."
            ),
        },
        "after": {
            "edge_removed": True,
            "remaining_claim": (
                "The proof declares F_2 h_l to be the unique nonzero lowest "
                "product component without establishing the extreme-degree "
                "decomposition of f_n."
            ),
        },
        "graph_changed": True,
        "target_effect": "target_breaking",
        "seed": 0,
        "provenance": {
            "generator": "pilots/00q2/build_candidate_mutation.py",
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
            "status": "not_run",
            "evidence": "dag_semantic_review.md",
        },
        "mutation_realism": {
            "method": "human",
            "status": "not_run",
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
