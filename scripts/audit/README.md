# Wrong-Solution Audit Workflow

This repository contains synthetic olympiad wrong-solution samples. The samples
are useful, but they are not human gold labels until reviewers verify the first
break, break type, and single-error assumptions.

## Workflow

1. Generate synthetic wrong solutions.
2. Run the unified evaluator.
3. Generate a stratified human-audit sample.
4. Human reviewers fill `audit_tasks.csv` or `audit_tasks_reviewed.jsonl`.
5. Analyze audit results.
6. Promote reviewed samples into silver, rejected, or needs-revision splits.
7. Use only `silver_verified` or `human_gold` samples for training/evaluation.

## Generate Audit Tasks

```bash
python3 make_audit_sample.py \
  --input synthetic_wrong_solutions_v0.jsonl \
  --out-jsonl audit_tasks.jsonl \
  --out-csv audit_tasks.csv \
  --out-md audit_cards.md \
  --per-topic 5 \
  --per-error-type 3 \
  --include-warnings \
  --seed 42
```

For the next audit round after the first quality review, focus the sample on the
known weak spots:

```bash
python3 make_audit_sample.py \
  --input synthetic_wrong_solutions_v0.jsonl \
  --out-jsonl audit_tasks_round2.jsonl \
  --out-csv audit_tasks_round2.csv \
  --out-md audit_cards_round2.md \
  --per-topic 5 \
  --per-error-type 3 \
  --include-warnings \
  --focus-error-type circular_reasoning \
  --focus-topic geometry \
  --focus-topic number_theory \
  --include-long-proofs \
  --long-proof-min-spus 30 \
  --focus-quality-warnings \
  --focus-first-break-spu-type Final \
  --focus-first-break-spu-type Remark \
  --per-focus 10 \
  --seed 43
```

The sampler reads both current and older JSONL shapes. For example, it accepts
`error_type` either as a top-level field or as `injected_error.error_type`, and
it accepts `generator_name` either as a top-level field or as
`metadata.generator`.

Each audit task includes:

- generated labels and evaluator results
- normalized wrong-solution steps with `spu_id`, `text`, `type`, and `depends_on`
- empty `human_review` fields for reviewer labels
- a markdown review card in `audit_cards.md`

Allowed review values:

```json
{
  "first_break_valid": ["yes", "no", "unclear"],
  "break_type_valid": ["yes", "no", "unclear"],
  "single_error_valid": ["yes", "no", "unclear"],
  "usable_as_gold": ["yes", "no", "revise"]
}
```

## Analyze Reviewed Tasks

```bash
python3 analyze_audit_results.py \
  --input audit_tasks_reviewed.jsonl \
  --out-json audit_summary.json \
  --out-md audit_summary.md
```

The analyzer accepts either reviewed JSONL or the CSV emitted by the sampler. It
reports review counts, validity rates, average quality scores,
accuracy by topic/error type/generator, common corrected break types, and common
failure modes.

## Promote Reviewed Samples

```bash
python3 promote_reviewed_samples.py \
  --synthetic synthetic_wrong_solutions_v0.jsonl \
  --reviewed audit_tasks_reviewed.jsonl \
  --out-silver wrong_solutions_silver.jsonl \
  --out-rejected wrong_solutions_rejected.jsonl \
  --out-needs-revision wrong_solutions_needs_revision.jsonl \
  --reviewer-id reviewer_1
```

Promotion rules:

- `silver_verified`: first break, break type, single-error validity, and
  `usable_as_gold` are all `yes`
- `needs_revision`: `usable_as_gold` is `revise`
- `rejected`: `usable_as_gold` is `no`, or `single_error_valid` is `no`

If a reviewer supplies `correct_first_break_spu_id` or `correct_break_type`, the
promoter preserves generated labels and adds `human_corrected_first_break`
instead of silently overwriting generated labels.

## Repair Needs-Revision Samples

```bash
python3 repair_needs_revision.py \
  --input wrong_solutions_needs_revision.jsonl \
  --out wrong_solutions_needs_revision_repaired.jsonl \
  --out-manual wrong_solutions_needs_manual_review.jsonl
```

The repair pass cleans OCR residue, drops commentary/source-note SPUs, rebuilds
`wrong_solution`, `wrong_solution_steps`, and dependency edges, and preserves
`sample_id`, `injected_error`, and `human_review`. If the repair removes the
generated first-break SPU, the sample is marked `needs_manual_review`.
