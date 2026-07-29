# Algebra Expert v0.2 Post-Freeze Heldout Report

## Boundary

This report evaluates the frozen `olympiad-algebra-expert-v0.2`. Results are
stored outside the Skill and do not modify the tagged release.

The original `heldout_reviewed_v0.2.jsonl` contained only `not_run` placeholders
and is not treated as prior test evidence.

## Input Gate

- Total heldout records: 21
- Clean statements: 18
- Corrupted or partially corrupted statements: 3
- Records whose references were exposed before prediction freeze: 3
- Records eligible for a later blind-proof run: 16

The statements-only snapshot removes `solution`, `final_answer`, and previous
review status fields. Its SHA256 is:

`5a89900ad2729c95e5e29ff3e4d7171de60f7a2e11e95e43bdd1b6d700143e17`

## Routing

All 21 statements received a frozen primary route, secondary routes, confidence,
and risk flags. The prediction agreed with the source module label on 15/21
records.

This is not a 71.4% routing accuracy. The source labels are heuristic and six
disagreements expose genuine label problems:

- `03te`: complex-valued inequality, primary mechanism is inequalities.
- `0get`: sharp inequality, not complex algebra.
- `047w`: cyclic linear recurrences, not complex algebra.
- `047t`: polynomial composition and degree divisibility.
- `0g45`: polynomial identity and degree analysis.
- `04bw`: finite digit/integrality problem, not inequalities.

## Proof Forward Test

Five clean, unexposed, tractable representatives were selected before opening
their references.

| ID | Module | Result | Comparison |
| --- | --- | --- | --- |
| `00fr` | discrete algebra | passed | Answer 70 and residue-class count agree. |
| `06r0` | functional equations | blocked | Shared-fiber structure found, but the hard equivalence-class step was not closed. |
| `0663` | inequalities | passed | Jensen proof and equality case agree. |
| `04bk` | polynomials | passed; reference defect found | Candidate gives the equivalent quadratic `x^2-a*x+1=0`; the supplied reference miscomputes a discriminant. |
| `09vy` | recurrences | passed | Invariant interval, period three, and denominator exclusions agree. |

Observed candidate pass rate: 4/5. This is a small, deliberately selected sample,
not an estimate of performance on the full heldout set.

`03te` was audited successfully after reference exposure and is excluded from
the metric.

## What This Establishes

- The frozen Skill can route by proof mechanism instead of trusting noisy
  dataset labels.
- It produced four correct candidate proofs across four modules.
- It reported a genuine unresolved gap instead of inventing a proof.
- It detected a mathematical error in a supplied reference solution.

## What This Does Not Establish

- It does not validate all 21 heldout proofs.
- It does not test heldout DAG construction, mutation, First Break, or Lean.
- It does not establish random-sample accuracy or 20,000-problem scalability.
- It provides no new evidence for a clean, unexposed complex-algebra heldout
  proof because the available complex candidates were already exposed or
  misrouted.

## Next Version Gate

Keep v0.2 frozen. For v0.3, first repair the heldout split and encoding, then run
a predeclared stratified sample with at least one clean problem per true proof
module. Only after proof predictions are frozen should references be opened.
