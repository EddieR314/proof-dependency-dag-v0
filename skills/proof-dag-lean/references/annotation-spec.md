# Proof DAG Annotation Specification

This is the operational summary of `proof-dag-schema-v0.4`.

## Static Graph

A graph is either a `reference` or `candidate` Fact-Inference graph.

- **Fact**: one atomic proposition with `id`, statement, canonical form,
  introduction kind, roles, scope, and source spans.
- **Inference/SPU**: one rule application with a unique contiguous
  `source_order`, at least one role-bound input Fact, exactly one output Fact,
  variable bindings, scope, and source spans.
- **Rule Schema**: declares premise roles, variable requirements, output
  pattern, and permitted scope behavior.

Producer and consumer relations are derived from bindings. Do not duplicate
them as another authority. AND uses one multi-premise Inference; alternative
proofs use multiple producers of the same Fact.

Static Facts and Inferences must not store support, availability, validity,
reason codes, or Lean declarations. Those belong to evaluation and mapping
records.

## Ordering

`source_order` is the reading order of Inferences in the source proof, not a
topological sort. It must be a bijection onto `1..N`. First Break is undefined
when this condition fails.

## Scope

Scopes form a rooted hierarchy.

- An Inference may consume Facts from its own scope or ancestors.
- It may not consume sibling or descendant Facts.
- Local assumptions cannot escape without an explicit discharge, merge, or
  export Inference whose Rule Schema permits it.
- A globally quantified theorem may legitimately use only the global scope.

## Reference and Candidate

A Reference DAG represents the reviewed proof and must be acyclic and derive
its targets. A Candidate Graph uses the same core Schema but may represent
missing premises, illegal scopes, rule mismatches, unsupported Facts, or
cycles. Such defects are computed in evaluation; they are not hand-written
node states.

## Dynamic Evaluation

Evaluation produces separate `FactEvaluation` and `InferenceEvaluation`
records.

- `intrinsic_status` asks whether the rule application itself is valid.
- `effective_status` also accounts for unsupported inputs.
- Fact support is recomputed from root introductions and valid producers.
- Descendants blocked by an earlier error receive propagation reasons such as
  `unsupported_input`; they are not extra primary errors.

## First Break

First Break is the earliest Inference by `source_order` whose intrinsic status
is invalid. For an omission, use the first surviving Inference that requires the
missing support; if none exists, use the first unjustified aggregation or goal
producer. Store a structured locator such as
`{"type": "inference", "id": "I10"}`.

## Critical

Criticality is relative to `(graph, target_fact, candidate_node)`. Confirm the
target is initially derivable, block the candidate, and re-evaluate. The
candidate is Critical exactly when the target becomes underivable. The target
itself is excluded. Degree, reach, and condition count are features, not the
definition.

## Mutation Record

Each Candidate Graph declares exactly one primary intervention and records:

- mutation type and seed;
- primary site and injection anchor;
- declared expected First Break;
- whether graph structure changed;
- expected target effect;
- mutation provenance.

Do not hard-code invalid states into descendants, append revealing templates,
or emit a sample when no mathematical content changed.

## Promotion

Track `current_annotation_level`, `requested_annotation_level`, and
`achieved_annotation_level` separately. Automatic checks can establish
structural and formal-build evidence; proof correctness, DAG semantic
faithfulness, translation faithfulness, and mutation realism remain human
review tasks.
