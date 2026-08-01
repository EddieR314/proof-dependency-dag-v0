---
name: dag-suitability-screening
description: Screen olympiad-algebra problem-and-proof records for suitability for Fact-Inference Proof DAG construction across functional equations, inequalities, polynomials, recurrences and sequences, complex algebra, and discrete algebra. Use for algebra-only batch triage before expensive DAG annotation, stratified human audit, or selecting representative algebra DAG pilots. This skill does not certify the mathematics, build the final DAG, or claim Lean verification.
---

# DAG Suitability Screening

Use this skill before `$proof-dag-lean` when an olympiad-algebra problem bank must be reduced to records worth annotating. Do not use it to screen geometry, combinatorics, or number theory.

## Non-negotiable distinctions

- `has_solution` is metadata, not evidence that the proof is complete or correct.
- DAG suitability is separate from Lean formalization cost.
- A linear proof can be suitable. Branching and alternative paths add structural richness but are not required.
- Model screening produces candidates, never human gold.
- Do not repair or silently complete the proof while screening it.

## Workflow

1. Run `scripts/prepare_screening_batch.py` on the source CSV or JSONL. It retains only records whose source bucket is algebra and records a candidate six-module route.
2. Apply the rubric in `references/suitability-rubric.md` to each prepared record.
3. Return exactly one JSON object per input record using `references/screening-schema.json`.
4. Run `scripts/validate_screening_results.py` before using the output.
5. Run `scripts/make_stratified_audit.py` to create a human-review packet.
6. Only records confirmed by a reviewer may receive `human_review_status=confirmed` or `overridden`.
7. Send confirmed `suitable` records to `$proof-dag-lean` for proof review, Reference DAG construction, mutation, First Break evaluation, and optional Lean work.

## Decision rule

Use `unsuitable` when any hard gate fails:

- statement is unreadable or materially incomplete;
- proof is absent, answer-only, corrupted, or truncated;
- essential information is only available in a missing image or external reference;
- no defensible atomic propositions and rule applications can be recovered without inventing mathematics.

Use `borderline` when the record is potentially usable after a bounded human repair, such as resolving a moderate jump, scope ambiguity, or incomplete reference.

Use `suitable` only when the source proof is readable, substantially complete, and decomposable into traceable Fact and Inference candidates. This is still not a correctness certificate.

## Output discipline

- Preserve `problem_id` exactly.
- Treat `algebra_module` as a reviewed proof-mechanism route, not a copy of the source domain label.
- Use only enumerated reason and repair codes from the rubric.
- Score every dimension independently; do not infer the decision from a raw sum alone.
- Put uncertainty in `confidence` and `notes`; do not hide it by upgrading the decision.
- Leave `human_review_status` as `not_reviewed` in all model-produced output.

## Batch expansion policy

Calibrate on known reviewed pilots and known failure cases first. For expansion, audit every `borderline`, all low-confidence outputs, all hard-gate rejections, and a stratified sample of high-confidence `suitable` and `unsuitable` outputs. Track false accepts and false rejects by reason code and problem family before increasing scale.
