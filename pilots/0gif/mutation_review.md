# 0gif Controlled Mutation Review

## Status

- Reference graph: `0gif-reference-v0.1`
- Candidate graph: `0gif-candidate-missing-bound-v0.1`
- Primary intervention: remove edge `F13 -> I9`
- Mutation type: `remove_required_premise`
- Expected First Break: `I9`
- Automatic mutation and First Break checks: passed
- Human mutation-realism review: passed

## Mathematical Change

In the reviewed proof, `I9` uses all three facts:

1. \(d_n\ge0\);
2. \(d_n\le d_{n+1}\);
3. the partial sums \(\sum_{j=0}^{N-1}d_{2j}\) are bounded above by \(x_0\).

Together these imply \(d_n=0\) for every \(n\). The Candidate Graph removes
the third premise but retains the same conclusion. The resulting claim is
false: the constant sequence \(d_n=1\) is nonnegative and nondecreasing but
does not vanish.

## Human Checks

- [x] The Reference DAG was valid before mutation.
- [x] Exactly one primary graph edit occurred.
- [x] The removed premise `F13` is mathematically required by `I9`.
- [x] The remaining premises do not imply `F14`; \(d_n=1\) is a counterexample.
- [x] The error is plausible as an omitted boundedness/positivity-of-orbit
      argument rather than a revealing template.
- [x] `I9` is the first intrinsically invalid Inference by `source_order`.
- [x] `I10`-`I14` are invalid only through unsupported inputs.
- [x] Independent sufficiency inferences `I15`-`I17` remain executable.
- [x] The final target `F23` becomes underivable because necessity is broken.
- [x] No second mathematical error was injected.

## Sign-Off

- Reviewer: Ruan Haochen (Eddie)
- Date: 2026-07-28
- Decision: `passed`
- Required corrections: none
