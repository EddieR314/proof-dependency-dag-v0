# Formal Verification Contract

`formal_mapping.json` is the only authority linking DAG items to formal
declarations. Fact and Inference nodes do not contain Lean declaration names.

## Coverage

- `none`: no formal declaration is claimed.
- `local`: selected Inferences are mapped.
- `end_to_end`: every required Inference and the target theorem are covered.

Each mapping record identifies the backend, source file, declaration,
Inference ID, output Fact ID, expected result, and observed result.

## Lean Rules

1. Preserve domains, quantifiers, positivity, nonzero assumptions, and cases.
2. Use named declarations for mapped steps.
3. Keep definitional rewrites distinct from substantive theorem applications.
4. Pin the Lean toolchain and mathlib revision.
5. Reject `sorry` and `admit`.
6. Run `lake build` and declaration checks.
7. Represent a mutation with a counterexample or expected-failure record; do
   not leave an uncompilable file in the default build.

Compilation proves the encoded Lean declarations. It does not prove that the
natural-language statement, DAG Fact, and Lean proposition mean the same thing.
That semantic translation remains a named human-review gate.
