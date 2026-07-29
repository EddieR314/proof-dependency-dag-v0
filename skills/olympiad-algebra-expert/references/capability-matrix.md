# Capability Matrix

This Skill is evidence-driven. A written module is not automatically validated.

| Module | Current evidence | Status |
| --- | --- | --- |
| Functional iteration/orbits | P5 plus sealed `0gif`; reviewed proof, v0.4 DAG, controlled mutation, First Break, Lean | validated pilots |
| General functional equations | integer-functional and positive-orbit proofs checked against references | proof calibration complete for current pair; DAG/Lean required |
| Inequalities | `06og` reviewed proof; reviewed v0.4 Reference/Candidate DAG; verified First Break `I8` | validated pilot |
| Polynomials | `00q2` reviewed proof; reviewed v0.4 Reference/Candidate DAG; verified First Break `I5` | validated pilot |
| Recurrences and sequences | `0ldq` reviewed proof; reviewed v0.4 Reference/Candidate DAG; verified First Break `I7` | validated pilot |
| Complex algebra | `0chi` reviewed migrated v0.4 DAG and mutation; First Break `I5`; non-functional Lean build and 3/6 high-risk/end-to-end mapping pass | validated pilot with partial formal coverage |
| Discrete algebra | `0le0` reviewed proof and mutation; two local scopes pass; verified First Break `I1` | validated pilot |

Promote a module only after multiple source-diverse problems expose stable:

1. proof-normalization patterns;
2. recurring hidden premises and failure modes;
3. SPU and Rule Schema patterns;
4. feasible Lean lemmas or clearly documented formalization blockers;
5. held-out forward-test performance.

These labels mean that one reviewed pilot exists for the module. They do not
establish broad module-level generalization across the full source
distribution.
