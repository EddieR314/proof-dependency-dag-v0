# Algebra Pattern Library v0.1

These patterns come from blind calibration proofs that were compared with the
stored reference only after drafting. They are proof-normalization aids, not
theorems that may be applied without checking their premises.

## Equal-Modulus Complex Tuples

When nonzero complex numbers have common modulus \(r\), use
\(\bar z=r^2/z\). Real elementary symmetric sums can then be recovered from
the real sum and product. Once all polynomial coefficients are real, use
Newton sums or the characteristic recurrence to prove power sums are real.

Required premises:

- every complex number is nonzero;
- the common modulus is positive;
- the recurrence base cases are explicit.

## Homogeneous Target With a Mixed-Degree Divisor

If a homogeneous polynomial \(G\) equals \(FH\), compare the lowest and
highest nonzero homogeneous components of \(F\) and \(H\). In an integral
domain, the extreme products cannot cancel. This can rule out divisibility
without claiming, without proof, that every divisor of a homogeneous
polynomial is homogeneous.

## Monotone Maps Have No Nontrivial Finite Cycles

Rewrite a cyclic real system as

\[
x_2=T(x_1),\ldots,x_1=T(x_k).
\]

If \(T\) is strictly increasing on the whole relevant domain, any strict
ordering propagates around the cycle and contradicts itself. Therefore all
cycle entries coincide and the system reduces to a fixed-point equation.

Do not use this pattern before proving global monotonicity.

## Sum-Difference Diagonalization

For symmetric quadratic systems in two real variables, add and subtract the
equations to obtain independent equations in \(u=x+y\) and \(v=x-y\). The map

\[
(x,y)\leftrightarrow(u,v)
\]

is invertible over \(\mathbb R\), so solving both transformed equations gives
both necessity and sufficiency.

## Integer Rank Followed by Affine Dynamics

For floor recurrences, identify an integer-valued rank such as
\(\lfloor a_i\rfloor\) or \(\lceil -a_i\rceil\). Prove the rank is monotone and
therefore eventually stable. Only after stabilization replace the recurrence
by its fixed affine rule. If the affine multiplier has modulus greater than
one while the orbit remains bounded, the orbit must be at the affine fixed
point; multiplier \(-1\) produces eventual period two.

## Global Pair Sum Reduced to Triple Inequalities

For sums over pairs, expand the global total \(S\) inside each pair term and
collect the remaining contributions by triples. Use the combinatorial identity
that each pair lies in exactly \(n-2\) triples. A local positive-variable
inequality on each triple can then prove the global estimate.

Track the factors of two and handle \(n=2\) separately when the triple set is
empty.

## Fixed-Point Deviation Contraction

For a recurrence \(x_{n+1}=F(x_n)\), identify a fixed point \(L\) and derive
an exact relation

\[
x_{n+1}-L=-\rho(x_n)(x_n-L).
\]

If \(0<\rho<1\) on an invariant interval, the deviations alternate and
contract. This simultaneously proves convergence and gives alternating-series
bounds for partial sums.

Do not infer convergence from \(F(L)=L\) alone.

## Orbit Drops Forced to Vanish

For a positive functional orbit \(x_{n+1}=f(x_n)\), a substitution may give
two-step monotonicity \(x_n\ge x_{n+2}\). If a second substitution shows the
drops

\[
d_n=x_n-x_{n+2}
\]

are nonnegative and nondecreasing, positivity of the even and odd
subsequences forces every \(d_n=0\). This upgrades a one-sided iterate bound
to \(f(f(x))=x\).

## Binary Cylinders For Floor Parity

For a finite depth \(M\), define binary digits through

\[
\lfloor2^j a\rfloor
=2\lfloor2^{j-1}a\rfloor+d_j.
\]

Then the parity of \(\lfloor2^j a\rfloor\) is exactly \(d_j\). Any expression
depending only on these \(M\) parities is constant on each dyadic cylinder
\([k/2^M,(k+1)/2^M)\). If the comparison function is monotone, reduce the
proof to the appropriate cylinder endpoint.

This floor-based definition avoids the two binary representations of dyadic
rationals.

## Shift A Recurrence Before Estimating

For an affine nonhomogeneous recurrence, first search for a shift that turns it
into a homogeneous geometric recurrence. Prove the resulting closed form
before applying inequalities. Keep exceptional indices separate when a later
bound uses conditions such as \(n\ge2\).

## Rational Substitution To A Square

When a rational inequality contains repeated Möbius-type expressions, use a
domain-checked substitution to expose a square or another manifestly
nonnegative expression. Record excluded denominator values and prove that the
substitution covers the intended family.

## Power Sums Reconstruct Polynomial Data

Use Newton identities to convert sufficiently many power sums into elementary
symmetric polynomials, then identify the associated monic polynomial. State
whether the conclusion concerns ordered tuples, sets, or multisets; equality
of root polynomials preserves multiplicity.

## Cyclic Difference Spectral Bound

For complex values on a cycle, compare the minimum consecutive difference
with total edge energy, then bound total edge energy by the largest eigenvalue
of the cycle Laplacian. The Fourier eigenvalues are

\[
4\sin^2\frac{\pi j}{n}.
\]

The parity-dependent maximum gives the sharp constant, and a maximal-frequency
Fourier mode supplies the equality construction. Keep the minimum-to-average
inequality direction explicit.

## Evidence Boundary

These patterns have passed natural-language proof review on calibration
examples. They have not all been converted to validated v0.4 DAGs or compiled
Lean declarations. Their current handoff status is `candidate`.
