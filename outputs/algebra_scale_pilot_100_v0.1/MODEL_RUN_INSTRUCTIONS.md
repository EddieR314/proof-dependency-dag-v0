# Model Run Instructions

Process each line of `statements_only.jsonl` independently with the frozen
`olympiad-algebra-expert-v0.2` Skill.

Do not read the original CSV, any `solution` field, or any previous answer for
the same problem.

Return exactly one JSON object per input problem with these fields:

```json
{
  "problem_id": "...",
  "pilot_id": "...",
  "prediction_status": "completed",
  "routing": {
    "primary_module": "functional_equations | inequalities | polynomials | recurrences_sequences | complex_algebra | discrete_algebra",
    "secondary_modules": [],
    "confidence": "low | medium | high"
  },
  "candidate_answer": "...",
  "proof_result": "passed | blocked | failed",
  "proof": "...",
  "unresolved_gap": "",
  "risk_flags": [],
  "spu_outline": [],
  "dag_lean_handoff_readiness": "blocked | candidate | reviewed",
  "component_status": {
    "proof_review": "not_run | passed | failed | partial",
    "dag": "not_run | candidate | validated",
    "formal_mapping": "not_run | candidate | validated",
    "lean_build": "not_run | passed | failed"
  }
}
```

Rules:

- Use `blocked` when a proof cannot be closed.
- Never label a proof `passed` merely because its final answer looks plausible.
- Do not claim DAG, formal mapping, or Lean success unless those artifacts were
  actually built and checked.
- Preserve domain conditions, quantifiers, exceptional cases, and equality
  cases.
- SPUs are ordered single-output reasoning actions, not sentence fragments.
