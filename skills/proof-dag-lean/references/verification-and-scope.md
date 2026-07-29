# Verification Status and Local Scope

Current, requested, and achieved annotation levels must be recorded separately.
None of them replaces the individual verification records.

## Independent Verification Records

Every promoted artifact should record:

- `proof_review`: human review of the mathematical proof;
- `dag_schema`: automatic JSON Schema validation;
- `dag_semantics`: executable derivability plus human dependency review;
- `lean_build`: automatic compilation status;
- `formal_mapping`: automatic declaration existence, output-Fact mapping, and coverage;
- `lean_translation_review`: human review that the Lean statement faithfully
  encodes the intended natural-language inference;
- `mutation`: single-intervention and First Break checks;
- `scope`: automatic visibility and promotion checks.

Allowed statuses are `not_run`, `passed`, `failed`, `partial`, and
`not_applicable`. Allowed methods are `automatic`, `human`, and `hybrid`.

## Scope Visibility

Scope IDs are hierarchical. The root is `global`; a case may use an ID such as
`global/case_even`.

- An Inference may consume Facts from its own scope or any ancestor scope.
- It may not consume Facts from a child or sibling scope.
- Its output normally remains in the Inference scope.
- Exporting a local result to an ancestor requires a Rule Schema that explicitly
  permits discharge, merge, or export.
- Export to a child or sibling scope is invalid.
- A case assumption remains local. An ancestor conclusion must be produced by a
  rule that discharges or aggregates the local assumptions.

The evaluator reports every violation with the Inference ID, Fact ID, Fact
scope, Inference scope, and violation kind.

## Automatic Lean Mapping Boundary

`check_artifact.py` automatically checks:

- referenced DAG IDs exist;
- mapped declarations exist in the Lean source;
- an Inference and its output Fact map to the same declaration;
- coverage and unmapped Inferences;
- absence of `sorry` and `admit`;
- a real `lake build`, when requested.

It does not prove that a natural-language statement and its Lean encoding mean
exactly the same thing. Record that separately under
`formal_translation_review`.
