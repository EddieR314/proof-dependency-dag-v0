"""Build the proof-dag-schema-v0.4 Reference DAG for problem 0gif."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPT_DIR = ROOT / "skills" / "proof-dag-lean" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from dag_core import evaluate_graph


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rule(
    rule_id: str,
    name: str,
    inputs: list[tuple[str, str]],
    output_predicate: str,
    output_canonical: str,
    category: str,
    variables: list[str],
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "name": name,
        "category": category,
        "input_patterns": [
            {"premise_role": role, "predicate": predicate}
            for role, predicate in inputs
        ],
        "variables": variables,
        "variable_constraints": [],
        "output_pattern": {
            "predicate": output_predicate,
            "canonical_form": output_canonical,
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    }


def fact(
    fact_id: str,
    statement: str,
    canonical_form: str,
    introduction_kind: str,
    objects: list[str],
    source_spans: list[str],
    *,
    goal: bool = False,
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "statement": statement,
        "canonical_form": canonical_form,
        "introduction_kind": introduction_kind,
        "roles": ["goal" if goal else "intermediate"],
        "scope": "global",
        "objects": objects,
        "source_spans": source_spans,
    }


def inference(
    number: int,
    rule_id: str,
    inputs: list[tuple[str, str]],
    output: str,
    variables: dict[str, str],
    risk_flags: list[str],
) -> dict[str, Any]:
    return {
        "id": f"I{number}",
        "spu_id": f"SPU{number}",
        "source_order": number,
        "rule_id": rule_id,
        "scope": "global",
        "input_bindings": [
            {"fact_id": fact_id, "premise_role": role}
            for fact_id, role in inputs
        ],
        "variable_bindings": variables,
        "output_fact_id": output,
        "source_spans": [f"proof:S{number}"],
        "risk_flags": risk_flags,
    }


RULES = [
    rule(
        "positive_forward_orbit",
        "A positive self-map has positive forward iterates",
        [("positive_map", "PositiveMap"), ("orbit_definition", "OrbitDefinition")],
        "PositiveOrbit",
        "PositiveOrbit(f,xseq)",
        "iteration",
        ["f", "xseq", "n"],
    ),
    rule(
        "two_step_descent",
        "Substitute y=f(x) and cancel a positive common factor",
        [("positive_map", "PositiveMap"), ("condition", "OriginalCondition")],
        "TwoStepDescent",
        "TwoStepDescent(f)",
        "functional_inequality",
        ["f", "x"],
    ),
    rule(
        "lift_descent_to_orbit",
        "Apply the two-step descent at every orbit point",
        [
            ("orbit_definition", "OrbitDefinition"),
            ("two_step_descent", "TwoStepDescent"),
        ],
        "OrbitTwoStepDescent",
        "OrbitTwoStepDescent(xseq)",
        "iteration",
        ["f", "xseq", "n"],
    ),
    rule(
        "adjacent_drop_comparison",
        "Apply the original inequality to adjacent orbit terms",
        [
            ("positive_map", "PositiveMap"),
            ("condition", "OriginalCondition"),
            ("orbit_definition", "OrbitDefinition"),
            ("positive_orbit", "PositiveOrbit"),
        ],
        "AdjacentDropInequality",
        "AdjacentDropInequality(xseq)",
        "functional_inequality",
        ["f", "xseq", "n"],
    ),
    rule(
        "drops_nonnegative",
        "Rewrite two-step descent using the drop definition",
        [
            ("drop_definition", "DropDefinition"),
            ("orbit_descent", "OrbitTwoStepDescent"),
        ],
        "NonnegativeDrops",
        "NonnegativeDrops(d)",
        "ordered_algebra",
        ["d", "xseq", "n"],
    ),
    rule(
        "drops_nondecreasing",
        "Rewrite the adjacent comparison using the drop definition",
        [
            ("drop_definition", "DropDefinition"),
            ("adjacent_comparison", "AdjacentDropInequality"),
        ],
        "MonotoneDrops",
        "MonotoneDrops(d)",
        "ordered_algebra",
        ["d", "xseq", "n"],
    ),
    rule(
        "even_telescoping",
        "Telescope the even orbit subsequence",
        [
            ("orbit_definition", "OrbitDefinition"),
            ("drop_definition", "DropDefinition"),
        ],
        "EvenTelescopingIdentity",
        "EvenTelescopingIdentity(xseq,d)",
        "finite_sum",
        ["xseq", "d", "N"],
    ),
    rule(
        "positive_orbit_bounds_drop_sum",
        "Positivity bounds every even-indexed drop sum",
        [
            ("positive_orbit", "PositiveOrbit"),
            ("telescoping", "EvenTelescopingIdentity"),
        ],
        "EvenDropSumBound",
        "EvenDropSumBound(xseq,d)",
        "ordered_algebra",
        ["xseq", "d", "N"],
    ),
    rule(
        "monotone_drops_vanish",
        "A bounded sum of nonnegative nondecreasing drops forces zero drops",
        [
            ("nonnegative", "NonnegativeDrops"),
            ("nondecreasing", "MonotoneDrops"),
            ("bounded_even_sum", "EvenDropSumBound"),
        ],
        "DropsVanish",
        "DropsVanish(d)",
        "archimedean",
        ["d", "n", "N"],
    ),
    rule(
        "drops_zero_implies_involution",
        "The zero initial drop is the composition identity",
        [
            ("orbit_definition", "OrbitDefinition"),
            ("drop_definition", "DropDefinition"),
            ("drops_vanish", "DropsVanish"),
        ],
        "Involution",
        "Involution(f)",
        "iteration",
        ["f", "xseq", "d", "x"],
    ),
    rule(
        "condition_reduces_to_product_order",
        "Use involution in the original inequality",
        [("condition", "OriginalCondition"), ("involution", "Involution")],
        "ProductOrder",
        "ProductOrder(f)",
        "ordered_algebra",
        ["f", "x", "y"],
    ),
    rule(
        "swap_product_order",
        "Exchange the universally quantified variables",
        [("forward_order", "ProductOrder")],
        "ReverseProductOrder",
        "ReverseProductOrder(f)",
        "quantifier_symmetry",
        ["f", "x", "y"],
    ),
    rule(
        "product_order_antisymmetry",
        "Combine the two product inequalities",
        [
            ("forward_order", "ProductOrder"),
            ("reverse_order", "ReverseProductOrder"),
        ],
        "ProductConstantAcrossInputs",
        "ProductConstantAcrossInputs(f)",
        "order_antisymmetry",
        ["f", "x", "y"],
    ),
    rule(
        "extract_positive_constant",
        "Choose one input and name the common positive product",
        [
            ("positive_map", "PositiveMap"),
            ("constant_product", "ProductConstantAcrossInputs"),
        ],
        "ReciprocalNecessity",
        "ReciprocalNecessity(f)",
        "existence",
        ["f", "c", "x"],
    ),
    rule(
        "candidate_positive",
        "A positive reciprocal translate maps positives to positives",
        [("candidate_definition", "CandidateDefinition")],
        "CandidatePositive",
        "CandidatePositive(g)",
        "ordered_field",
        ["g", "c", "x"],
    ),
    rule(
        "candidate_involution",
        "The reciprocal candidate is an involution",
        [("candidate_definition", "CandidateDefinition")],
        "CandidateInvolution",
        "CandidateInvolution(g)",
        "field_simplification",
        ["g", "c", "x"],
    ),
    rule(
        "candidate_verification",
        "Directly substitute the reciprocal candidate",
        [
            ("candidate_definition", "CandidateDefinition"),
            ("candidate_positive", "CandidatePositive"),
            ("candidate_involution", "CandidateInvolution"),
        ],
        "CandidateSatisfies",
        "CandidateSatisfies(g)",
        "functional_inequality",
        ["g", "c", "x", "y"],
    ),
    rule(
        "necessity_and_sufficiency",
        "Combine necessity with direct verification",
        [
            ("necessity", "ReciprocalNecessity"),
            ("sufficiency", "CandidateSatisfies"),
        ],
        "Classification",
        "Classification(f,g)",
        "aggregation",
        ["f", "g", "c", "x"],
    ),
]


FACTS = [
    fact(
        "F1",
        "f maps every positive real number to a positive real number.",
        "PositiveMap(f)",
        "given",
        ["f"],
        ["problem"],
    ),
    fact(
        "F2",
        "For all positive x and y, x(f(x)+f(y)) >= (f(f(x))+y)f(y).",
        "OriginalCondition(f)",
        "given",
        ["f", "x", "y"],
        ["problem"],
    ),
    fact(
        "F3",
        "For arbitrary x>0, x_0=x and x_(n+1)=f(x_n).",
        "OrbitDefinition(f,xseq)",
        "constructed",
        ["f", "x", "xseq", "n"],
        ["proof:definition-orbit"],
    ),
    fact(
        "F4",
        "For every n, d_n=x_n-x_(n+2).",
        "DropDefinition(d,xseq)",
        "constructed",
        ["d", "xseq", "n"],
        ["proof:definition-drop"],
    ),
    fact(
        "F5",
        "For every c>0, define g_c(x)=c/x on the positive reals.",
        "CandidateDefinition(g,c)",
        "constructed",
        ["g", "c", "x"],
        ["proof:candidate-definition"],
    ),
    fact(
        "F6",
        "Every forward-orbit term x_n is positive.",
        "PositiveOrbit(f,xseq)",
        "derived",
        ["f", "xseq", "n"],
        ["proof:S1"],
    ),
    fact(
        "F7",
        "For every positive x, f(f(x)) <= x.",
        "TwoStepDescent(f)",
        "derived",
        ["f", "x"],
        ["proof:S2"],
    ),
    fact(
        "F8",
        "For every n>=0, x_(n+2) <= x_n.",
        "OrbitTwoStepDescent(xseq)",
        "derived",
        ["xseq", "n"],
        ["proof:S3"],
    ),
    fact(
        "F9",
        "For every n>=0, x_(n+1)+x_(n+2) >= x_n+x_(n+3).",
        "AdjacentDropInequality(xseq)",
        "derived",
        ["xseq", "n"],
        ["proof:S4"],
    ),
    fact(
        "F10",
        "For every n>=0, d_n>=0.",
        "NonnegativeDrops(d)",
        "derived",
        ["d", "n"],
        ["proof:S5"],
    ),
    fact(
        "F11",
        "For every n>=0, d_n<=d_(n+1).",
        "MonotoneDrops(d)",
        "derived",
        ["d", "n"],
        ["proof:S6"],
    ),
    fact(
        "F12",
        "For every N>=1, x_(2N)=x_0-sum_(j=0)^(N-1) d_(2j).",
        "EvenTelescopingIdentity(xseq,d)",
        "derived",
        ["xseq", "d", "N", "j"],
        ["proof:S7"],
    ),
    fact(
        "F13",
        "For every N>=1, sum_(j=0)^(N-1) d_(2j)<x_0.",
        "EvenDropSumBound(xseq,d)",
        "derived",
        ["xseq", "d", "N", "j"],
        ["proof:S8"],
    ),
    fact(
        "F14",
        "For every n>=0, d_n=0.",
        "DropsVanish(d)",
        "derived",
        ["d", "n"],
        ["proof:S9"],
    ),
    fact(
        "F15",
        "For every positive x, f(f(x))=x.",
        "Involution(f)",
        "derived",
        ["f", "x"],
        ["proof:S10"],
    ),
    fact(
        "F16",
        "For all positive x and y, x f(x)>=y f(y).",
        "ProductOrder(f)",
        "derived",
        ["f", "x", "y"],
        ["proof:S11"],
    ),
    fact(
        "F17",
        "For all positive x and y, y f(y)>=x f(x).",
        "ReverseProductOrder(f)",
        "derived",
        ["f", "x", "y"],
        ["proof:S12"],
    ),
    fact(
        "F18",
        "For all positive x and y, x f(x)=y f(y).",
        "ProductConstantAcrossInputs(f)",
        "derived",
        ["f", "x", "y"],
        ["proof:S13"],
    ),
    fact(
        "F19",
        "There exists c>0 such that f(x)=c/x for every positive x.",
        "ReciprocalNecessity(f)",
        "derived",
        ["f", "c", "x"],
        ["proof:S14"],
    ),
    fact(
        "F20",
        "For every c>0, g_c maps positive reals to positive reals.",
        "CandidatePositive(g)",
        "derived",
        ["g", "c", "x"],
        ["proof:S15"],
    ),
    fact(
        "F21",
        "For every c>0 and x>0, g_c(g_c(x))=x.",
        "CandidateInvolution(g)",
        "derived",
        ["g", "c", "x"],
        ["proof:S16"],
    ),
    fact(
        "F22",
        "Every g_c(x)=c/x with c>0 satisfies the original inequality.",
        "CandidateSatisfies(g)",
        "derived",
        ["g", "c", "x", "y"],
        ["proof:S17"],
    ),
    fact(
        "F23",
        "The solutions are exactly f(x)=c/x for constants c>0.",
        "Classification(f,g)",
        "derived",
        ["f", "g", "c", "x"],
        ["problem", "proof:S18"],
        goal=True,
    ),
]


INFERENCES = [
    inference(
        1,
        "positive_forward_orbit",
        [("F1", "positive_map"), ("F3", "orbit_definition")],
        "F6",
        {"f": "f", "xseq": "xseq", "n": "n"},
        [],
    ),
    inference(
        2,
        "two_step_descent",
        [("F1", "positive_map"), ("F2", "condition")],
        "F7",
        {"f": "f", "x": "x"},
        ["hidden_domain_condition", "nonlinear_arithmetic"],
    ),
    inference(
        3,
        "lift_descent_to_orbit",
        [("F3", "orbit_definition"), ("F7", "two_step_descent")],
        "F8",
        {"f": "f", "xseq": "xseq", "n": "n"},
        ["quantifier_sensitive"],
    ),
    inference(
        4,
        "adjacent_drop_comparison",
        [
            ("F1", "positive_map"),
            ("F2", "condition"),
            ("F3", "orbit_definition"),
            ("F6", "positive_orbit"),
        ],
        "F9",
        {"f": "f", "xseq": "xseq", "n": "n"},
        ["hidden_domain_condition", "nonlinear_arithmetic"],
    ),
    inference(
        5,
        "drops_nonnegative",
        [("F4", "drop_definition"), ("F8", "orbit_descent")],
        "F10",
        {"d": "d", "xseq": "xseq", "n": "n"},
        [],
    ),
    inference(
        6,
        "drops_nondecreasing",
        [("F4", "drop_definition"), ("F9", "adjacent_comparison")],
        "F11",
        {"d": "d", "xseq": "xseq", "n": "n"},
        [],
    ),
    inference(
        7,
        "even_telescoping",
        [("F3", "orbit_definition"), ("F4", "drop_definition")],
        "F12",
        {"xseq": "xseq", "d": "d", "N": "N"},
        ["quantifier_sensitive"],
    ),
    inference(
        8,
        "positive_orbit_bounds_drop_sum",
        [("F6", "positive_orbit"), ("F12", "telescoping")],
        "F13",
        {"xseq": "xseq", "d": "d", "N": "N"},
        ["nonlinear_arithmetic"],
    ),
    inference(
        9,
        "monotone_drops_vanish",
        [
            ("F10", "nonnegative"),
            ("F11", "nondecreasing"),
            ("F13", "bounded_even_sum"),
        ],
        "F14",
        {"d": "d", "n": "n", "N": "N"},
        ["quantifier_sensitive", "large_lemma_compression"],
    ),
    inference(
        10,
        "drops_zero_implies_involution",
        [
            ("F3", "orbit_definition"),
            ("F4", "drop_definition"),
            ("F14", "drops_vanish"),
        ],
        "F15",
        {"f": "f", "xseq": "xseq", "d": "d", "x": "x"},
        [],
    ),
    inference(
        11,
        "condition_reduces_to_product_order",
        [("F2", "condition"), ("F15", "involution")],
        "F16",
        {"f": "f", "x": "x", "y": "y"},
        ["nonlinear_arithmetic"],
    ),
    inference(
        12,
        "swap_product_order",
        [("F16", "forward_order")],
        "F17",
        {"f": "f", "x": "x", "y": "y"},
        ["quantifier_sensitive"],
    ),
    inference(
        13,
        "product_order_antisymmetry",
        [("F16", "forward_order"), ("F17", "reverse_order")],
        "F18",
        {"f": "f", "x": "x", "y": "y"},
        [],
    ),
    inference(
        14,
        "extract_positive_constant",
        [("F1", "positive_map"), ("F18", "constant_product")],
        "F19",
        {"f": "f", "c": "c", "x": "x"},
        ["existence_witness", "quantifier_sensitive"],
    ),
    inference(
        15,
        "candidate_positive",
        [("F5", "candidate_definition")],
        "F20",
        {"g": "g", "c": "c", "x": "x"},
        ["hidden_domain_condition"],
    ),
    inference(
        16,
        "candidate_involution",
        [("F5", "candidate_definition")],
        "F21",
        {"g": "g", "c": "c", "x": "x"},
        ["hidden_domain_condition", "nonlinear_arithmetic"],
    ),
    inference(
        17,
        "candidate_verification",
        [
            ("F5", "candidate_definition"),
            ("F20", "candidate_positive"),
            ("F21", "candidate_involution"),
        ],
        "F22",
        {"g": "g", "c": "c", "x": "x", "y": "y"},
        ["nonlinear_arithmetic"],
    ),
    inference(
        18,
        "necessity_and_sufficiency",
        [("F19", "necessity"), ("F22", "sufficiency")],
        "F23",
        {"f": "f", "g": "g", "c": "c", "x": "x"},
        ["quantifier_sensitive"],
    ),
]


def main() -> None:
    problem_text = (HERE / "problem.md").read_text(encoding="utf-8")
    proof_text = (
        problem_text.split("## Reviewed Natural-Language Proof", 1)[1]
        .split("## Review Status", 1)[0]
        .strip()
    )
    source_record = {
        "problem_source": "HuggingFace:ShadenA/MathNet problem 0gif",
        "solution_source": "human-reviewed blind proof in problem.md",
        "source_record_id": "mathnet:all:train:17595:2567d5bd3f85",
        "source_hash": (
            "3d0e9b57196b5f7df9b908c3591fc46648059d33206a29c75ec6dfc54a5b8f8b"
        ),
        "candidate_reference_solution_hash": sha256_text(proof_text),
        "reviewed_solution_hash": sha256_text(proof_text),
    }
    graph = {
        "schema_version": "proof-dag-schema-v0.4",
        "graph_kind": "reference",
        "graph_id": "0gif-reference-v0.1",
        "problem_id": "0gif",
        "target_fact_ids": ["F23"],
        "versions": {
            "skill_standard": "0.3",
            "dag_schema": "proof-dag-schema-v0.4",
            "fact_schema": "fact-v0.4",
            "inference_schema": "inference-v0.4",
            "scope_schema": "scope-v0.4",
            "mutation_schema": "mutation-v0.4",
            "canonicalizer": "math-expression-v1",
            "rule_registry": "functional-iteration-rules-v1",
            "common_tooling": "proof-dag-lean-v0.4",
            "domain_skill": "olympiad-algebra-expert-v0.1",
        },
        "source_record": source_record,
        "scopes": [{"id": "global", "parent_id": None, "kind": "global"}],
        "rule_schemas": RULES,
        "facts": FACTS,
        "inferences": INFERENCES,
        "provenance": {
            "source": "data/algebra_skill_curriculum + reviewed problem.md",
            "current_annotation_level": "synthetic",
            "requested_target_level": "silver_verified",
            "achieved_annotation_level": "pending",
            "promotion_profile": "algebra-reference-dag-v0.1",
            "proof_review": {
                "method": "human",
                "status": "passed",
                "reviewer": "Ruan Haochen (Eddie)",
                "review_date": "2026-07-28",
            },
            "dag_semantic_review": {
                "method": "human",
                "status": "passed",
                "reviewer": "Ruan Haochen (Eddie)",
                "review_date": "2026-07-28",
                "evidence": "dag_semantic_review.md",
            },
            "alternative_paths": {
                "status": "none_claimed",
                "notes": "The reviewed blind proof contains one necessity route and one sufficiency branch, not alternative producers for the same intermediate Fact.",
            },
        },
    }
    (HERE / "source_record.json").write_text(
        json.dumps(source_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (HERE / "reference_dag.json").write_text(
        json.dumps(graph, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (HERE / "correct_evaluation.json").write_text(
        json.dumps(evaluate_graph(graph), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
