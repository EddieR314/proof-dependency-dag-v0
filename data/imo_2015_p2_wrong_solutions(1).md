# Wrong Solution Set: IMO 2015 Problem 2

## Problem

Find all triples \((a,b,c)\) of positive integers such that
\[
ab-c,\qquad bc-a,\qquad ca-b
\]
are all powers of \(2\).

Here \(1=2^0\) is allowed.

## Correct Answer

The solutions are
\[
(2,2,2),\quad (2,2,3),\quad (2,6,11),\quad (3,5,7),
\]
and all permutations of these triples.

## Simplified Correct Proof DAG

| Node | Kind | Statement |
| ---- | ---- | --------- |
| D1 | Fact | \((a,b,c)\) is a positive integer triple satisfying the condition. |
| D2 | Inference | Permute variables and assume \(a\ge b\ge c\). |
| D5 | Fact | \(ab-c\ge ca-b\ge bc-a\). |
| D7 | Fact | \(bc-a\mid ca-b\mid ab-c\). |
| D12 | Fact | Case 1 gives \((a,b,c)=(2,2,2)\). |
| D17 | Fact | Case 2 gives \((a,b,c)=(7,5,3)\). |
| D22 | Fact | Mixed parity case gives \((a,b,c)=(3,2,2)\) or \((11,6,2)\). |
| D26 | Final Fact | All solutions are permutations of \((2,2,2),(2,2,3),(2,6,11),(3,5,7)\). |

## Wrong Solution Types

This v0 dataset contains five controlled wrong-solution mutations:

1. `missing_premise_edge`: uses the parity-dependent claim \(a^2-1\) is odd without assuming \(a\) is even.
2. `case_omission`: proves the even-\(a\) and all-odd cases but omits the mixed parity case.
3. `invalid_theorem_use`: treats ordered powers of \(2\) as consecutive powers of \(2\).
4. `overclaim_final`: solves only the ordered case but forgets to apply all permutations.
5. `variable_mismatch`: repeats information about \(bc-a\) in the mixed parity case instead of analyzing \(ca-b\).

The structured SPU labels for these five samples are in:

```text
data/imo_2015_p2_spu_dependency_gold_v0.jsonl
```
