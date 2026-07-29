# Capability Matrix

This Skill is evidence-driven. A written module is not automatically validated.

| Module | Current evidence | Status |
| --- | --- | --- |
| Functional iteration/orbits | P5 plus sealed `0gif`; reviewed proof, v0.4 DAG, controlled mutation, First Break, Lean | validated pilots |
| General functional equations | integer-functional and positive-orbit proofs checked against references | proof calibration complete for current pair; DAG/Lean required |
| Inequalities | `06og` reviewed proof; v0.4 Reference/Candidate DAG and First Break pass automatically | candidate; human DAG/mutation review pending |
| Polynomials | `00q2` reviewed proof; v0.4 Reference/Candidate DAG and First Break pass automatically | candidate; human DAG/mutation review pending |
| Recurrences and sequences | `0ldq` reviewed proof; v0.4 Reference/Candidate DAG and First Break pass automatically | candidate; human DAG/mutation review pending |
| Complex algebra | `0chi` migrated v0.4 DAG, wrong-sign mutation, First Break, and non-functional Lean build pass | candidate; migrated DAG/mutation human review pending |
| Discrete algebra | `0le0` reviewed proof; two local case scopes, v0.4 DAG, mutation, and First Break pass automatically | candidate; human DAG/mutation review pending |

Promote a module only after multiple source-diverse problems expose stable:

1. proof-normalization patterns;
2. recurring hidden premises and failure modes;
3. SPU and Rule Schema patterns;
4. feasible Lean lemmas or clearly documented formalization blockers;
5. held-out forward-test performance.

Automatic structural success does not promote a row from `candidate`.
Promotion requires the named human reviews in
`evidence-ledger-v0.2.md`.
