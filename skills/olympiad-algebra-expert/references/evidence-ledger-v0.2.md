# Algebra Expert Evidence Ledger v0.2

This ledger separates mathematical proof review, DAG structure, DAG semantic
faithfulness, mutation checks, formal mapping, and Lean compilation.

| Problem | Primary module | Proof review | Reference DAG automatic | Candidate + First Break automatic | DAG semantic review | Mutation realism review | Lean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0gif` | functional equations / iteration | passed | passed | passed | passed | passed | passed |
| `00q2` | polynomials | passed | passed | passed, `I5` | passed | passed | deferred |
| `06og` | inequalities | passed | passed | passed, `I8` | passed | passed | deferred |
| `0ldq` | recurrences and sequences | passed | passed | passed, `I7` | passed | passed | deferred |
| `0le0` | discrete algebra | passed | passed, including two local scopes | passed, `I1` | passed | passed | deferred |
| `0chi` | complex algebra | passed | migrated v0.4 passed | passed, `I5` | passed | passed | passed; 3/6 high-risk/end-to-end mapping |

## Controlled Errors

- `00q2`: omit the mixed-degree decomposition needed for the lowest product
  component.
- `06og`: omit the identity that every pair occurs in exactly `n-2` triples.
- `0ldq`: infer a uniform contraction from a pointwise bound without using the
  compact invariant interval.
- `0le0`: read floor parity as a binary digit without first fixing the finite
  floor-based digit convention.
- `0chi`: change the recurrence term `+B*C_n` to `-B*C_n`; Lean contains a
  counterexample to this exact mutation.

## Freeze Record

- Human DAG semantic and mutation reviews: passed on 2026-07-29.
- Component-level status records: stored in each pilot.
- Frozen Skill version: `0.2`.
- Heldout policy: results are recorded separately and cannot modify `0.2`.
