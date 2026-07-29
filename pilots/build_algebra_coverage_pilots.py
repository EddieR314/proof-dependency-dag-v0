"""Build schema-v0.4 DAG pilots for three reviewed algebra proofs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "proof-dag-lean" / "scripts"))

from check_artifact import check_mutation
from dag_core import evaluate_graph


def predicate(canonical: str) -> str:
    return canonical.split("(", 1)[0]


def fact(
    fact_id: str,
    statement: str,
    canonical: str,
    kind: str,
    scope: str = "global",
    *,
    roles: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "statement": statement,
        "canonical_form": canonical,
        "introduction_kind": kind,
        "roles": roles or ["intermediate"],
        "scope": scope,
        "objects": [],
        "source_spans": [f"reviewed-proof:{fact_id}"],
    }


def inference(
    index: int,
    name: str,
    inputs: list[tuple[str, str]],
    output: str,
    *,
    scope: str = "global",
    risks: list[str] | None = None,
    discharge: bool = False,
) -> dict[str, Any]:
    return {
        "id": f"I{index}",
        "spu_id": f"SPU{index}",
        "source_order": index,
        "rule_id": f"R{index}",
        "scope": scope,
        "input_bindings": [
            {"fact_id": fact_id, "premise_role": role}
            for fact_id, role in inputs
        ],
        "variable_bindings": {},
        "output_fact_id": output,
        "source_spans": [f"reviewed-proof:SPU{index}"],
        "risk_flags": risks or [],
        "_rule_name": name,
        "_discharge": discharge,
    }


def build_rules(
    facts: list[dict[str, Any]], inferences: list[dict[str, Any]], category: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    facts_by_id = {item["id"]: item for item in facts}
    rules = []
    cleaned = []
    for item in inferences:
        rule = {
            "rule_id": item["rule_id"],
            "name": item.pop("_rule_name"),
            "category": category,
            "input_patterns": [
                {
                    "premise_role": binding["premise_role"],
                    "predicate": predicate(
                        facts_by_id[binding["fact_id"]]["canonical_form"]
                    ),
                }
                for binding in item["input_bindings"]
            ],
            "variables": [],
            "variable_constraints": [],
            "output_pattern": {
                "predicate": predicate(
                    facts_by_id[item["output_fact_id"]]["canonical_form"]
                ),
                "canonical_form": facts_by_id[item["output_fact_id"]][
                    "canonical_form"
                ],
            },
            "scope_constraints": ["inputs_visible_from_inference_scope"],
            "version": 1,
        }
        if item.pop("_discharge"):
            rule["scope_constraints"].append("allow_scope_discharge")
        rules.append(rule)
        cleaned.append(item)
    return rules, cleaned


def spec_06og() -> dict[str, Any]:
    facts = [
        fact("F1", "n>=2 and all a_i are positive.", "PositiveFamily(a,n)", "given"),
        fact("F2", "S=sum a_i, E2=sum_{i<j} a_i a_j, and L is the left side.", "SumDefinitions(S,E2,L)", "constructed"),
        fact("F3", "The target is equivalent to 2SL <= nE2 because 2S>0.", "ScaledTargetEquivalent(S,L,n,E2)", "derived"),
        fact("F4", "2SL equals 2E2 plus the residual sum collected by triples.", "TripleExpansion(S,L,E2,T)", "derived"),
        fact("F5", "For positive a,b,c, 1/a+1/b >= 4/(a+b).", "PairReciprocalBound(a,b)", "derived"),
        fact("F6", "For each positive triple, 2abc sum_cyc 1/(a+b) <= ab+bc+ca.", "TripleReciprocalBound(a,b,c)", "derived"),
        fact("F7", "Summing the local triple inequality bounds the residual triple sum.", "SummedTripleBound(T,P)", "derived"),
        fact("F8", "Every unordered pair occurs in exactly n-2 unordered triples.", "PairTripleMultiplicity(n)", "derived"),
        fact("F9", "The pair sum over all triples equals (n-2)E2.", "TriplePairIdentity(P,n,E2)", "derived"),
        fact("F10", "The residual triple sum is at most (n-2)E2.", "ResidualBound(T,n,E2)", "derived"),
        fact("F11", "2SL <= nE2.", "ScaledInequality(S,L,n,E2)", "derived"),
        fact("F12", "The required inequality holds.", "TargetInequality(a,n)", "derived", roles=["goal"]),
    ]
    inferences = [
        inference(1, "Scale by the positive total sum", [("F1", "positivity"), ("F2", "definitions")], "F3", risks=["hidden_domain_condition"]),
        inference(2, "Expand the total sum and regroup by unordered triples", [("F2", "definitions")], "F4", risks=["large_lemma_compression"]),
        inference(3, "Apply AM-HM to each reciprocal pair", [("F1", "positivity")], "F5", risks=["external_theorem_dependency"]),
        inference(4, "Sum three cyclic bounds and multiply by abc", [("F5", "pair_bound"), ("F1", "positivity")], "F6", risks=["nonlinear_arithmetic"]),
        inference(5, "Sum the local inequality over all triples", [("F6", "local_bound")], "F7"),
        inference(6, "Count how many triples contain a fixed pair", [("F1", "index_range")], "F8", risks=["large_lemma_compression"]),
        inference(7, "Convert the triple pair sum to (n-2)E2", [("F8", "multiplicity"), ("F2", "definitions")], "F9"),
        inference(8, "Combine the local bound with pair multiplicity", [("F7", "summed_bound"), ("F9", "count_identity")], "F10"),
        inference(9, "Insert the residual estimate into the expansion", [("F4", "expansion"), ("F10", "residual_bound")], "F11"),
        inference(10, "Undo the positive scaling", [("F3", "equivalence"), ("F11", "scaled_result")], "F12", risks=["hidden_domain_condition"]),
    ]
    return {
        "problem_id": "06og",
        "module": "inequalities",
        "source_hash": "c893a7e5b392b907f83a81f17bc287df6109e64ea8ef1bc9012267930368840d",
        "facts": facts,
        "inferences": inferences,
        "target": "F12",
        "mutation": ("I8", "F9", "count_identity", "F9->I8"),
        "mutation_reason": "The proof bounds the residual without using the n-2 pair multiplicity identity.",
    }


def spec_0ldq() -> dict[str, Any]:
    facts = [
        fact("F1", "x_1=2 and x_{n+1}=sqrt(x_n+8)-sqrt(x_n+3).", "Recurrence(x)", "given"),
        fact("F2", "All x_n are positive.", "PositiveOrbit(x)", "derived"),
        fact("F3", "F(x)=sqrt(x+8)-sqrt(x+3) and F(1)=1.", "FixedPointMap(F)", "constructed"),
        fact("F4", "x_{n+1}-1=-rho(x_n)(x_n-1) with the stated rho.", "SignedDeviationIdentity(x,rho)", "derived"),
        fact("F5", "For x>=0, 0<rho(x)<1.", "PointwiseContraction(rho)", "derived"),
        fact("F6", "The deviations alternate sign and have nonincreasing magnitude.", "AlternatingDeviations(x)", "derived"),
        fact("F7", "The orbit remains in the compact interval [0,2].", "InvariantCompactInterval(x)", "derived"),
        fact("F8", "There is q<1 with rho(x)<=q throughout the orbit.", "UniformContraction(rho,q)", "derived"),
        fact("F9", "|x_n-1| <= q^(n-1), hence x_n tends to 1.", "ConvergenceToOne(x)", "derived"),
        fact("F10", "Every partial sum of d_i=x_i-1 lies in [0,1].", "AlternatingPartialSumBound(x)", "derived"),
        fact("F11", "n <= sum_{i=1}^n x_i <= n+1.", "SequenceSumBound(x,n)", "derived"),
        fact("F12", "The limit is 1 and the required sum bound holds for every n.", "SequenceTarget(x,n)", "derived", roles=["goal"]),
    ]
    inferences = [
        inference(1, "Positivity is preserved by the recurrence", [("F1", "recurrence")], "F2", risks=["hidden_domain_condition"]),
        inference(2, "Identify the fixed point", [("F1", "recurrence")], "F3"),
        inference(3, "Rationalize both differences from the fixed point", [("F1", "recurrence"), ("F3", "fixed_point")], "F4", risks=["nonlinear_arithmetic"]),
        inference(4, "Bound the signed multiplier pointwise", [("F2", "positivity"), ("F4", "identity")], "F5", risks=["hidden_domain_condition"]),
        inference(5, "Read sign alternation and magnitude monotonicity", [("F4", "identity"), ("F5", "pointwise_bound")], "F6"),
        inference(6, "Prove the orbit remains in [0,2]", [("F1", "recurrence"), ("F2", "positivity")], "F7"),
        inference(7, "Upgrade pointwise contraction to a uniform one on a compact invariant interval", [("F5", "pointwise_bound"), ("F7", "compact_invariant")], "F8", risks=["hidden_domain_condition", "external_theorem_dependency"]),
        inference(8, "Iterate the uniform contraction", [("F4", "identity"), ("F8", "uniform_bound")], "F9"),
        inference(9, "Apply the finite alternating-sum estimate", [("F6", "alternation"), ("F1", "initial_value")], "F10", risks=["external_theorem_dependency"]),
        inference(10, "Translate deviation sums back to x_i", [("F10", "deviation_sum")], "F11"),
        inference(11, "Combine the limit and sum conclusions", [("F9", "limit"), ("F11", "sum_bound")], "F12"),
    ]
    return {
        "problem_id": "0ldq",
        "module": "recurrences_sequences",
        "source_hash": "39ffc14e5e1bc68d07dbbc4f44a5341cd89feba8b0b59d184719160fc12bd4e2",
        "facts": facts,
        "inferences": inferences,
        "target": "F12",
        "mutation": ("I7", "F7", "compact_invariant", "F7->I7"),
        "mutation_reason": "The proof claims a uniform q<1 from pointwise rho(x)<1 without a compact invariant interval.",
    }


def spec_0le0() -> dict[str, Any]:
    zscope = "global/case_even_mass_zero"
    pscope = "global/case_even_mass_positive"
    facts = [
        fact("F1", "a is in [1/2,2/3], M=2019, and h=2^-M.", "ProblemDomain(a,M,h)", "given"),
        fact("F2", "Define finite digits d_j by the floor recurrence.", "FiniteBinaryDigits(a,d,M)", "constructed"),
        fact("F3", "(-1)^floor(2^j a)=1-2d_j.", "FloorParityDigit(a,d,j)", "derived"),
        fact("F4", "Define odd and even digit masses O,E and s=O+E.", "DigitMasses(O,E,s)", "constructed"),
        fact("F5", "O,E are constant on each half-open binary cylinder [s,s+h).", "BinaryCylinderConstancy(O,E,s,h)", "derived"),
        fact("F6", "The two finite sums equal the explicit expressions A and C.", "FiniteSumFormula(A,C,O,E,h)", "derived"),
        fact("F7", "It suffices to check the quadratic bound at a=s.", "CylinderEndpointReduction(a,s)", "derived"),
        fact("F8", "After substitution the target is equivalent to G>=0.", "ReducedInequality(G,O,E,s,h)", "derived"),
        fact("F9", "E=0.", "EvenMassZero(E)", "case_assumed", zscope, roles=["case_condition"]),
        fact("F10", "G>=0 in the E=0 case, with equality at s=2/3-h/3.", "ZeroCaseBound(G,s,h)", "derived", zscope),
        fact("F11", "If E=0 then the reduced inequality holds with the stated equality condition.", "ZeroCaseConclusion(G,s,h)", "derived"),
        fact("F12", "E>0.", "EvenMassPositive(E)", "case_assumed", pscope, roles=["case_condition"]),
        fact("F13", "The least positive even-position contribution is 2h.", "LeastEvenContribution(E,h)", "derived", pscope),
        fact("F14", "G>0 in the E>0 case.", "PositiveCaseBound(G)", "derived", pscope),
        fact("F15", "If E>0 then the reduced inequality is strict.", "PositiveCaseConclusion(G)", "derived"),
        fact("F16", "Exactly one of E=0 and E>0 holds.", "EvenMassCaseExhaustive(E)", "derived"),
        fact("F17", "The required inequality holds and equality occurs only at a=2/3-1/(3*2^2019).", "BinaryProblemTarget(a)", "derived", roles=["goal"]),
    ]
    inferences = [
        inference(1, "Read floor parity from the last finite binary digit", [("F1", "domain"), ("F2", "digits")], "F3", risks=["floor_or_ceiling"]),
        inference(2, "Finite floor digits determine the binary cylinder", [("F2", "digits"), ("F4", "digit_masses")], "F5", risks=["floor_or_ceiling"]),
        inference(3, "Evaluate odd and even finite geometric sums", [("F3", "parity"), ("F4", "digit_masses"), ("F1", "odd_length")], "F6", risks=["nonlinear_arithmetic"]),
        inference(4, "Use monotonicity of the quadratic on each cylinder", [("F1", "domain"), ("F5", "constancy"), ("F6", "sum_formula")], "F7", risks=["hidden_domain_condition"]),
        inference(5, "Algebraically reduce the endpoint inequality to G>=0", [("F6", "sum_formula"), ("F7", "endpoint")], "F8", risks=["nonlinear_arithmetic", "large_lemma_compression"]),
        inference(6, "Use the truncated upper endpoint when E=0", [("F9", "case"), ("F1", "domain"), ("F8", "reduction")], "F10", scope=zscope, risks=["floor_or_ceiling"]),
        inference(7, "Discharge the E=0 case", [("F9", "case"), ("F10", "bound")], "F11", scope=zscope, discharge=True),
        inference(8, "Identify the least positive even-position digit mass", [("F12", "case"), ("F2", "digits"), ("F1", "scale")], "F13", scope=pscope, risks=["floor_or_ceiling"]),
        inference(9, "Lower-bound G using E>=2h and d_1=1", [("F12", "case"), ("F13", "least_mass"), ("F8", "reduction"), ("F1", "domain")], "F14", scope=pscope, risks=["nonlinear_arithmetic"]),
        inference(10, "Discharge the E>0 case", [("F12", "case"), ("F14", "strict_bound")], "F15", scope=pscope, discharge=True),
        inference(11, "Split the nonnegative even digit mass", [("F4", "digit_masses")], "F16", risks=["case_exhaustiveness"]),
        inference(12, "Combine both cases and translate the equality prefix", [("F11", "zero_case"), ("F15", "positive_case"), ("F16", "exhaustiveness"), ("F7", "endpoint_reduction")], "F17", risks=["case_exhaustiveness", "floor_or_ceiling"]),
    ]
    return {
        "problem_id": "0le0",
        "module": "discrete_algebra",
        "source_hash": "ea67bcdd2fc804044b069710371bb3e2c13397af6b69532b5e33135c772208d2",
        "facts": facts,
        "inferences": inferences,
        "target": "F17",
        "scopes": [
            {"id": "global", "parent_id": None, "kind": "global"},
            {"id": zscope, "parent_id": "global", "kind": "case"},
            {"id": pscope, "parent_id": "global", "kind": "case"},
        ],
        "mutation": ("I1", "F2", "digits", "F2->I1"),
        "mutation_reason": "The proof reads floor parity as a binary digit without defining the finite floor-based digit convention.",
    }


def write_review_files(directory: Path, spec: dict[str, Any]) -> None:
    pid = spec["problem_id"]
    directory.joinpath("dag_semantic_review.md").write_text(
        f"""# {pid} DAG Semantic Review

- [ ] Every Fact is atomic enough to be consumed by a later rule.
- [ ] Every Inference represents one defensible mathematical rule application.
- [ ] All required premises and premise roles are present.
- [ ] Source order follows the reviewed proof rather than graph topology alone.
- [ ] Local case Facts do not escape their scope without an explicit discharge.
- [ ] The target statement matches the original problem.
- [ ] No edge was inferred only from shared words or adjacency.

Reviewer:
Date:
Decision: pending
Notes:
""",
        encoding="utf-8",
    )
    directory.joinpath("mutation_review.md").write_text(
        f"""# {pid} Mutation Review

Primary intervention: remove `{spec['mutation'][3]}`.

Mathematical effect: {spec['mutation_reason']}

- [ ] Exactly one primary intervention was made.
- [ ] The removed premise is genuinely necessary at the injection anchor.
- [ ] The remaining inference is a plausible but invalid proof step.
- [ ] Expected and computed First Break agree.
- [ ] Later failures are propagation, not additional injected errors.
- [ ] Independent branches remain executable.

Reviewer:
Date:
Decision: pending
Notes:
""",
        encoding="utf-8",
    )


def build_one(spec: dict[str, Any]) -> None:
    pid = spec["problem_id"]
    directory = ROOT / "pilots" / pid
    directory.mkdir(parents=True, exist_ok=True)
    facts = spec["facts"]
    rules, inferences = build_rules(facts, spec["inferences"], spec["module"])
    source = {
        "problem_source": f"HuggingFace:ShadenA/MathNet problem {pid}",
        "solution_source": "human-reviewed blind proof in algebra curriculum",
        "source_record_id": f"mathnet:{pid}",
        "source_hash": spec["source_hash"],
        "candidate_reference_solution_hash": spec["source_hash"],
        "reviewed_solution_hash": spec["source_hash"],
    }
    graph = {
        "schema_version": "proof-dag-schema-v0.4",
        "graph_kind": "reference",
        "graph_id": f"{pid}-reference-v0.1",
        "problem_id": pid,
        "target_fact_ids": [spec["target"]],
        "versions": {
            "skill_standard": "0.3",
            "dag_schema": "proof-dag-schema-v0.4",
            "fact_schema": "fact-v0.4",
            "inference_schema": "inference-v0.4",
            "scope_schema": "scope-v0.4",
            "mutation_schema": "mutation-v0.4",
            "canonicalizer": "math-expression-v1",
            "rule_registry": f"{spec['module']}-pilot-rules-v1",
            "common_tooling": "proof-dag-lean-v0.4",
            "domain_skill": "olympiad-algebra-expert-v0.1",
        },
        "source_record": source,
        "scopes": spec.get(
            "scopes", [{"id": "global", "parent_id": None, "kind": "global"}]
        ),
        "rule_schemas": rules,
        "facts": facts,
        "inferences": inferences,
        "provenance": {
            "source": "data/algebra_skill_curriculum",
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
                "notes": "No intermediate Fact has multiple producers.",
            },
        },
    }
    candidate = copy.deepcopy(graph)
    candidate["graph_kind"] = "candidate"
    candidate["graph_id"] = f"{pid}-candidate-v0.1"
    inference_id, fact_id, role, edge_id = spec["mutation"]
    anchor = next(x for x in candidate["inferences"] if x["id"] == inference_id)
    anchor["input_bindings"] = [
        x
        for x in anchor["input_bindings"]
        if not (x["fact_id"] == fact_id and x["premise_role"] == role)
    ]
    candidate["mutation"] = {
        "base_graph_id": graph["graph_id"],
        "operation": "remove_required_premise",
        "primary_site": {"type": "edge", "id": edge_id},
        "injection_anchor": {"type": "inference", "id": inference_id},
        "declared_expected_first_break": {"type": "inference", "id": inference_id},
        "before": {"fact_id": fact_id, "premise_role": role},
        "after": {"edge_removed": True, "remaining_claim": spec["mutation_reason"]},
        "graph_changed": True,
        "target_effect": "target_breaking",
        "seed": 0,
        "provenance": {
            "generator": "pilots/build_algebra_coverage_pilots.py",
            "intent": "single realistic missing-dependency error",
        },
    }
    candidate["provenance"] = {
        "source": f"controlled mutation of {graph['graph_id']}",
        "current_annotation_level": "synthetic",
        "requested_target_level": "silver_verified",
        "achieved_annotation_level": "pending",
        "promotion_profile": "algebra-candidate-mutation-v0.1",
        "reference_dag_semantics": {"method": "human", "status": "not_run"},
        "mutation_realism": {"method": "human", "status": "not_run"},
    }
    outputs = {
        "source_record.json": source,
        "reference_dag.json": graph,
        "correct_evaluation.json": evaluate_graph(graph),
        "candidate_graph.json": candidate,
        "candidate_evaluation.json": evaluate_graph(candidate),
        "mutation_check.json": check_mutation(candidate),
    }
    for filename, payload in outputs.items():
        directory.joinpath(filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    write_review_files(directory, spec)


def main() -> None:
    for spec in (spec_06og(), spec_0ldq(), spec_0le0()):
        build_one(spec)


if __name__ == "__main__":
    main()
