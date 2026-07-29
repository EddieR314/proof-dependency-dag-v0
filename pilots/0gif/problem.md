# 0gif Functional-Inequality Pilot

## Problem

Let \(\mathbb{R}_{>0}\) be the set of positive real numbers. Determine all
functions \(f:\mathbb{R}_{>0}\to\mathbb{R}_{>0}\) such that

\[
x(f(x)+f(y))\ge (f(f(x))+y)f(y)
\]

for every \(x,y\in\mathbb{R}_{>0}\).

## Reviewed Natural-Language Proof

Write the assertion as \(P(x,y)\), and fix \(x>0\). Define its forward orbit by

\[
x_0=x,\qquad x_{n+1}=f(x_n).
\]

Every orbit term is positive. Substituting \(y=f(x)\) into \(P(x,y)\) gives

\[
x(x_1+x_2)\ge (x_2+x_1)x_2.
\]

The common factor \(x_1+x_2\) is positive, so \(x_0\ge x_2\). Applying the same
argument at every orbit point yields

\[
x_n\ge x_{n+2}\qquad(n\ge0). \tag{1}
\]

Next apply \(P(x_{n+1},x_n)\). It gives

\[
x_{n+1}(x_{n+2}+x_{n+1})
\ge(x_{n+3}+x_n)x_{n+1}.
\]

Since \(x_{n+1}>0\), cancellation gives

\[
x_{n+1}+x_{n+2}\ge x_n+x_{n+3}.
\]

Define \(d_n=x_n-x_{n+2}\). Equation (1) gives \(d_n\ge0\), and the last
inequality gives

\[
d_n\le d_{n+1}. \tag{2}
\]

For every \(N\ge1\),

\[
x_{2N}=x_0-\sum_{j=0}^{N-1}d_{2j}>0,
\]

so the even-indexed partial sums of the drops are bounded above by \(x_0\).
If some \(d_m>0\), monotonicity would make every sufficiently late
even-indexed drop at least \(d_m\), forcing those partial sums to be
unbounded. This contradiction proves \(d_n=0\) for every \(n\). In
particular,

\[
f(f(x))=x\qquad(x>0). \tag{3}
\]

Substituting (3) into the original inequality and cancelling \(xf(y)\) gives

\[
xf(x)\ge yf(y).
\]

Interchanging \(x\) and \(y\) gives the reverse inequality. Hence \(xf(x)\)
is a positive constant \(c\), and therefore

\[
f(x)=\frac{c}{x}
\]

for some \(c>0\).

Conversely, if \(f(x)=c/x\) with \(c>0\), then \(f\) maps positive reals to
positive reals, \(f(f(x))=x\), and both sides of the original inequality are
equal to

\[
c+\frac{cx}{y}.
\]

Thus the complete family is \(f(x)=c/x\), where \(c>0\).

## Review Status

- Natural-language proof: human-reviewed and passed on 2026-07-28.
- Reference DAG: generated separately and pending human semantic review.
- Mutation: not run.
- Lean: not run.
