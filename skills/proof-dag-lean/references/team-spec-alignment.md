# Team Specification Alignment

`proof-skill-standard-v0.3` is the human-readable meta-standard.
`proof-dag-schema-v0.4` is its executable graph interface.

| Team concept | v0.4 representation | Executable check | Human boundary |
| --- | --- | --- | --- |
| Atomic proposition | static `facts[]` | Schema and unique IDs | Atomicity and truth |
| One rule application per SPU | static `inferences[]` | Inputs, one output, order | Segmentation quality |
| Producer/consumer | computed from bindings | Fixed-point evaluation | Annotation completeness |
| Premise semantics | named `premise_role` | Rule Schema matching | Correct role choice |
| Reading order | `source_order` | Bijection over `1..N` | Faithful source alignment |
| Scope | rooted `scopes[]` | Visibility and parent checks | Scope extraction |
| Support/validity | separate evaluations | Recomputed, never trusted | Deep theorem validity |
| Alternative path | multiple producers | Fixed-point derivation | Missing alternatives |
| First Break | structured locator | Recomputed by source order | Error interpretation |
| Critical | block and rederive | Target-relative computation | Choice of target |
| Controlled error | generic mutation record | Site, anchor, FB agreement | Plausibility |
| Formal grounding | `formal_mapping.json` | Coverage, declarations, build | Translation faithfulness |
| Promotion | three level fields + profile | Gate completeness | Human sign-off |

## P5 Coverage

The functional-inequality P5 pilot exercises:

- 22 atomic Facts and 18 ordered Inferences;
- complete role and variable bindings;
- a Reference DAG that derives `F22`;
- one missing-premise edge mutation at `F13 -> I10`;
- intrinsic First Break at `I10`;
- downstream `unsupported_input` propagation while independent branches remain
  valid;
- Criticality of `I10` relative to `F22`;
- end-to-end Lean mapping and a pinned successful build.

The proof is globally quantified, so `local_scope_count = 0` is expected. Scope
discharge and sibling-visibility behavior are covered by generic regression
tests, not artificially inserted into this proof.
