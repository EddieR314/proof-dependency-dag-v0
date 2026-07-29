# 00q2 Polynomial Divisibility

## Problem

Determine all positive integers \(n\) such that

\[
f_n(x,y,z)=x^{2n}+y^{2n}+z^{2n}-xy-yz-zx
\]

divides

\[
g_n(x,y,z)=(x-y)^{5n}+(y-z)^{5n}+(z-x)^{5n}
\]

as polynomials in \(x,y,z\) with integer coefficients.

## Reviewed Natural-Language Proof

Write

\[
f_n=F_2+F_{2n},\qquad
F_2=-(xy+yz+zx),\qquad
F_{2n}=x^{2n}+y^{2n}+z^{2n}.
\]

For \(n>1\), suppose \(g_n=f_nh\), and let the smallest and largest
nonzero homogeneous degrees of \(h\) be \(l\) and \(u\). The product has
nonzero lowest-degree component \(F_2h_l\), of degree \(l+2\), and nonzero
highest-degree component \(F_{2n}h_u\), of degree \(u+2n\). These components
are nonzero because the polynomial ring over the integers is an integral
domain. Since \(g_n\) is homogeneous of degree \(5n\),

\[
l+2=5n=u+2n.
\]

Therefore \(l=5n-2\) and \(u=3n\). The necessary inequality \(l\le u\)
implies \(n\le1\), contradicting \(n>1\). Hence divisibility for a positive
integer \(n\) forces \(n=1\).

For \(n=1\), put \(p=x-y\), \(q=y-z\), and \(r=z-x\). Then
\(p+q+r=0\), and

\[
p^5+q^5+r^5=\frac52pqr(p^2+q^2+r^2).
\]

Moreover,

\[
f_1=x^2+y^2+z^2-xy-yz-zx
=\frac12(p^2+q^2+r^2).
\]

Consequently,

\[
g_1=5pqr f_1,
\]

so \(f_1\mid g_1\). Therefore the only solution is \(n=1\).

## Review Status

- Natural-language proof review: passed.
- Reviewer: Ruan Haochen (Eddie).
- Review date: 2026-07-28.
- Primary module: `polynomials`.
- Main risk: inferring that a divisor of a homogeneous polynomial is
  homogeneous without the lowest/highest nonzero-degree argument.
