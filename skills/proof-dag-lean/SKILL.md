---
name: proof-dag-lean
description: Convert a natural-language mathematical proof into a validated Fact-Inference proof DAG, create controlled single-error mutations, locate the first invalid inference, and connect important inferences to Lean declarations. Includes a reusable playbook for radical functional inequalities and iterative algebra proofs. Use for proof annotation, dependency extraction, synthetic wrong-proof generation, critical-node analysis, algebra-proof normalization, or a DAG-plus-Lean formalization pilot.
---

# Proof DAG + Lean

Build artifacts against `proof-dag-schema-v0.4`, the machine interface for
`proof-skill-standard-v0.3`.

## Required References

Read before annotating:

- `references/annotation-spec.md`
- `references/team-spec-alignment.md`
- `references/lean-contract.md`
- `references/dag-schema.json`
- `references/verification-and-scope.md`

For functional inequalities or iteration-driven algebra, also read
`references/algebra-functional-inequality-playbook.md`.

## Workflow

1. Gate the source.
   - Preserve the original problem and candidate reference proof.
   - Human-review mathematical correctness before treating it as a reference.
2. Normalize the proof.
   - Separate assumptions, constructions, derived facts, and goals.
   - Split each rule application into one SPU.
   - Assign every Inference a unique contiguous `source_order`.
3. Build a static Reference DAG.
   - Facts are atomic propositions; Inferences are rule applications.
   - Each Inference has at least one input and exactly one output.
   - AND is one multi-premise Inference; OR is multiple producers.
   - Bind every input to a named premise role.
   - Store structure in the graph, not computed support or validity states.
4. Evaluate the Reference DAG.
   - Validate Schema, scopes, rule bindings, acyclicity, and target derivability.
   - Persist dynamic results separately in `correct_evaluation.json`.
5. Add formal grounding.
   - Keep all DAG-to-formal links in the single authority
     `formal_mapping.json`.
   - Compile the pinned Lean project and record exact coverage.
   - Do not infer semantic translation faithfulness from compilation alone.
6. Create one Candidate Graph.
   - Apply one declared intervention to an edge, rule, Fact, Inference, or scope.
   - Record the primary site, injection anchor, mutation type, seed, expected
     First Break, target effect, and provenance.
7. Re-evaluate from scratch.
   - Compute intrinsic and effective statuses without editing node labels.
   - Locate First Break by `source_order`.
   - Treat unsupported descendants as propagation, not extra injected errors.
   - Test Critical relative to a named target and exclude the target itself.
8. Review and promote.
   - Human-review source proof, DAG semantics, formal translation, mutation
     realism, First Break, and student-text consistency.
   - Record current, requested, and achieved annotation levels separately.

## Commands

```powershell
python skills/proof-dag-lean/scripts/validate_dag.py --graph <reference-or-candidate.json>
python skills/proof-dag-lean/scripts/evaluate_dag.py --graph <graph.json>
python skills/proof-dag-lean/scripts/evaluate_dag.py --graph <graph.json> --critical-candidate <node-id>
python skills/proof-dag-lean/scripts/check_artifact.py --graph <reference.json> --candidate-graph <candidate.json> --formal-mapping <formal_mapping.json> --project <lean-project> --run-build
```

## Acceptance Gates

Accept an artifact only if:

- the Reference DAG validates and derives every target;
- `source_order` is a complete bijection over Inferences;
- static nodes contain no cached dynamic truth state;
- the Candidate Graph records exactly one primary intervention;
- computed and declared First Break agree;
- propagation is separated from intrinsic failure;
- Critical is evaluated relative to a target other than the candidate;
- every claimed formal declaration exists and compiles;
- human-only checks remain explicitly human-only;
- the achieved level satisfies the requested promotion profile.
