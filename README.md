# Proof Dependency DAG v0

This repository contains a small prototype for Lean-preprocessing proof diagnosis.

The current pipeline is:

1. Split a natural-language wrong proof into semantic proof units (SPUs).
2. Extract `depends_on` edges between SPUs.
3. Treat the SPUs and dependencies as a proof-dependency DAG.
4. Evaluate first-break localization and error-type prediction against human gold labels.

This is not Lean verification yet. It is the structural layer before Lean: SPU nodes, dependency edges, case scope, first-break labels, and a simple evaluator.

## Files

- `data/imo_2015_p2_wrong_solutions(1).md`  
  Source wrong-solution set for IMO 2015 Problem 2.
- `data/imo_2015_p2_spu_dependency_gold_v0.jsonl`  
  Human-annotated structural gold labels.
- `data/model_pred.jsonl`  
  Model predictions generated with the revised prompt.
- `scripts/eval_spu_dependency.py`  
  Evaluator for first-break, break type, DAG sanity, and dependency sanity.

## Run

From the repository root:

```powershell
python scripts\eval_spu_dependency.py --gold data\imo_2015_p2_spu_dependency_gold_v0.jsonl --pred data\model_pred.jsonl
```

Expected v0 result:

```text
first_break_accuracy = 1.0
break_type_accuracy = 1.0
dag_ok_rate = 1.0
missing_predictions = 0
```

## Current Status

This is a 5-sample sanity check on one problem. It shows that the SPU/dependency intermediate representation and evaluator can run end-to-end, but it does not establish generalization.

Next steps:

1. Test the same prompt on new non-geometry problems.
2. Record model failures as DPO chosen/rejected pairs.
3. Add case-scope and dependency-closure checks.
4. Connect high-risk SPUs to local Lean checks.
