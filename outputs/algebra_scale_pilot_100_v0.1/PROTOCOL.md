# Algebra Scale Pilot 100 v0.1

## Objective

Test whether frozen `olympiad-algebra-expert-v0.2` can process a larger,
previously unreviewed algebra batch without changing the Skill.

This pilot tests the proof layer first. It does not claim that 100 complete
Proof DAGs or Lean files have been produced.

## Frozen Inputs

- Source: `proof_750_non_geometry_sample_v4(1).csv`
- Skill: `olympiad-algebra-expert-v0.2`
- Seed: `20260729`
- Sample size: 100
- Excluded: every old calibration and heldout problem and normalized hash
- Model input: `statements_only.jsonl`
- References remain sealed in the original source until predictions are frozen

The 100 records are distributed as follows:

| Source bucket | Count |
| --- | ---: |
| Functional equations | 24 |
| Inequalities | 24 |
| Polynomials | 18 |
| Recurrences and sequences | 17 |
| Complex algebra | 9 |
| Discrete algebra | 8 |

These are source buckets used for stratification, not trusted gold routes.

## Model Output

For every record, run the frozen Skill and fill one row of
`predictions_template.jsonl`.

Required output:

1. reviewed primary and secondary routing candidate;
2. candidate answer or theorem;
3. proof, or an explicit unresolved gap;
4. exceptional and equality cases;
5. risk flags;
6. ordered SPU proposal;
7. component-level status;
8. DAG/Lean handoff readiness.

The model must not open the source solution during generation.

After all 100 predictions are complete:

1. validate the file with `validate_algebra_scale_predictions.py`;
2. freeze it and record SHA256;
3. only then open references for the 30 audit records.

## Human Audit

Thirty records are preselected: five per source bucket. Two reviewers fill
`human_audit_30_reviewer_a.jsonl` and
`human_audit_30_reviewer_b.jsonl` independently.

Review dimensions:

- routing by actual proof mechanism;
- mathematical correctness and completeness;
- reference agreement or a valid alternative proof;
- SPU granularity;
- risk-flag coverage;
- severe false positives, especially a wrong proof marked passed.

Disagreements must be adjudicated separately; do not silently overwrite one
reviewer's decision.

## Predeclared Pilot Gates

These are pilot targets, not claims already achieved:

- prediction completion: at least 98/100;
- human-reviewed routing correctness: at least 90%;
- human-reviewed proof acceptance: at least 85%;
- severe false-positive rate: at most 5%;
- SPU acceptance: at least 90%;
- reviewer agreement: Cohen's kappa at least 0.80 where defined;
- zero solution leakage before prediction freeze.

## Downstream Sampling

Only after proof audit:

- choose 12 passed records, ideally two per reviewed primary module, for
  Reference/Candidate DAG construction and First Break evaluation;
- choose 3 of those records for selected Lean grounding, including at least one
  non-functional problem.

## Interpretation

Passing this pilot permits expansion to 500 problems. It does not itself justify
the claim that the system has been validated on 20,000 problems.
