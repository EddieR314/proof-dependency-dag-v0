# 00q2 DAG Semantic Review

## Artifact

- Problem ID: `00q2`
- Reference graph: `00q2-reference-v0.1`
- Primary module: `polynomials`
- Automatic schema/derivability/scope checks: passed
- Human decision: pending

## Facts and SPUs

- [ ] `F1-F2` faithfully encode the positive-integer domain and polynomial
      definitions.
- [ ] `F3-F19` represent the necessity branch without treating its local
      divisibility or `n>1` assumptions as global Facts.
- [ ] `F6` records both nonzero extreme components of `f_n` and the condition
      `n>1`.
- [ ] `I5-I6` use the integral-domain nonzero-product fact and uniqueness of
      the extreme total degrees; they do not assume that `h` is homogeneous.
- [ ] `I7-I11` correctly derive `l=5n-2`, `u=3n`, and then `n<=1`.
- [ ] `I13` discharges only the `n>1` contradiction into the necessity scope.
- [ ] `I15` discharges the divisibility assumption as an implication rather
      than promoting a local equality without its premise.
- [ ] `F20-F27` form an independent `n=1` sufficiency branch.
- [ ] `I18-I21` faithfully encode the fifth-power identity, the quadratic
      difference identity, factorization, and divisibility.
- [ ] `I23` consumes both implications before producing the exact target.

## Scope

- [ ] `global/necessity/case_gt_one` can see global and necessity Facts.
- [ ] No Fact from the contradiction subcase is consumed by a parent or
      sibling scope without an explicit discharge rule.
- [ ] The sufficiency branch cannot consume necessity-only Facts.

## Sign-Off

- Reviewer:
- Date:
- Decision: `pending`
- Notes:
