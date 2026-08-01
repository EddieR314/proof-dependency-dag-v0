# Algebra DAG Suitability Screening v0.1

## Frozen Result

- Candidate algebra problems: 250
- Suitable: 186
- Borderline: 44
- Unsuitable: 20
- Screening total check: 250
- Freeze date: 2026-08-01

## Review Evidence

- A 35-record calibration batch received Agent screening and human review.
- The remaining 215 records received Agent screening.
- A 108-record stratified human audit covered all 51 initial borderline records,
  all 13 initial unsuitable records, and 44 sampled suitable records.
- All 108 audited decisions were confirmed by the reviewer.
- All 59 borderline records then received a second pass: 13 were selected for
  bounded cleanup, 44 remained borderline, and 2 were downgraded.
- The 13 cleaned proofs were subsequently confirmed complete and mathematically
  correct by Ruan Haochen (Eddie).

## Scope Boundary

This release freezes DAG-suitability screening only. A `suitable` decision means
that the natural-language proof is an appropriate candidate for later atomic
Fact-Inference decomposition. It does not mean that a Proof DAG, controlled
mutation, First Break annotation, or Lean translation has already been built or
verified.

## Reproducibility

The archive includes the screening Skill, prepared candidate data, screening
outputs, review records, validators, and the bounded-cleanup utilities. The
machine-generated `MANIFEST.json` records SHA-256 hashes for every archived file.

