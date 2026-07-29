# Proof Dependency DAG v0

This repository is a small prototype for proof-diagnosis preprocessing before Lean.

It does not perform Lean verification yet. The current layer converts natural-language olympiad solutions into semantic proof units (SPUs), extracts dependency edges, checks the resulting proof-dependency DAG, and evaluates first-break localization.

## Current Pipeline

1. Split a natural-language solution into SPU nodes.
2. Extract `depends_on` edges between SPUs.
3. Validate the proof-dependency DAG for cycles, missing dependencies, closure errors, and case-scope errors.
4. Evaluate predicted first-break location and break type against gold labels.
5. Generate synthetic wrong-solution samples from correct solutions as a prototype data source.

Lean should be attached later only to selected high-risk SPUs or local subgraphs, not to full informal proofs at this stage.

## Repository Layout

- `data/imo_2015_p2_wrong_solutions(1).md`  
  Source wrong-solution set for IMO 2015 Problem 2.
- `data/imo_2015_p2_spu_dependency_gold_v0.jsonl`  
  Human-annotated SPU/dependency gold labels for 5 wrong solutions.
- `data/model_pred.jsonl`  
  Model predictions generated with the revised prompt.
- `data/raw_wrong_solutions_demo.jsonl`  
  Minimal raw-input demo for the heuristic extractor.
- `data/synthetic_wrong_solutions_v0.jsonl`  
  Generated synthetic wrong-solution dataset. It contains one wrong solution per source problem from `proof_dag_problem_dataset`.
- `data/audit/`  
  Human-audit task files for checking synthetic wrong solutions.
- `data/proof_dag_problem_dataset/`  
  Correct-solution problem dataset for SPU decomposition and synthetic wrong-solution generation.
- `scripts/eval_spu_dependency.py`  
  Main evaluator for first-break, break type, DAG sanity, dependency closure, and case scope.
- `scripts/spu_utils.py`  
  Shared DAG and SPU validation utilities.
- `scripts/validate_dataset.py`  
  Schema and consistency checker for gold/prediction JSONL files.
- `scripts/check_dependency_closure.py`  
  Checks whether invalid/unsupported dependencies are propagated downstream.
- `scripts/check_case_scope.py`  
  Checks whether case-scoped SPUs depend only on global or same-case SPUs.
- `scripts/run_spu_extractor.py`  
  Heuristic extractor demo. This is an I/O scaffold, not the final LLM extractor.
- `scripts/error-generator/`  
  Prototype synthetic wrong-solution generator.
- `scripts/audit/`  
  Audit, analysis, promotion, and repair tools for synthetic wrong-solution labels.

## Run Core Evaluation

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

Run the structural checks separately:

```powershell
python scripts\validate_dataset.py data\imo_2015_p2_spu_dependency_gold_v0.jsonl data\model_pred.jsonl
python scripts\check_dependency_closure.py data\model_pred.jsonl
python scripts\check_case_scope.py data\model_pred.jsonl
```

## Run Extractor Demo

```powershell
python scripts\run_spu_extractor.py --input-jsonl data\raw_wrong_solutions_demo.jsonl --output outputs\demo_model_pred.jsonl
```

This extractor is rule-based and should only be used to test the JSONL contract. The real extractor should be LLM-backed and then evaluated by `eval_spu_dependency.py`.

## Run Synthetic Wrong-Solution Generator

Small smoke test:

```powershell
python scripts\error-generator\generate_wrong_solutions.py --input data\proof_dag_problem_dataset\proof_dag_problems.jsonl --out outputs\generated_wrong_solutions.jsonl --num-per-problem 1 --keep-failed
```

The generator is heuristic. Its output is useful for synthetic negative samples and DPO rejected-pair scaffolding, but generated labels still need human audit before being treated as gold.

The generated v0 file is tracked at:

```text
data/synthetic_wrong_solutions_v0.jsonl
```

It was generated with `--num-per-problem 1`, so the current version has 286 synthetic wrong solutions from 286 source problems.

## Human Audit And Promotion

The audit tools live in `scripts/audit/`.

Current round-2 audit task files are tracked under:

```text
data/audit/audit_tasks_round2.jsonl
data/audit/audit_tasks_round2.csv
data/audit/audit_cards_round2.md
```

After reviewers fill the `human_review` fields, use:

```powershell
python scripts\audit\analyze_audit_results.py --input outputs\audit_tasks_reviewed.jsonl --out-json outputs\audit_summary.json --out-md outputs\audit_summary.md
python scripts\audit\promote_reviewed_samples.py --synthetic data\synthetic_wrong_solutions_v0.jsonl --reviewed outputs\audit_tasks_reviewed.jsonl --out-silver data\wrong_solutions_silver.jsonl --out-rejected data\wrong_solutions_rejected.jsonl --out-needs-revision data\wrong_solutions_needs_revision.jsonl --reviewer-id reviewer_1
```

Only `silver_verified` samples should enter the usable silver training/evaluation pool. `rejected` and `needs_revision` should be kept for failure analysis.

## Data Notes

The current problem dataset summary:

- 286 usable records.
- Sources: IMO 156, CMO 27, TST 103.
- Topics: geometry 106, algebra 93, number theory 66, combinatorics 21.
- 168 records are marked with formula-corruption issues and should be filtered or audited before serious experiments.

## Current Status

The repository now has four runnable layers:

1. A 5-sample manually checked SPU/dependency benchmark.
2. DAG validation and first-break evaluation.
3. A prototype synthetic wrong-solution generator.
4. A frozen olympiad-algebra expert Skill with a statements-only 100-problem
   proof-layer scale pilot.

The scale pilot currently has 91 schema-valid model predictions and 9 pending
retries after the model service reported a usage limit. This is a partial
engineering result, not a proof-accuracy result and not a completed 100-problem
validation. References remain sealed until all 100 predictions are frozen.

See:

```text
outputs/algebra_scale_pilot_100_v0.1/PROTOCOL.md
outputs/algebra_scale_pilot_100_v0.1/STATUS.md
outputs/algebra_scale_pilot_100_v0.1/MODEL_RUN_PARTIAL_REPORT.md
```

After the remaining predictions are complete, the preselected 30-problem
double-review audit is the next gate. Only audited proof-layer results should
be used to select the 12 downstream Proof DAG cases and 3 Lean-grounding cases.
