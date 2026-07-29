# Algebra Expert Evidence Ledger v0.2-rc1

This ledger separates mathematical proof review, DAG structure, DAG semantic
faithfulness, mutation checks, formal mapping, and Lean compilation.

| Problem | Primary module | Proof review | Reference DAG automatic | Candidate + First Break automatic | DAG semantic review | Mutation realism review | Lean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0gif` | functional equations / iteration | passed | passed | passed | passed | passed | passed |
| `00q2` | polynomials | passed | passed | passed, `I5` | pending | pending | deferred |
| `06og` | inequalities | passed | passed | passed, `I8` | pending | pending | deferred |
| `0ldq` | recurrences and sequences | passed | passed | passed, `I7` | pending | pending | deferred |
| `0le0` | discrete algebra | passed | passed, including two local scopes | passed, `I1` | pending | pending | deferred |
| `0chi` | complex algebra | passed | migrated v0.4 passed | passed, `I5` | pending for migration | pending for migration | passed |

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

## Freeze Gate

Do not freeze `v0.2` until:

1. all five pending DAG semantic reviews are signed;
2. all five pending mutation realism reviews are signed;
3. review decisions are copied into component-level status records;
4. the Skill, Schema, checker, and evidence manifest receive immutable version
   identifiers and checksums;
5. heldout is run only after that freeze.
