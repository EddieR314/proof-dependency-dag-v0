"""Migrate the reviewed 0chi pilot from proof-dag-v0.3 to schema v0.4."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "skills" / "proof-dag-lean" / "scripts"))

from check_artifact import check_mutation
from dag_core import evaluate_graph


def migrate_fact(item: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "id",
        "statement",
        "canonical_form",
        "introduction_kind",
        "roles",
        "scope",
        "objects",
        "source_spans",
    }
    migrated = {key: value for key, value in item.items() if key in allowed}
    if migrated["introduction_kind"] == "definition":
        migrated["introduction_kind"] = "constructed"
    return migrated


def migrate_inference(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "spu_id": item["spu_id"],
        "source_order": item["order"],
        "rule_id": item["rule_id"],
        "scope": item["scope"],
        "input_bindings": item["input_bindings"],
        "variable_bindings": item["variable_bindings"],
        "output_fact_id": item["output_fact_id"],
        "source_spans": item["source_spans"],
        "risk_flags": (
            ["large_lemma_compression", "external_theorem_dependency"]
            if item["id"] in {"I1", "I5", "I6"}
            else []
        ),
    }


def migrate(old: dict[str, Any], *, candidate: bool) -> dict[str, Any]:
    graph_id = "0chi-candidate-wrong-sign-v0.4" if candidate else "0chi-reference-v0.4"
    graph = {
        "schema_version": "proof-dag-schema-v0.4",
        "graph_kind": "candidate" if candidate else "reference",
        "graph_id": graph_id,
        "problem_id": "0chi",
        "target_fact_ids": old["target_fact_ids"],
        "versions": {
            "skill_standard": "0.3",
            "dag_schema": "proof-dag-schema-v0.4",
            "fact_schema": "fact-v0.4",
            "inference_schema": "inference-v0.4",
            "scope_schema": "scope-v0.4",
            "mutation_schema": "mutation-v0.4",
            "canonicalizer": "math-expression-v1",
            "rule_registry": "complex-power-sum-rules-v1",
            "common_tooling": "proof-dag-lean-v0.4",
            "domain_skill": "olympiad-algebra-expert-v0.1",
        },
        "source_record": {
            "problem_source": "HuggingFace:ShadenA/MathNet problem 0chi",
            "solution_source": "human-reviewed proof in pilots/0chi/problem.md",
            "source_record_id": "ShadenA/MathNet:all:train:1296",
            "source_hash": "reviewed-source-0chi",
            "candidate_reference_solution_hash": "reviewed-proof-0chi",
            "reviewed_solution_hash": "reviewed-proof-0chi",
        },
        "scopes": [
            {"id": item["id"], "parent_id": item["parent_id"], "kind": item["kind"]}
            for item in old["scopes"]
        ],
        "rule_schemas": old["rule_schemas"],
        "facts": [migrate_fact(item) for item in old["facts"]],
        "inferences": [migrate_inference(item) for item in old["inferences"]],
        "provenance": {
            "source": "pilots/0chi proof-dag-v0.3 reviewed pilot",
            "current_annotation_level": "silver_verified",
            "requested_target_level": "silver_verified",
            "achieved_annotation_level": "pending",
            "promotion_profile": "algebra-schema-v0.4-migration",
            "proof_review": {
                "method": "human",
                "status": "passed",
                "reviewer": "Ruan Haochen (Eddie)",
            },
            "dag_semantic_review": {
                "method": "human",
                "status": "not_run",
                "evidence": "dag_semantic_review_v04.md",
            },
        },
    }
    if candidate:
        graph["mutation"] = {
            "base_graph_id": "0chi-reference-v0.4",
            "operation": "alter_output_sign",
            "primary_site": {"type": "inference", "id": "I5"},
            "injection_anchor": {"type": "inference", "id": "I5"},
            "declared_expected_first_break": {"type": "inference", "id": "I5"},
            "before": old["mutation"]["before"],
            "after": old["mutation"]["after"],
            "graph_changed": True,
            "target_effect": "target_breaking",
            "seed": 0,
            "provenance": {
                "source_mutation": "pilots/0chi/mutated_dag.json",
                "lean_counterexample": "ProofDag0chi.wrongSign_recurrence_counterexample",
            },
        }
        graph["provenance"]["mutation_realism"] = {
            "method": "human",
            "status": "not_run",
            "evidence": "mutation_review_v04.md",
        }
    return graph


def main() -> None:
    old_reference = json.loads((HERE / "correct_dag.json").read_text(encoding="utf-8"))
    old_candidate = json.loads((HERE / "mutated_dag.json").read_text(encoding="utf-8"))
    reference = migrate(old_reference, candidate=False)
    candidate = migrate(old_candidate, candidate=True)
    outputs = {
        "reference_dag.json": reference,
        "candidate_graph.json": candidate,
        "reference_evaluation_v04.json": evaluate_graph(reference),
        "candidate_evaluation_v04.json": evaluate_graph(candidate),
        "mutation_check_v04.json": check_mutation(candidate),
    }
    for filename, payload in outputs.items():
        (HERE / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
