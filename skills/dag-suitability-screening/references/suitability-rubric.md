# DAG Suitability Rubric v0.1

## What is being judged

Judge whether the supplied olympiad-algebra statement and proof are suitable inputs for constructing a Fact-Inference Reference DAG. Do not judge whether the topic is prestigious, whether the model can solve it, or whether Lean will be easy. Route the proof mechanism to one of the six algebra modules; source taxonomy is only a hint.

## Score dimensions

Each score is an integer from 0 to 2.

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `source_integrity` | corrupt, truncated, or missing essential material | suspicious formatting or bounded repair needed | readable and internally coherent source |
| `proof_completeness` | absent, answer-only, or major missing argument | moderate omitted argument | substantially complete proof |
| `atomic_decomposability` | no stable proposition/rule units | units exist but require substantial normalization | clear atomic proposition and rule candidates |
| `dependency_explicitness` | dependencies must largely be invented | several recoverable implicit dependencies | dependencies are mostly traceable |
| `scope_traceability` | branches/quantifiers/local assumptions cannot be tracked | some ambiguity needing review | scopes are explicit or safely global |
| `external_context_burden` | essential missing image/reference/library | limited recoverable external context | self-contained for DAG purposes |
| `structural_richness` | only an answer or one opaque leap | short/mostly linear but valid proof structure | useful merges, cases, reusable facts, or alternatives |

`structural_richness=0` alone is not a hard rejection. A clean linear proof may still be suitable.

## Reason codes

Positive evidence:

- `complete_proof`
- `clear_inference_units`
- `traceable_dependencies`
- `scope_clear`
- `case_structure`
- `multi_premise_merge`
- `alternative_paths`
- `clean_linear_proof`

Risk or rejection evidence:

- `missing_solution`
- `answer_only`
- `proof_corrupted`
- `proof_truncated`
- `source_mojibake`
- `excessive_repetition`
- `image_required`
- `unresolved_reference`
- `opaque_large_jump`
- `pure_computation`
- `scope_ambiguous`
- `too_short_for_dag`
- `too_long_unstructured`
- `non_proof_content`

## Repair action codes

- `none`
- `recover_source`
- `recover_image`
- `remove_repetition`
- `resolve_reference`
- `expand_omitted_step`
- `clarify_scope`
- `normalize_notation`
- `human_math_review`

## Decision examples

- A correct-looking, readable chain of six algebraic implications: `suitable`, possibly `clean_linear_proof`.
- A proof with one named lemma whose statement is missing but easy to locate: `borderline`, `unresolved_reference`.
- A long solution containing repeated unrelated paragraphs: `unsuitable`, `proof_corrupted` and `excessive_repetition`.
- A geometry proof whose essential construction exists only in an unavailable diagram: `unsuitable`, `image_required`.
- A proof that is mathematically difficult for Lean but has explicit logical dependencies: potentially `suitable`; record Lean cost elsewhere.
