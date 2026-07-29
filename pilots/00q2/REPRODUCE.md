# Reproduce 00q2

Run from the repository root:

```powershell
python pilots\00q2\build_reference_dag.py
python skills\proof-dag-lean\scripts\validate_dag.py --graph pilots\00q2\reference_dag.json --output pilots\00q2\validation_report.json
python skills\proof-dag-lean\scripts\evaluate_dag.py --graph pilots\00q2\reference_dag.json --output pilots\00q2\correct_evaluation.json
python pilots\00q2\build_candidate_mutation.py
python skills\proof-dag-lean\scripts\validate_dag.py --graph pilots\00q2\candidate_graph.json --output pilots\00q2\candidate_validation_report.json
python skills\proof-dag-lean\scripts\evaluate_dag.py --graph pilots\00q2\candidate_graph.json --output pilots\00q2\candidate_evaluation.json
```

Expected result:

- both graphs pass schema validation;
- the reference derives target `F28`;
- the candidate does not derive `F28`;
- the candidate's expected and computed First Break are both `I5`;
- the sufficiency branch remains executable.
