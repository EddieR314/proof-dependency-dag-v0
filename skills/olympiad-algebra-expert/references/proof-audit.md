# Algebra Proof Audit

## Universal Checks

- Every substitution respects the domain.
- Every division has a nonzero premise.
- Squaring, square roots, logarithms, and monotone transformations have the
  required sign/domain facts.
- Equality conditions are propagated through every inequality used.
- Quantifier order is preserved.
- Necessity is not confused with sufficiency.
- Boundary, zero, repeated-root, and degenerate cases are handled.
- A cited theorem has all premises, not merely a matching conclusion shape.

## Module-Specific Risks

### Functional equations

- Unproved injectivity or surjectivity.
- Iteration outside the function domain.
- Assuming continuity, monotonicity, or orbit intersection.

### Inequalities

- Applying Jensen without convexity on the actual interval.
- Using smoothing without proving the transformation is monotone.
- Losing equality cases after normalization.

### Polynomials

- Comparing coefficients without a polynomial identity on an infinite domain.
- Counting roots without degree and nonzero-polynomial checks.
- Using Vieta before establishing multiplicity and field assumptions.

### Recurrences

- Guessing a formula from initial terms.
- Missing base cases or shifting the index illegally.
- Passing to a limit without convergence.

### Complex algebra

- Applying real order to complex quantities.
- Dividing by a root that may be zero.
- Confusing modulus equality with complex equality.

### Discrete algebra

- Replacing floor/ceiling inequalities by equalities.
- Ignoring endpoint cases in interval-to-integer conversion.
- Treating an integer-valued expression as arbitrary real data.
