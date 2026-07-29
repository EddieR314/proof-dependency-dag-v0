# Algebra Functional-Inequality Playbook

Use this playbook for functional inequalities on ordered domains when radicals,
iteration, or a defect such as `f(x)-x` drives the proof. It is not a template
for every algebra problem.

## 1. Gate and Normalize

1. Preserve the exact domain, codomain, quantifiers, and radical conventions.
2. Replace radical inequalities by squared forms only after proving both sides
   nonnegative. Keep a named equivalence lemma when possible.
3. Separate:
   - domain and positivity Facts;
   - the original or safely squared inequalities;
   - substitutions;
   - algebraic identities;
   - global rigidity arguments;
   - candidate verification.
4. Do not treat a formula containing an unknown value such as `g(y)` as an
   ordinary polynomial in `y` unless that dependence has been removed.

## 2. Search for an Iterative Invariant

1. Try substitutions involving `f(x)` when the codomain makes them legal.
2. If an identity such as `f(f(x))=2f(x)-x` appears, define a defect or shift:

   ```text
   h(x) = f(x)-x.
   ```

3. Derive shift invariance and an iterate formula as separate inferences:

   ```text
   h(f(x))=h(x),
   f^[n](x)=x+n h(x).
   ```

4. Use codomain constraints on every iterate to constrain `h`; for example,
   positivity of all iterates can rule out `h(x)<0`.

Do not assume the iterate formula from a visual pattern. Prove the invariant
and induction explicitly.

## 3. Prove Global Rigidity Without Fake Orbit Intersections

When two starting points have positive shifts `a` and `b`, their orbits are
arithmetic progressions. They need not intersect.

Use a finite Archimedean comparison:

1. choose a sufficiently large point `X=u+n a`;
2. choose a nearby point `Y=v+m b` using `floor` or `round`;
3. record an explicit bound on `|X-Y|`;
4. apply the squared inequality to `(X,Y)`;
5. derive a contradiction if `a<b` or `a>b`;
6. prove both directions before concluding `a=b`.

Prefer a finite argument over an informal limit. If a limit is used, create
explicit convergence Facts and formalize them.

## 4. Eliminate a Residual Finite Choice

After proving that every shift is either `0` or one positive constant `c`, do
not assume continuity of `f`.

Instead:

1. derive quantitative separation between zero-shift and `c`-shift points;
2. prove each level set is relatively open;
3. use connectedness of the domain to rule out two nonempty disjoint open
   pieces.

The continuity-like conclusion comes from the inequality, not from an
unstated regularity assumption.

## 5. Verify Candidate Families

Substitute each candidate family into both inequalities. Reduce each gap to a
manifestly nonnegative expression such as a square. Verify parameter
restrictions from the codomain separately.

## 6. Recommended DAG Backbone

Keep these as distinct Inferences when they occur:

1. safe radical elimination;
2. special substitution and composition identity;
3. defect invariance;
4. iterate formula;
5. defect sign restriction;
6. forward orbit comparison;
7. reverse orbit comparison;
8. equality from the two comparisons;
9. finite-value dichotomy;
10. separation of level sets;
11. connectedness aggregation;
12. candidate necessity and sufficiency.

Equality from antisymmetry must consume both directional inequalities. This is
a useful critical-node candidate.

## 7. Controlled Mutations

Plausible single errors include:

- square without proving nonnegativity;
- omit the reverse inequality before claiming equality;
- assume two arithmetic orbits intersect;
- treat a function-dependent expression as a fixed-coefficient polynomial;
- invoke continuity without deriving local separation;
- alter one parameter restriction in the candidate family.

Never append a revealing template sentence. Recompute downstream support after
the mutation.

## 8. Lean Guidance

- Encode positive reals as a subtype, or use a total real function with every
  hypothesis and conclusion explicitly restricted to positive inputs.
- Name the safe-squaring equivalence and every high-risk global lemma.
- Use `exists_nat_gt` with `floor` or `round` for finite orbit comparison.
- Keep topology and connectedness in separate declarations.
- Compile an end-to-end classification theorem and record exact DAG coverage.

This playbook was extracted from one successful pilot. Treat it as a
hypothesis about a reusable proof pattern and test it on additional problems
before claiming broad algebra coverage.
