# 0gif Reference DAG Pilot

This directory contains the first `proof-dag-schema-v0.4` Reference DAG for
the functional-equation calibration problem `0gif`.

## Current Scope

- Natural-language proof: human-reviewed and passed.
- Static Reference DAG: generated.
- Schema, scope, acyclicity, and target derivability: automatically checked.
- DAG semantic faithfulness: human-reviewed and passed.
- Candidate mutation, First Break, and mutation realism: passed.
- Lean mapping coverage and pinned `lake build`: automatically passed.
- Lean translation faithfulness: human-reviewed and passed.
- Independent promotion decision: `silver_verified`.

The graph uses only the `global` scope because every proof statement is
universally quantified. No local case assumption is introduced or exported.

The proof has one necessity route and one sufficiency branch. It does not
claim alternative producers for any intermediate Fact.

## Main Target

`F23`: the solutions are exactly \(f(x)=c/x\) for constants \(c>0\).

## Files

- `problem.md`: preserved statement and reviewed proof.
- `source_record.json`: source and proof hashes.
- `proof_review.json`: local named human proof-review record.
- `reference_dag.json`: static Fact-Inference graph.
- `validation_report.json`: automatic schema and structural validation.
- `correct_evaluation.json`: dynamic derivability evaluation.
- `candidate_graph.json`: one missing-premise Candidate Graph.
- `candidate_validation_report.json`: Candidate structural validation.
- `candidate_evaluation.json`: First Break and propagation evaluation.
- `mutation_check.json`: unified single-error and First Break check.
- `mutation_review.md`: human realism and single-error review checklist.
- `dag_semantic_review.md`: human review checklist for graph faithfulness.
- `verification_status.json`: independent component statuses.
- `promotion_record.json`: independent level decision derived from all checks.
- `artifact_manifest.json`, `VERSION`, and `tooling_versions.json`: release metadata.
- `checksums.sha256` and `zip_integrity_report.txt`: generated release checks.
- `formal_mapping.json`: complete `I1-I18` to Lean declaration mapping.
- `lean_translation_review.md`: human semantic-faithfulness checklist.
- `ProofDag0gif/Basic.lean`: compiled end-to-end Lean formalization.
- `verification_report.json`: unified automatic artifact check.
- `build_reference_dag.py`: deterministic graph builder.
- `REPRODUCE.md`: commands to rebuild and check the artifact.
