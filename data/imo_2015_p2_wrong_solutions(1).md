# Wrong Solution Set: IMO 2015 Problem 2

Source: `Lean题库/IMO.pdf`, IMO 2015/2 solution section on PDF page 87.

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

This is not the full formal proof; it is the inference-node skeleton used to generate controlled wrong solutions.

| Node | Kind | Statement |
| ---- | ---- | --------- |
| D1 | Fact | \((a,b,c)\) is a positive integer triple satisfying the condition. |
| D2 | Inference | Permute variables and assume \(a\ge b\ge c\). |
| D3 | Fact | \(a\ge b\ge c>1\). |
| D4 | Inference | Compare the three expressions using \(a\ge b\ge c\). |
| D5 | Fact | \(ab-c\ge ca-b\ge bc-a\). |
| D6 | Inference | Use the fact that ordered powers of \(2\) divide each other. |
| D7 | Fact | \(bc-a\mid ca-b\mid ab-c\). |
| D8 | Case Fact | Case 1: \(a\) is even. |
| D9 | Inference | Use gcd estimate with \(ca-b=\gcd(ab-c,ca-b)\). |
| D10 | Fact | \(ca-b\le c\). |
| D11 | Inference | Combine \(a\ge b\ge c>1\) with \(ca-b\le c\). |
| D12 | Fact | Case 1 gives \((a,b,c)=(2,2,2)\). |
| D13 | Case Fact | Case 2: \(a,b,c\) are all odd. |
| D14 | Inference | Use the 2-adic estimate involving \(a^2-1\). |
| D15 | Fact | \(c=3\) and \(a=b+2\). |
| D16 | Inference | Use \(ca-b\ge 2(bc-a)\). |
| D17 | Fact | Case 2 gives \((a,b,c)=(7,5,3)\). |
| D18 | Case Fact | Case 3: \(a\) is odd and \(b,c\) are even. |
| D19 | Inference | Use parity to get \(bc-a=1\). |
| D20 | Fact | \(bc-a=1\). |
| D21 | Inference | Use the identity involving \(c^3-b-c\). |
| D22 | Fact | Mixed parity case gives \((a,b,c)=(3,2,2)\) or \((11,6,2)\). |
| D23 | Inference | Aggregate the parity cases. |
| D24 | Final Fact | Ordered solutions are \((2,2,2),(3,2,2),(11,6,2),(7,5,3)\). |
| D25 | Inference | Apply all permutations. |
| D26 | Final Fact | All solutions are permutations of \((2,2,2),(2,2,3),(2,6,11),(3,5,7)\). |

## Wrong Solution 1

Mutation type: `missing_premise_edge`

Target flaw: The proof uses divisibility between powers of \(2\), but never justifies the ordering step carefully enough.

### Student-Style Wrong Solution

Assume without loss of generality that \(a\ge b\ge c\). Then clearly
\[
ab-c,\quad ca-b,\quad bc-a
\]
are powers of \(2\), so the smaller ones divide the larger ones. In particular,
\[
ca-b\mid ab-c.
\]
Hence
\[
ca-b=\gcd(ab-c,ca-b).
\]
Now
\[
\gcd(ab-c,ca-b)
\le \gcd(ab-c,a(ca-b)+ab-c)
=\gcd(ab-c,c(a^2-1)).
\]
Since \(a^2-1\) is odd, this gcd is at most \(c\). Therefore
\[
ca-b\le c.
\]
But \(a\ge b\ge c\), so this forces \(a=b=c=2\). Thus the only ordered solution is \((2,2,2)\), and by permutation the only solution is \((2,2,2)\).

### Why It Is Wrong

The argument silently applies the “\(a^2-1\) is odd” step as if \(a\) were even, but no parity case has been assumed. If \(a\) is odd, then \(a^2-1\) is even, and the gcd estimate collapses. The proof deletes the case node \(a\) is even but still uses the theorem that depends on it.

## Wrong Solution 2

Mutation type: `case_omission`

Target flaw: The solution proves two parity cases and forgets the mixed case.

### Student-Style Wrong Solution

We may suppose \(a\ge b\ge c\). Then
\[
ab-c\ge ca-b\ge bc-a,
\]
so since all three are powers of \(2\), we have
\[
bc-a\mid ca-b\mid ab-c.
\]

First suppose \(a\) is even. Then \(ab-c\) being a power of \(2\) implies \(c\) is even. Using
\[
ca-b=\gcd(ab-c,ca-b)
\le \gcd(ab-c,c(a^2-1)),
\]
and \(a^2-1\) odd, we get \(ca-b\le c\). This gives \(a=b=c=2\).

Now suppose all of \(a,b,c\) are odd. Then the usual estimate gives
\[
ca-b\le 2^{\nu_2(a^2-1)}\le 2a+2.
\]
Since \(ca-b\ge 3a-b\), we must have \(c=3\). Then \(a=b+2\), and from
\[
ca-b\ge 2(bc-a)
\]
we get \(a=7,b=5\). This gives \((a,b,c)=(7,5,3)\).

Therefore the ordered solutions are \((2,2,2)\) and \((7,5,3)\), so all solutions are their permutations.

### Why It Is Wrong

It omits the mixed parity case \(a\) odd and \(b,c\) even. That missing branch contains the ordered solutions \((3,2,2)\) and \((11,6,2)\), corresponding to permutations of \((2,2,3)\) and \((2,6,11)\).

## Wrong Solution 3

Mutation type: `invalid_theorem_use`

Target flaw: It treats “ordered powers of \(2\)” as if consecutive powers must differ by a factor of exactly \(2\).

### Student-Style Wrong Solution

Assume \(a\ge b\ge c\). Then
\[
ab-c\ge ca-b\ge bc-a.
\]
Since these are powers of \(2\), the three numbers must occur as consecutive powers of \(2\). Hence
\[
ab-c=2(ca-b),\qquad ca-b=2(bc-a).
\]
Subtracting the two equations gives
\[
ab-3ca+2bc+c+2b-2a=0.
\]
Rearranging,
\[
a(b-3c-2)+2bc+2b+c=0.
\]
Since \(b\le a\) and \(c\le b\), the only way for this to hold with positive integers is with very small values. Checking \(c=2\) gives \((a,b,c)=(2,2,2)\), and checking \(c=3\) gives \((7,5,3)\). Thus the solutions are the permutations of \((2,2,2)\) and \((3,5,7)\).

### Why It Is Wrong

Ordered powers of \(2\) need not be consecutive powers. For example \(1,4,16\) are ordered powers of \(2\), but the ratios are \(4\) and \(4\), not \(2\). The inference node “ordered powers imply exact ratio \(2\)” is a false theorem.

## Wrong Solution 4

Mutation type: `overclaim_final`

Target flaw: The ordered answer is found, but the final answer forgets permutations.

### Student-Style Wrong Solution

We arrange the variables so that \(a\ge b\ge c\). Then
\[
ab-c\ge ca-b\ge bc-a.
\]
Because all three numbers are powers of \(2\), the smaller ones divide the larger ones. We split into parity cases.

If \(a\) is even, the gcd argument gives \(ca-b\le c\), hence \((a,b,c)=(2,2,2)\).

If all three are odd, the 2-adic bound applied to \(a^2-1\) gives \(c=3\) and \(a=b+2\). Then using \(ca-b\ge 2(bc-a)\), we obtain \((a,b,c)=(7,5,3)\).

Finally, if \(a\) is odd while \(b,c\) are even, then \(bc-a=1\). The standard identity
\[
c^3-b-c=(1-c^2)(ab-c)+a(ca-b)+(ca-b)
\]
forces either \(c^3-b-c\ne0\), giving \((3,2,2)\), or \(c^3-b-c=0\), giving \((11,6,2)\).

Therefore the solutions are exactly
\[
(2,2,2),\quad (3,2,2),\quad (7,5,3),\quad (11,6,2).
\]

### Why It Is Wrong

The proof started with a WLOG ordering \(a\ge b\ge c\). The final answer lists only ordered triples, not all permutations. The mathematical classification branch is mostly correct, but the final translation step is missing.

## Wrong Solution 5

Mutation type: `variable_mismatch`

Target flaw: It mixes up \(ca-b\) and \(bc-a\) in the mixed parity case.

### Student-Style Wrong Solution

Assume \(a\ge b\ge c\). Then
\[
ab-c\ge ca-b\ge bc-a.
\]
We only need to consider parity cases.

If \(a\) is even, the usual gcd estimate gives \(ca-b\le c\), hence \((a,b,c)=(2,2,2)\). If \(a,b,c\) are all odd, the 2-adic estimate gives \(c=3,a=b+2\), so \((a,b,c)=(7,5,3)\).

Now suppose \(a\) is odd and \(b,c\) are even. Then \(bc-a\) is odd, so \(bc-a=1\). Thus
\[
a=bc-1.
\]
Substituting this into \(bc-a\), we get
\[
bc-a=bc-(bc-1)=1.
\]
So the mixed case only gives the small solution \(b=c=2,a=3\). Therefore the ordered solutions are
\[
(2,2,2),\quad (3,2,2),\quad (7,5,3),
\]
and all solutions are their permutations.

### Why It Is Wrong

The mixed case needs information about \(ca-b\), not merely a repeated verification of \(bc-a=1\). The solution never uses the identity involving \(c^3-b-c\), so it misses \((a,b,c)=(11,6,2)\). In DAG terms, it replaces the real mixed-case inference node with an irrelevant self-check.

