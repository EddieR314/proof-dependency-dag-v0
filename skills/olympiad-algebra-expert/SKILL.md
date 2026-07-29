---
name: olympiad-algebra-expert
description: Classify, solve, audit, and normalize olympiad algebra proofs across functional equations, inequalities, polynomials, recurrences, complex numbers, and discrete algebra, then hand reviewed proofs to proof-dag-lean for v0.4 DAG construction and Lean mapping. Use for competition algebra problems that require a rigorous proof, hidden-assumption audit, topic-specific strategy selection, controlled error design, or preparation for formalization. Route iteration-driven functional problems to algebra-iteration-proof. Do not use for geometry or primarily number-theoretic/combinatorial proofs merely containing algebraic manipulation.
---

# Olympiad Algebra Expert

Use this as the algebra routing and proof-audit layer. Use `proof-dag-lean` only
after the mathematical proof is reviewed.

## References

Read:

- `references/topic-routing.md` to choose the primary and secondary modules.
- `references/proof-audit.md` before accepting a proof.
- `references/capability-matrix.md` before claiming a module is validated.
- `references/curriculum-protocol.md` when selecting or reviewing training
  problems.
- `references/pattern-library-v0.1.md` for proof patterns already observed in
  blind calibration.
- `references/problem-review-schema.json` when recording per-problem evidence.
- `references/evidence-ledger-v0.2.md` before describing a module as DAG- or
  Lean-validated.

For iteration-driven functional equations or inequalities, invoke
`algebra-iteration-proof` and read its iteration patterns.

## Workflow

1. Preserve the source.
   - Record the exact statement, domain, quantifiers, source, and candidate
     reference solution.
   - Do not treat an official-looking answer as a reviewed proof.
2. Route the problem.
   - Assign one primary module and any secondary modules.
   - Reject the algebra route when the proof is fundamentally geometric,
     number-theoretic, or combinatorial.
3. Normalize the proof obligations.
   - Separate definitions, assumptions, constructions, intermediate claims,
     equality cases, and the goal.
   - List every theorem application and its required premises.
4. Solve and audit.
   - Prove necessity and sufficiency separately where applicable.
   - Check domains, signs, denominators, equality conditions, endpoints, and
     exceptional cases.
   - Record unresolved gaps instead of silently completing them.
5. Propose SPUs.
   - Produce an ordered list of single-output reasoning actions.
   - Keep reverse inequalities, case merges, induction steps, and candidate
     verification separate.
6. Hand off to the common layer.
   - Send the reviewed proof, proposed SPUs, risk flags, and source spans to
     `proof-dag-lean`.
   - Target `proof-dag-schema-v0.4`.
   - Keep dynamic evaluation outside static nodes and all formal links in
     `formal_mapping.json`.
7. Report evidence.
   - Return per-component automatic and human statuses.
   - Do not use a release label as a substitute for component evidence.

## Output Contract

Start with this machine-readable JSON object, using the exact enum strings:

```json
{
  "routing": {
    "primary_module": "functional_equations | inequalities | polynomials | recurrences_sequences | complex_algebra | discrete_algebra",
    "secondary_modules": [],
    "confidence": "low | medium | high"
  },
  "dag_lean_handoff_readiness": "blocked | candidate | reviewed",
  "component_status": {
    "proof_review": "not_run | passed | failed | partial",
    "dag": "not_run | candidate | validated",
    "formal_mapping": "not_run | candidate | validated",
    "lean_build": "not_run | passed | failed"
  }
}
```

Do not invent additional primary-module or status labels. After the JSON,
return:

Status invariants:

- `reviewed` is allowed only when `proof_review=passed`, `dag=validated`,
  `formal_mapping=validated`, and `lean_build=passed`.
- Use `candidate` when the mathematical proof has passed review but any DAG,
  mapping, or Lean check is still incomplete.
- Use `blocked` when the proof has a known gap or a required downstream
  artifact cannot yet be constructed.
- Never infer a release or promotion label from this readiness field.

1. topic routing with confidence;
2. candidate answer or theorem;
3. reviewed proof or explicit unresolved gaps;
4. equality and exceptional cases;
5. ordered SPU proposal;
6. high-risk claims and likely student-error sites;
7. recommended Lean coverage;
8. DAG/Lean handoff readiness: `blocked`, `candidate`, or `reviewed`.

## Release Boundary

Version `0.2` is frozen against `proof-skill-standard-v0.3` and
`proof-dag-schema-v0.4`.

- `0gif` is the sealed functional-iteration exemplar.
- `00q2`, `06og`, `0ldq`, and `0le0` have reviewed proofs, validated
  Reference/Candidate DAGs, reviewed mutations, and verified First Breaks.
- `0chi` supplies the non-functional Lean exemplar. Its high-risk and
  end-to-end mapping covers `I1`, `I5`, and `I6`; `I2-I4` are intentionally
  recorded as unmapped rather than implied to be formally covered.
- Heldout results belong to a separate post-freeze report and must not be used
  to revise version `0.2`.
