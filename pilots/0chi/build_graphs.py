"""Generate the v0.3 correct and single-mutation DAGs for problem 0chi."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent


RULE_SCHEMAS: list[dict[str, Any]] = [
    {
        "rule_id": "second_symmetric_is_real",
        "name": "Equal modulus and real symmetric sums",
        "category": "complex_algebra",
        "input_patterns": [
            {"premise_role": "nonzero_anchor", "predicate": "Nonzero"},
            {"premise_role": "equal_norm_ab", "predicate": "EqualNorm"},
            {"premise_role": "equal_norm_ac", "predicate": "EqualNorm"},
            {"premise_role": "real_first_sum", "predicate": "IsReal"},
            {"premise_role": "real_product", "predicate": "IsReal"},
            {"premise_role": "definition_A", "predicate": "Definition"},
            {"premise_role": "definition_B", "predicate": "Definition"},
            {"premise_role": "definition_S", "predicate": "Definition"},
        ],
        "variables": ["a", "b", "c", "A", "B", "S"],
        "variable_constraints": ["a != 0", "norm(a)=norm(b)=norm(c)"],
        "output_pattern": {
            "predicate": "IsReal",
            "canonical_form": "IsReal(S)",
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    },
    {
        "rule_id": "power_sum_zero_is_real",
        "name": "Expand C(0)",
        "category": "definition_expansion",
        "input_patterns": [
            {"premise_role": "definition_C", "predicate": "Definition"}
        ],
        "variables": ["a", "b", "c", "C"],
        "variable_constraints": [],
        "output_pattern": {
            "predicate": "IsReal",
            "canonical_form": "IsReal(C(0))",
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    },
    {
        "rule_id": "power_sum_one_is_real",
        "name": "Rewrite C(1) as A",
        "category": "definition_expansion",
        "input_patterns": [
            {"premise_role": "real_A", "predicate": "IsReal"},
            {"premise_role": "definition_A", "predicate": "Definition"},
            {"premise_role": "definition_C", "predicate": "Definition"},
        ],
        "variables": ["a", "b", "c", "A", "C"],
        "variable_constraints": [],
        "output_pattern": {
            "predicate": "IsReal",
            "canonical_form": "IsReal(C(1))",
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    },
    {
        "rule_id": "power_sum_two_is_real",
        "name": "Use C(2)=A^2-2S",
        "category": "symmetric_identity",
        "input_patterns": [
            {"premise_role": "real_A", "predicate": "IsReal"},
            {"premise_role": "real_S", "predicate": "IsReal"},
            {"premise_role": "definition_A", "predicate": "Definition"},
            {"premise_role": "definition_S", "predicate": "Definition"},
            {"premise_role": "definition_C", "predicate": "Definition"},
        ],
        "variables": ["a", "b", "c", "A", "S", "C"],
        "variable_constraints": [],
        "output_pattern": {
            "predicate": "IsReal",
            "canonical_form": "IsReal(C(2))",
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    },
    {
        "rule_id": "power_sum_recurrence",
        "name": "Vieta power-sum recurrence",
        "category": "polynomial_identity",
        "input_patterns": [
            {"premise_role": "definition_A", "predicate": "Definition"},
            {"premise_role": "definition_B", "predicate": "Definition"},
            {"premise_role": "definition_S", "predicate": "Definition"},
            {"premise_role": "definition_C", "predicate": "Definition"},
        ],
        "variables": ["a", "b", "c", "A", "B", "S", "C", "n"],
        "variable_constraints": ["n is a natural number"],
        "output_pattern": {
            "predicate": "Recurrence",
            "canonical_form": (
                "Recurrence(C(n+3),Add(Sub(Mul(A,C(n+2)),Mul(S,C(n+1))),"
                "Mul(B,C(n))))"
            ),
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    },
    {
        "rule_id": "strong_induction_real_power_sums",
        "name": "Strong induction over the recurrence",
        "category": "induction",
        "input_patterns": [
            {"premise_role": "real_A", "predicate": "IsReal"},
            {"premise_role": "real_B", "predicate": "IsReal"},
            {"premise_role": "real_S", "predicate": "IsReal"},
            {"premise_role": "base_C0", "predicate": "IsReal"},
            {"premise_role": "base_C1", "predicate": "IsReal"},
            {"premise_role": "base_C2", "predicate": "IsReal"},
            {"premise_role": "recurrence", "predicate": "Recurrence"},
        ],
        "variables": ["A", "B", "S", "C", "n"],
        "variable_constraints": ["n is a natural number"],
        "output_pattern": {
            "predicate": "ForAll",
            "canonical_form": "ForAll(n,IsReal(C(n)))",
        },
        "scope_constraints": ["inputs_visible_from_inference_scope"],
        "version": 1,
    },
]


def fact(
    fact_id: str,
    statement: str,
    canonical_form: str,
    introduction_kind: str,
    roles: list[str],
    objects: list[str],
    source_spans: list[str],
    *,
    support_status: str = "supported",
    lean_declaration: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": fact_id,
        "statement": statement,
        "canonical_form": canonical_form,
        "introduction_kind": introduction_kind,
        "roles": roles,
        "scope": "global",
        "support_status": support_status,
        "availability_status": "active",
        "objects": objects,
        "source_spans": source_spans,
    }
    if lean_declaration is not None:
        value["lean_declaration"] = lean_declaration
    return value


def inference(
    inference_id: str,
    order: int,
    rule_id: str,
    bindings: list[tuple[str, str]],
    variables: dict[str, str],
    output_fact_id: str,
    source_span: str,
    *,
    validation_status: str = "valid",
    invalid_reason_codes: list[str] | None = None,
    lean_declaration: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "id": inference_id,
        "spu_id": f"SPU{order}",
        "order": order,
        "rule_id": rule_id,
        "scope": "global",
        "input_bindings": [
            {"fact_id": fact_id, "premise_role": role}
            for fact_id, role in bindings
        ],
        "variable_bindings": variables,
        "output_fact_id": output_fact_id,
        "validation_status": validation_status,
        "invalid_reason_codes": invalid_reason_codes or [],
        "source_spans": [source_span],
    }
    if lean_declaration is not None:
        value["lean_declaration"] = lean_declaration
    return value


def base_graph() -> dict[str, Any]:
    facts = [
        fact("F1", "a is nonzero.", "Nonzero(a)", "given", ["intermediate"], ["a"], ["problem"]),
        fact("F1b", "b is nonzero.", "Nonzero(b)", "given", ["intermediate"], ["b"], ["problem"]),
        fact("F1c", "c is nonzero.", "Nonzero(c)", "given", ["intermediate"], ["c"], ["problem"]),
        fact("F2", "a and b have the same modulus.", "EqualNorm(a,b)", "given", ["intermediate"], ["a", "b"], ["problem"]),
        fact("F2c", "a and c have the same modulus.", "EqualNorm(a,c)", "given", ["intermediate"], ["a", "c"], ["problem"]),
        fact("F3", "A is real.", "IsReal(A)", "given", ["intermediate"], ["A"], ["problem"]),
        fact("F4", "B is real.", "IsReal(B)", "given", ["intermediate"], ["B"], ["problem"]),
        fact("F5", "A = a + b + c.", "Definition(A,Add(a,b,c))", "definition", ["intermediate"], ["A", "a", "b", "c"], ["problem"]),
        fact("F6", "B = a*b*c.", "Definition(B,Mul(a,b,c))", "definition", ["intermediate"], ["B", "a", "b", "c"], ["problem"]),
        fact("F7", "S = a*b + b*c + c*a.", "Definition(S,Add(Mul(a,b),Mul(b,c),Mul(c,a)))", "definition", ["intermediate"], ["S", "a", "b", "c"], ["proof:S1"]),
        fact("F8", "For every n, C_n = a^n + b^n + c^n.", "Definition(C(n),Add(Pow(a,n),Pow(b,n),Pow(c,n)))", "definition", ["intermediate"], ["C", "n", "a", "b", "c"], ["problem"]),
        fact("F9", "S is real.", "IsReal(S)", "derived", ["intermediate"], ["S"], ["proof:S2"], lean_declaration="ProofDag0chi.secondSymmetric_isReal"),
        fact("F10", "C_0 is real.", "IsReal(C(0))", "derived", ["intermediate"], ["C"], ["proof:S3"]),
        fact("F11", "C_1 is real.", "IsReal(C(1))", "derived", ["intermediate"], ["C"], ["proof:S4"]),
        fact("F12", "C_2 is real.", "IsReal(C(2))", "derived", ["intermediate"], ["C"], ["proof:S5"]),
        fact(
            "F13",
            "For every n, C_(n+3) = A*C_(n+2) - S*C_(n+1) + B*C_n.",
            "Recurrence(C(n+3),Add(Sub(Mul(A,C(n+2)),Mul(S,C(n+1))),Mul(B,C(n))))",
            "derived",
            ["intermediate"],
            ["A", "B", "S", "C", "n"],
            ["proof:S6"],
            lean_declaration="ProofDag0chi.powerSum_recurrence",
        ),
        fact(
            "F14",
            "For every natural number n, C_n is real.",
            "ForAll(n,IsReal(C(n)))",
            "derived",
            ["goal"],
            ["C", "n"],
            ["problem", "proof:S7"],
            lean_declaration="ProofDag0chi.all_powerSums_real",
        ),
    ]
    inferences = [
        inference(
            "I1",
            1,
            "second_symmetric_is_real",
            [
                ("F1", "nonzero_anchor"),
                ("F2", "equal_norm_ab"),
                ("F2c", "equal_norm_ac"),
                ("F3", "real_first_sum"),
                ("F4", "real_product"),
                ("F5", "definition_A"),
                ("F6", "definition_B"),
                ("F7", "definition_S"),
            ],
            {"a": "a", "b": "b", "c": "c", "A": "A", "B": "B", "S": "S"},
            "F9",
            "proof:S2",
            lean_declaration="ProofDag0chi.secondSymmetric_isReal",
        ),
        inference(
            "I2",
            2,
            "power_sum_zero_is_real",
            [("F8", "definition_C")],
            {"a": "a", "b": "b", "c": "c", "C": "C"},
            "F10",
            "proof:S3",
        ),
        inference(
            "I3",
            3,
            "power_sum_one_is_real",
            [("F3", "real_A"), ("F5", "definition_A"), ("F8", "definition_C")],
            {"a": "a", "b": "b", "c": "c", "A": "A", "C": "C"},
            "F11",
            "proof:S4",
        ),
        inference(
            "I4",
            4,
            "power_sum_two_is_real",
            [
                ("F3", "real_A"),
                ("F9", "real_S"),
                ("F5", "definition_A"),
                ("F7", "definition_S"),
                ("F8", "definition_C"),
            ],
            {"a": "a", "b": "b", "c": "c", "A": "A", "S": "S", "C": "C"},
            "F12",
            "proof:S5",
        ),
        inference(
            "I5",
            5,
            "power_sum_recurrence",
            [
                ("F5", "definition_A"),
                ("F6", "definition_B"),
                ("F7", "definition_S"),
                ("F8", "definition_C"),
            ],
            {
                "a": "a",
                "b": "b",
                "c": "c",
                "A": "A",
                "B": "B",
                "S": "S",
                "C": "C",
                "n": "n",
            },
            "F13",
            "proof:S6",
            lean_declaration="ProofDag0chi.powerSum_recurrence",
        ),
        inference(
            "I6",
            6,
            "strong_induction_real_power_sums",
            [
                ("F3", "real_A"),
                ("F4", "real_B"),
                ("F9", "real_S"),
                ("F10", "base_C0"),
                ("F11", "base_C1"),
                ("F12", "base_C2"),
                ("F13", "recurrence"),
            ],
            {"A": "A", "B": "B", "S": "S", "C": "C", "n": "n"},
            "F14",
            "proof:S7",
            lean_declaration="ProofDag0chi.all_powerSums_real",
        ),
    ]
    return {
        "schema_version": "proof-dag-v0.3",
        "graph_id": "0chi-correct-v2",
        "problem_id": "0chi",
        "canonicalizer_version": "math-expression-v1",
        "target_fact_ids": ["F14"],
        "scopes": [
            {
                "id": "global",
                "parent_id": None,
                "kind": "global",
                "availability_status": "active",
            }
        ],
        "scope_evaluations": [
            {
                "scope_id": "global",
                "consistency_status": "consistent",
                "conflicting_fact_ids": [],
            }
        ],
        "rule_schemas": copy.deepcopy(RULE_SCHEMAS),
        "facts": facts,
        "inferences": inferences,
        "provenance": {
            "source": "proof_750_non_geometry_sample_v4(1).csv:0chi",
            "annotation_level": "synthetic",
            "reviewers": [],
            "lean_coverage": "end_to_end",
            "team_spec_alignment": "Node normalization draft + critical-node v1 + error-injection v1",
        },
    }


def mutated_graph(correct: dict[str, Any]) -> dict[str, Any]:
    graph = copy.deepcopy(correct)
    graph["graph_id"] = "0chi-wrong-sign-v2"
    graph["facts_by_id"] = {fact["id"]: fact for fact in graph["facts"]}
    recurrence = graph["facts_by_id"]["F13"]
    recurrence["statement"] = (
        "For every n, C_(n+3) = A*C_(n+2) - S*C_(n+1) - B*C_n."
    )
    recurrence["canonical_form"] = (
        "Recurrence(C(n+3),Sub(Sub(Mul(A,C(n+2)),Mul(S,C(n+1))),Mul(B,C(n))))"
    )
    recurrence["support_status"] = "unsupported"
    recurrence.pop("lean_declaration", None)
    graph["facts_by_id"]["F14"]["support_status"] = "unsupported"
    del graph["facts_by_id"]

    inference_by_id = {
        inference["id"]: inference for inference in graph["inferences"]
    }
    inference_by_id["I5"]["validation_status"] = "invalid"
    inference_by_id["I5"]["invalid_reason_codes"] = [
        "output_mismatch",
        "wrong_sign",
    ]
    inference_by_id["I5"][
        "lean_declaration"
    ] = "ProofDag0chi.wrongSign_recurrence_counterexample"
    inference_by_id["I6"]["validation_status"] = "invalid"
    inference_by_id["I6"]["invalid_reason_codes"] = ["unsupported_input"]
    graph["mutation"] = {
        "base_graph_id": correct["graph_id"],
        "operation": "alter_output",
        "primary_inference_id": "I5",
        "expected_first_break": "I5",
        "before": (
            "C_(n+3) = A*C_(n+2) - S*C_(n+1) + B*C_n"
        ),
        "after": (
            "C_(n+3) = A*C_(n+2) - S*C_(n+1) - B*C_n"
        ),
    }
    graph["provenance"] = {
        "source": f"controlled mutation of {correct['graph_id']}",
        "annotation_level": "synthetic",
        "reviewers": [],
        "lean_coverage": "local_counterexample",
        "team_spec_alignment": "single controlled modification with downstream recomputation",
    }
    return graph


def write_graph(path: Path, graph: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    correct = base_graph()
    wrong = mutated_graph(correct)
    write_graph(HERE / "correct_dag.json", correct)
    write_graph(HERE / "mutated_dag.json", wrong)


if __name__ == "__main__":
    main()
