# 00q2 Proof DAG Pilot

This pilot encodes the reviewed polynomial proof for problem `00q2` using
`proof-dag-schema-v0.4`.

## Contents

- `problem.md`: problem statement and reviewed proof route.
- `source_record.json`: source and review provenance.
- `reference_dag.json`: correct Fact-Inference DAG.
- `candidate_graph.json`: one controlled missing-premise mutation.
- `correct_evaluation.json`: reference derivability and scope evaluation.
- `candidate_evaluation.json`: mutation propagation and First Break result.
- `mutation_check.json`: single-intervention and First Break check.
- `dag_semantic_review.md`: human review form for DAG semantic faithfulness.
- `mutation_review.md`: human review form for mutation realism.
- `verification_status.json`: component-level verification state.

## Current Result

- Reference DAG schema, derivability, and scope checks: passed.
- Candidate DAG schema and mutation checks: passed.
- Expected and computed First Break: `I5`.
- Human DAG semantic review: pending.
- Human mutation realism review: pending.
- Lean: intentionally deferred.

The artifact must not be promoted to `silver_verified` until both pending human
reviews are signed.
