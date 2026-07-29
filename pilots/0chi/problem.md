# 0chi: Proof DAG v0.3 + Lean Pilot

This pilot implements the team's existing Node, critical-node, and
error-injection specifications as an executable Fact-Inference graph. The v0.3
changes are implementation completion, not a replacement theory.

## Source

- Dataset: `proof_750_non_geometry_sample_v4(1).csv`
- Problem ID: `0chi`
- Competition: 74th Romanian Mathematical Olympiad
- Domain: algebra / complex numbers
- Upstream source: `HuggingFace:ShadenA/MathNet`
- Source record: `ShadenA/MathNet:all:train:1296`

## Statement

Let `a`, `b`, and `c` be nonzero complex numbers with the same modulus. Assume
that

`A = a + b + c` and `B = a * b * c`

are real. Prove that, for every natural number `n`,

`C_n = a^n + b^n + c^n`

is real.

## Correct Proof Plan

Define the second elementary symmetric sum

`S = a*b + b*c + c*a`.

Equal moduli and nonzeroness imply that the conjugates can be written with a
common real norm-square factor. Conjugating the identity for `A`, and using that
`A` and `B` are real, then shows that `S` is real.

The roots `a`, `b`, and `c` satisfy

`x^3 = A*x^2 - S*x + B`.

Summing this identity after multiplication by `a^n`, `b^n`, and `c^n` gives

`C_(n+3) = A*C_(n+2) - S*C_(n+1) + B*C_n`.

The initial values `C_0`, `C_1`, and `C_2` are real, so strong induction using
this recurrence proves that every `C_n` is real.

## Controlled Mutation

Replace the recurrence's final term `+ B*C_n` with `- B*C_n`. No other node or
edge changes. The recurrence inference `I5` is therefore the expected first
break. After state recomputation, `I6` is also dynamically invalid because its
input `F13` is unsupported; this is propagation from the one injected error,
not a second mutation.

## Verified Results

- The correct DAG is acyclic and derives `F14`.
- Rule Schema premise roles, variable bindings, Fact states, and scope states
  pass the v0.3 validator.
- Blocking recurrence inference `I5` makes `F14` underivable, so `I5` is critical
  relative to that goal.
- The mutated DAG has first break `I5`; `I6` reports `unsupported_input`, and
  `F13` and `F14` are unsupported.
- Lean compiles the end-to-end theorem
  `ProofDag0chi.all_powerSums_real`.
- Lean proves a concrete counterexample to the mutated recurrence at
  `a = b = c = 1` and `n = 0`.

The artifacts remain labelled `synthetic` until a human reviews the
natural-language-to-DAG translation.

## Current Boundary

The executable Rule Schema matcher checks canonical predicate names, premise
roles, selected exact outputs, and required variable-binding keys. It does not
yet prove arbitrary substitutions or semantic equivalence. Lean covers the
named high-risk steps, while faithfulness of the natural-language annotation
still needs human review.
