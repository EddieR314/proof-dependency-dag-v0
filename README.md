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
- `scripts/validate_dataset.py`  
  Schema and consistency validator for SPU JSONL files.
- `scripts/check_dependency_closure.py`  
  Checks whether unsupported/invalid dependencies propagate to downstream SPUs.
- `scripts/check_case_scope.py`  
  Checks basic case-scope consistency and cross-case dependency mistakes.
- `scripts/run_spu_extractor.py`  
  Local heuristic prototype for converting raw wrong solutions into model-prediction JSONL.

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
closure_ok_rate = 1.0
case_scope_ok_rate = 1.0
missing_predictions = 0
```

Additional checks:

```bash
python3 scripts/validate_dataset.py data/imo_2015_p2_spu_dependency_gold_v0.jsonl data/model_pred.jsonl
python3 scripts/check_dependency_closure.py data/model_pred.jsonl
python3 scripts/check_case_scope.py data/model_pred.jsonl
```

Run the local extractor prototype:

```bash
mkdir -p outputs
python3 scripts/run_spu_extractor.py \
  --input-jsonl data/raw_wrong_solutions_demo.jsonl \
  --output outputs/demo_model_pred.jsonl

python3 scripts/validate_dataset.py outputs/demo_model_pred.jsonl
python3 scripts/check_dependency_closure.py outputs/demo_model_pred.jsonl
```

The extractor is intentionally heuristic. It exists to lock the input/output contract for `model_pred.jsonl`; production extraction should replace the internals with an LLM-backed SPU parser.

## Current Status

This is a 5-sample sanity check on one problem. It shows that the SPU/dependency intermediate representation and evaluator can run end-to-end, but it does not establish generalization.

Next steps:

1. Test the same prompt on new non-geometry problems.
2. Record model failures as DPO chosen/rejected pairs.
3. Replace the heuristic extractor with an LLM-backed SPU parser.
4. Add rubric-impact mapping from bad SPUs to score changes.
5. Connect high-risk SPUs to local Lean checks.
