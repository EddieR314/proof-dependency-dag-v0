# Reproduce the 0gif Reference DAG

Run from the repository root:

```powershell
python pilots\0gif\build_reference_dag.py
python skills\proof-dag-lean\scripts\validate_dag.py `
  --graph pilots\0gif\reference_dag.json `
  --output pilots\0gif\validation_report.json
python skills\proof-dag-lean\scripts\evaluate_dag.py `
  --graph pilots\0gif\reference_dag.json `
  --output pilots\0gif\correct_evaluation.json
python pilots\0gif\build_candidate_mutation.py
python skills\proof-dag-lean\scripts\validate_dag.py `
  --graph pilots\0gif\candidate_graph.json `
  --output pilots\0gif\candidate_validation_report.json
python skills\proof-dag-lean\scripts\evaluate_dag.py `
  --graph pilots\0gif\candidate_graph.json `
  --output pilots\0gif\candidate_evaluation.json
python skills\proof-dag-lean\scripts\check_artifact.py `
  --graph pilots\0gif\reference_dag.json `
  --candidate-graph pilots\0gif\candidate_graph.json `
  --formal-mapping pilots\0gif\formal_mapping.json `
  --project pilots\0gif `
  --run-build `
  --output pilots\0gif\verification_report.json
```

Expected structural result:

- schema errors: `0`
- semantic errors: `0`
- target `F23`: derivable
- First Break: none

Expected Candidate result:

- candidate schema and structure: valid
- computed First Break: `I9`
- declared/computed First Break: match
- target `F23`: underivable
- independent sufficiency branch `I15`-`I17`: executable
- Lean declarations mapped: `18/18`
- pinned `lake build`: passed

These checks do not establish mathematical or DAG-translation faithfulness;
the latter remains a separate human review in `lean_translation_review.md`.
