"""Build the schema-v0.4 Reference DAG for polynomial problem 00q2."""

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
    variables: list[str],
    *,
    category: str = "polynomial",
    scope_constraints: list[str] | None = None,
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
        "scope_constraints": scope_constraints
        or ["inputs_visible_from_inference_scope"],
        "version": 1,
    }


def fact(
    fact_id: str,
    statement: str,
    canonical_form: str,
    introduction_kind: str,
    scope: str,
    objects: list[str],
    source_span: str,
    *,
    roles: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "statement": statement,
        "canonical_form": canonical_form,
        "introduction_kind": introduction_kind,
        "roles": roles or ["intermediate"],
        "scope": scope,
        "objects": objects,
        "source_spans": [source_span],
    }


def inference(
    number: int,
    rule_id: str,
    inputs: list[tuple[str, str]],
    output: str,
    scope: str,
    variables: dict[str, str],
    risk_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"I{number}",
        "spu_id": f"SPU{number}",
        "source_order": number,
        "rule_id": rule_id,
        "scope": scope,
        "input_bindings": [
            {"fact_id": fact_id, "premise_role": role}
            for fact_id, role in inputs
        ],
        "variable_bindings": variables,
        "output_fact_id": output,
        "source_spans": [f"proof:S{number}"],
        "risk_flags": risk_flags or [],
    }


GLOBAL = "global"
NEC = "global/necessity"
CASE = "global/necessity/case_gt_one"
SUFF = "global/sufficiency"


RULES = [
    rule(
        "quotient_witness",
        "Expand polynomial divisibility as a quotient identity",
        [("divisibility", "Divisibility")],
        "QuotientIdentity",
        "QuotientIdentity(fn,gn,h)",
        ["fn", "gn", "h"],
    ),
    rule(
        "split_extreme_components",
        "Identify the degree-2 and degree-2n components of f_n when n>1",
        [("definitions", "PolynomialDefinitions"), ("case", "GreaterThanOne")],
        "ExtremeDegreeDecomposition",
        "ExtremeDegreeDecomposition(fn,2,2n)",
        ["fn", "n"],
    ),
    rule(
        "quotient_extreme_degrees",
        "Choose the lowest and highest nonzero homogeneous parts of h",
        [("quotient", "QuotientIdentity")],
        "QuotientExtremeDegrees",
        "QuotientExtremeDegrees(h,l,u)",
        ["h", "l", "u"],
    ),
    rule(
        "extreme_index_order",
        "The lowest nonzero degree does not exceed the highest",
        [("extrema", "QuotientExtremeDegrees")],
        "IndexOrder",
        "IndexOrder(l,u)",
        ["l", "u"],
    ),
    rule(
        "lowest_product_component",
        "The unique lowest product component is F_2 h_l",
        [
            ("decomposition", "ExtremeDegreeDecomposition"),
            ("extrema", "QuotientExtremeDegrees"),
            ("quotient", "QuotientIdentity"),
        ],
        "LowestProductDegree",
        "LowestProductDegree(l+2)",
        ["fn", "gn", "h", "l", "n"],
    ),
    rule(
        "highest_product_component",
        "The unique highest product component is F_2n h_u",
        [
            ("decomposition", "ExtremeDegreeDecomposition"),
            ("extrema", "QuotientExtremeDegrees"),
            ("quotient", "QuotientIdentity"),
        ],
        "HighestProductDegree",
        "HighestProductDegree(u+2n)",
        ["fn", "gn", "h", "u", "n"],
    ),
    rule(
        "match_lowest_degree",
        "A nonzero component of a homogeneous polynomial has degree 5n",
        [
            ("definitions", "PolynomialDefinitions"),
            ("lowest", "LowestProductDegree"),
        ],
        "LowestDegreeEquation",
        "LowestDegreeEquation(l+2,5n)",
        ["gn", "l", "n"],
    ),
    rule(
        "match_highest_degree",
        "The highest component also has homogeneous degree 5n",
        [
            ("definitions", "PolynomialDefinitions"),
            ("highest", "HighestProductDegree"),
        ],
        "HighestDegreeEquation",
        "HighestDegreeEquation(u+2n,5n)",
        ["gn", "u", "n"],
    ),
    rule(
        "solve_lowest_index",
        "Solve l+2=5n",
        [("equation", "LowestDegreeEquation")],
        "LowestIndexValue",
        "LowestIndexValue(l,5n-2)",
        ["l", "n"],
        category="arithmetic",
    ),
    rule(
        "solve_highest_index",
        "Solve u+2n=5n",
        [("equation", "HighestDegreeEquation")],
        "HighestIndexValue",
        "HighestIndexValue(u,3n)",
        ["u", "n"],
        category="arithmetic",
    ),
    rule(
        "index_order_bounds_n",
        "Combine l<=u with the solved extreme degrees",
        [
            ("order", "IndexOrder"),
            ("lowest_value", "LowestIndexValue"),
            ("highest_value", "HighestIndexValue"),
        ],
        "UpperBoundOnN",
        "UpperBoundOnN(n,1)",
        ["l", "u", "n"],
        category="arithmetic",
    ),
    rule(
        "case_contradiction",
        "The assumptions n>1 and n<=1 contradict",
        [("case", "GreaterThanOne"), ("bound", "UpperBoundOnN")],
        "Contradiction",
        "Contradiction(n>1,n<=1)",
        ["n"],
        category="logic",
    ),
    rule(
        "discharge_gt_one",
        "Discharge the n>1 contradiction inside the necessity branch",
        [("case", "GreaterThanOne"), ("contradiction", "Contradiction")],
        "UpperBoundOnN",
        "UpperBoundOnN(n,1)",
        ["n"],
        category="logic",
        scope_constraints=[
            "inputs_visible_from_inference_scope",
            "allow_scope_discharge",
        ],
    ),
    rule(
        "positive_integer_bound",
        "A positive integer not exceeding 1 equals 1",
        [("positive_integer", "PositiveInteger"), ("bound", "UpperBoundOnN")],
        "EqualsOne",
        "EqualsOne(n)",
        ["n"],
        category="arithmetic",
    ),
    rule(
        "discharge_necessity",
        "Discharge the divisibility assumption as the necessity implication",
        [("divisibility", "Divisibility"), ("equals_one", "EqualsOne")],
        "DividesImpliesOne",
        "DividesImpliesOne(fn,gn,n)",
        ["fn", "gn", "n"],
        category="logic",
        scope_constraints=[
            "inputs_visible_from_inference_scope",
            "allow_scope_discharge",
        ],
    ),
    rule(
        "difference_substitution",
        "Introduce p=x-y, q=y-z, r=z-x for n=1",
        [("case", "EqualsOne"), ("definitions", "PolynomialDefinitions")],
        "DifferenceVariables",
        "DifferenceVariables(p,q,r,x,y,z)",
        ["p", "q", "r", "x", "y", "z"],
    ),
    rule(
        "difference_sum_zero",
        "The cyclic differences sum to zero",
        [("differences", "DifferenceVariables")],
        "DifferenceSumZero",
        "DifferenceSumZero(p,q,r)",
        ["p", "q", "r"],
        category="algebraic_identity",
    ),
    rule(
        "fifth_power_identity",
        "Apply the fifth-power identity under p+q+r=0",
        [("sum_zero", "DifferenceSumZero")],
        "FifthPowerIdentity",
        "FifthPowerIdentity(p,q,r)",
        ["p", "q", "r"],
        category="algebraic_identity",
    ),
    rule(
        "quadratic_difference_identity",
        "Rewrite f_1 as half the cyclic squared-difference sum",
        [
            ("definitions", "PolynomialDefinitions"),
            ("differences", "DifferenceVariables"),
        ],
        "QuadraticDifferenceIdentity",
        "QuadraticDifferenceIdentity(f1,p,q,r)",
        ["f1", "p", "q", "r"],
        category="algebraic_identity",
    ),
    rule(
        "factor_g1",
        "Combine the two identities to factor g_1 by f_1",
        [
            ("fifth_identity", "FifthPowerIdentity"),
            ("quadratic_identity", "QuadraticDifferenceIdentity"),
            ("definitions", "PolynomialDefinitions"),
        ],
        "G1Factorization",
        "G1Factorization(g1,f1,p,q,r)",
        ["g1", "f1", "p", "q", "r"],
        category="factorization",
    ),
    rule(
        "factorization_implies_divisibility",
        "An explicit polynomial factorization proves divisibility",
        [("factorization", "G1Factorization")],
        "Divisibility",
        "Divisibility(f1,g1)",
        ["f1", "g1"],
    ),
    rule(
        "discharge_sufficiency",
        "Discharge n=1 as the sufficiency implication",
        [("case", "EqualsOne"), ("divisibility", "Divisibility")],
        "OneImpliesDivides",
        "OneImpliesDivides(fn,gn,n)",
        ["fn", "gn", "n"],
        category="logic",
        scope_constraints=[
            "inputs_visible_from_inference_scope",
            "allow_scope_discharge",
        ],
    ),
    rule(
        "necessity_and_sufficiency",
        "Combine both implications into the exact classification",
        [
            ("necessity", "DividesImpliesOne"),
            ("sufficiency", "OneImpliesDivides"),
        ],
        "ExactClassification",
        "ExactClassification(fn,gn,n)",
        ["fn", "gn", "n"],
        category="logic",
    ),
]


FACTS = [
    fact(
        "F1",
        "n is a positive integer.",
        "PositiveInteger(n)",
        "given",
        GLOBAL,
        ["n"],
        "problem:n-positive",
    ),
    fact(
        "F2",
        "f_n and g_n are the polynomials in the problem; g_n is homogeneous of degree 5n.",
        "PolynomialDefinitions(fn,gn,n)",
        "given",
        GLOBAL,
        ["fn", "gn", "n", "x", "y", "z"],
        "problem:definitions",
    ),
    fact(
        "F3",
        "Assume f_n divides g_n.",
        "Divisibility(fn,gn)",
        "assumed",
        NEC,
        ["fn", "gn"],
        "proof:necessity-assumption",
        roles=["case_condition"],
    ),
    fact(
        "F4",
        "There is a nonzero polynomial h such that g_n=f_n h.",
        "QuotientIdentity(fn,gn,h)",
        "derived",
        NEC,
        ["fn", "gn", "h"],
        "proof:quotient",
    ),
    fact(
        "F5",
        "Assume n>1 inside the contradiction subcase.",
        "GreaterThanOne(n)",
        "case_assumed",
        CASE,
        ["n"],
        "proof:case-n-gt-one",
        roles=["case_condition"],
    ),
    fact(
        "F6",
        "For n>1, f_n has nonzero extreme homogeneous components of degrees 2 and 2n.",
        "ExtremeDegreeDecomposition(fn,2,2n)",
        "derived",
        CASE,
        ["fn", "n"],
        "proof:split-f",
    ),
    fact(
        "F7",
        "Let l and u be the lowest and highest nonzero homogeneous degrees of h.",
        "QuotientExtremeDegrees(h,l,u)",
        "derived",
        CASE,
        ["h", "l", "u"],
        "proof:extreme-h",
    ),
    fact(
        "F8",
        "The extreme indices satisfy l<=u.",
        "IndexOrder(l,u)",
        "derived",
        CASE,
        ["l", "u"],
        "proof:index-order",
    ),
    fact(
        "F9",
        "The nonzero lowest homogeneous component of f_n h has degree l+2.",
        "LowestProductDegree(l+2)",
        "derived",
        CASE,
        ["fn", "h", "l"],
        "proof:lowest-product",
    ),
    fact(
        "F10",
        "The nonzero highest homogeneous component of f_n h has degree u+2n.",
        "HighestProductDegree(u+2n)",
        "derived",
        CASE,
        ["fn", "h", "u", "n"],
        "proof:highest-product",
    ),
    fact(
        "F11",
        "The lowest-degree comparison gives l+2=5n.",
        "LowestDegreeEquation(l+2,5n)",
        "derived",
        CASE,
        ["l", "n"],
        "proof:lowest-equation",
    ),
    fact(
        "F12",
        "The highest-degree comparison gives u+2n=5n.",
        "HighestDegreeEquation(u+2n,5n)",
        "derived",
        CASE,
        ["u", "n"],
        "proof:highest-equation",
    ),
    fact(
        "F13",
        "l=5n-2.",
        "LowestIndexValue(l,5n-2)",
        "derived",
        CASE,
        ["l", "n"],
        "proof:solve-l",
    ),
    fact(
        "F14",
        "u=3n.",
        "HighestIndexValue(u,3n)",
        "derived",
        CASE,
        ["u", "n"],
        "proof:solve-u",
    ),
    fact(
        "F15",
        "The extreme-index order forces n<=1.",
        "UpperBoundOnN(n,1)",
        "derived",
        CASE,
        ["n"],
        "proof:n-bound",
    ),
    fact(
        "F16",
        "The assumptions n>1 and n<=1 contradict.",
        "Contradiction(n>1,n<=1)",
        "derived",
        CASE,
        ["n"],
        "proof:contradiction",
        roles=["contradiction"],
    ),
    fact(
        "F17",
        "Within the divisibility branch, n<=1.",
        "UpperBoundOnN(n,1)",
        "derived",
        NEC,
        ["n"],
        "proof:discharge-gt-one",
    ),
    fact(
        "F18",
        "Within the divisibility branch, n=1.",
        "EqualsOne(n)",
        "derived",
        NEC,
        ["n"],
        "proof:necessity-one",
    ),
    fact(
        "F19",
        "If f_n divides g_n, then n=1.",
        "DividesImpliesOne(fn,gn,n)",
        "derived",
        GLOBAL,
        ["fn", "gn", "n"],
        "proof:necessity",
        roles=["lemma_output"],
    ),
    fact(
        "F20",
        "Assume n=1 for the sufficiency branch.",
        "EqualsOne(n)",
        "case_assumed",
        SUFF,
        ["n"],
        "proof:sufficiency-assumption",
        roles=["case_condition"],
    ),
    fact(
        "F21",
        "Define p=x-y, q=y-z, and r=z-x.",
        "DifferenceVariables(p,q,r,x,y,z)",
        "constructed",
        SUFF,
        ["p", "q", "r", "x", "y", "z"],
        "proof:differences",
    ),
    fact(
        "F22",
        "p+q+r=0.",
        "DifferenceSumZero(p,q,r)",
        "derived",
        SUFF,
        ["p", "q", "r"],
        "proof:sum-zero",
    ),
    fact(
        "F23",
        "p^5+q^5+r^5=(5/2)pqr(p^2+q^2+r^2).",
        "FifthPowerIdentity(p,q,r)",
        "derived",
        SUFF,
        ["p", "q", "r"],
        "proof:fifth-identity",
    ),
    fact(
        "F24",
        "f_1=(1/2)(p^2+q^2+r^2).",
        "QuadraticDifferenceIdentity(f1,p,q,r)",
        "derived",
        SUFF,
        ["f1", "p", "q", "r"],
        "proof:quadratic-identity",
    ),
    fact(
        "F25",
        "g_1=5pqr f_1.",
        "G1Factorization(g1,f1,p,q,r)",
        "derived",
        SUFF,
        ["g1", "f1", "p", "q", "r"],
        "proof:factorization",
    ),
    fact(
        "F26",
        "f_1 divides g_1.",
        "Divisibility(f1,g1)",
        "derived",
        SUFF,
        ["f1", "g1"],
        "proof:divisibility-n1",
    ),
    fact(
        "F27",
        "If n=1, then f_n divides g_n.",
        "OneImpliesDivides(fn,gn,n)",
        "derived",
        GLOBAL,
        ["fn", "gn", "n"],
        "proof:sufficiency",
        roles=["lemma_output"],
    ),
    fact(
        "F28",
        "For positive integers n, f_n divides g_n if and only if n=1.",
        "ExactClassification(fn,gn,n)",
        "derived",
        GLOBAL,
        ["fn", "gn", "n"],
        "proof:conclusion",
        roles=["goal"],
    ),
]


INFERENCES = [
    inference(1, "quotient_witness", [("F3", "divisibility")], "F4", NEC, {"fn": "f_n", "gn": "g_n", "h": "h"}),
    inference(2, "split_extreme_components", [("F2", "definitions"), ("F5", "case")], "F6", CASE, {"fn": "f_n", "n": "n"}),
    inference(3, "quotient_extreme_degrees", [("F4", "quotient")], "F7", CASE, {"h": "h", "l": "l", "u": "u"}),
    inference(4, "extreme_index_order", [("F7", "extrema")], "F8", CASE, {"l": "l", "u": "u"}),
    inference(
        5,
        "lowest_product_component",
        [("F6", "decomposition"), ("F7", "extrema"), ("F4", "quotient")],
        "F9",
        CASE,
        {"fn": "f_n", "gn": "g_n", "h": "h", "l": "l", "n": "n"},
        ["hidden_domain_condition", "large_lemma_compression"],
    ),
    inference(
        6,
        "highest_product_component",
        [("F6", "decomposition"), ("F7", "extrema"), ("F4", "quotient")],
        "F10",
        CASE,
        {"fn": "f_n", "gn": "g_n", "h": "h", "u": "u", "n": "n"},
        ["hidden_domain_condition", "large_lemma_compression"],
    ),
    inference(7, "match_lowest_degree", [("F2", "definitions"), ("F9", "lowest")], "F11", CASE, {"gn": "g_n", "l": "l", "n": "n"}),
    inference(8, "match_highest_degree", [("F2", "definitions"), ("F10", "highest")], "F12", CASE, {"gn": "g_n", "u": "u", "n": "n"}),
    inference(9, "solve_lowest_index", [("F11", "equation")], "F13", CASE, {"l": "l", "n": "n"}),
    inference(10, "solve_highest_index", [("F12", "equation")], "F14", CASE, {"u": "u", "n": "n"}),
    inference(11, "index_order_bounds_n", [("F8", "order"), ("F13", "lowest_value"), ("F14", "highest_value")], "F15", CASE, {"l": "l", "u": "u", "n": "n"}),
    inference(12, "case_contradiction", [("F5", "case"), ("F15", "bound")], "F16", CASE, {"n": "n"}),
    inference(13, "discharge_gt_one", [("F5", "case"), ("F16", "contradiction")], "F17", CASE, {"n": "n"}),
    inference(14, "positive_integer_bound", [("F1", "positive_integer"), ("F17", "bound")], "F18", NEC, {"n": "n"}),
    inference(15, "discharge_necessity", [("F3", "divisibility"), ("F18", "equals_one")], "F19", NEC, {"fn": "f_n", "gn": "g_n", "n": "n"}),
    inference(16, "difference_substitution", [("F20", "case"), ("F2", "definitions")], "F21", SUFF, {"p": "p", "q": "q", "r": "r", "x": "x", "y": "y", "z": "z"}),
    inference(17, "difference_sum_zero", [("F21", "differences")], "F22", SUFF, {"p": "p", "q": "q", "r": "r"}),
    inference(18, "fifth_power_identity", [("F22", "sum_zero")], "F23", SUFF, {"p": "p", "q": "q", "r": "r"}),
    inference(19, "quadratic_difference_identity", [("F2", "definitions"), ("F21", "differences")], "F24", SUFF, {"f1": "f_1", "p": "p", "q": "q", "r": "r"}),
    inference(20, "factor_g1", [("F23", "fifth_identity"), ("F24", "quadratic_identity"), ("F2", "definitions")], "F25", SUFF, {"g1": "g_1", "f1": "f_1", "p": "p", "q": "q", "r": "r"}),
    inference(21, "factorization_implies_divisibility", [("F25", "factorization")], "F26", SUFF, {"f1": "f_1", "g1": "g_1"}),
    inference(22, "discharge_sufficiency", [("F20", "case"), ("F26", "divisibility")], "F27", SUFF, {"fn": "f_n", "gn": "g_n", "n": "n"}),
    inference(23, "necessity_and_sufficiency", [("F19", "necessity"), ("F27", "sufficiency")], "F28", GLOBAL, {"fn": "f_n", "gn": "g_n", "n": "n"}),
]


def main() -> None:
    problem_text = (HERE / "problem.md").read_text(encoding="utf-8")
    proof_text = (
        problem_text.split("## Reviewed Natural-Language Proof", 1)[1]
        .split("## Review Status", 1)[0]
        .strip()
    )
    source_record = {
        "problem_source": "HuggingFace:ShadenA/MathNet problem 00q2",
        "solution_source": "human-reviewed blind proof in problem.md",
        "source_record_id": "mathnet:all:train:22204:e577c87c164f",
        "source_hash": "3f8d257b3e334d889b80dcbc81aca4684537329c0142168815e909ad5f58278d",
        "candidate_reference_solution_hash": sha256_text(proof_text),
        "reviewed_solution_hash": sha256_text(proof_text),
    }
    graph = {
        "schema_version": "proof-dag-schema-v0.4",
        "graph_kind": "reference",
        "graph_id": "00q2-reference-v0.1",
        "problem_id": "00q2",
        "target_fact_ids": ["F28"],
        "versions": {
            "skill_standard": "0.3",
            "dag_schema": "proof-dag-schema-v0.4",
            "fact_schema": "fact-v0.4",
            "inference_schema": "inference-v0.4",
            "scope_schema": "scope-v0.4",
            "mutation_schema": "mutation-v0.4",
            "canonicalizer": "math-expression-v1",
            "rule_registry": "polynomial-extreme-degree-rules-v1",
            "common_tooling": "proof-dag-lean-v0.4",
            "domain_skill": "olympiad-algebra-expert-v0.1",
        },
        "source_record": source_record,
        "scopes": [
            {"id": GLOBAL, "parent_id": None, "kind": "global"},
            {"id": NEC, "parent_id": GLOBAL, "kind": "lemma"},
            {"id": CASE, "parent_id": NEC, "kind": "contradiction"},
            {"id": SUFF, "parent_id": GLOBAL, "kind": "case"},
        ],
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
                "status": "not_run",
                "evidence": "dag_semantic_review.md",
            },
            "alternative_paths": {
                "status": "none_claimed",
                "notes": "Necessity and sufficiency are separate branches; no intermediate Fact has an alternative producer.",
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
