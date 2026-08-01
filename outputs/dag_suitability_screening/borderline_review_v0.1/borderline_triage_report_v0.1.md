# Borderline second-stage triage v0.1

Total: 59

## Buckets

- source_recovery: 28
- bounded_proof_repair: 21
- scope_clarification: 8
- hard_source_failure: 1
- low_dag_yield: 1

## Recommendations

- keep_borderline: 58
- downgrade_unsuitable: 1

## Records

| ID | Module | Bucket | Recommendation | Reasons |
| --- | --- | --- | --- | --- |
| 042l | inequalities | bounded_proof_repair | keep_borderline | clear_inference_units, case_structure, unresolved_reference |
| 040g | recurrences_sequences | source_recovery | keep_borderline | traceable_dependencies, clean_linear_proof, excessive_repetition |
| 05xg | functional_equations | bounded_proof_repair | keep_borderline | clear_inference_units, traceable_dependencies, case_structure, opaque_large_jump |
| 07e6 | polynomials | bounded_proof_repair | keep_borderline | case_structure, multi_premise_merge, opaque_large_jump |
| 0fs7 | inequalities | source_recovery | keep_borderline | complete_proof, clear_inference_units, traceable_dependencies, alternative_paths, excessive_repetition |
| 09s9 | polynomials | source_recovery | keep_borderline | complete_proof, clear_inference_units, traceable_dependencies, scope_clear, case_structure, alternative_paths, source_mojibake |
| 02m4 | inequalities | bounded_proof_repair | keep_borderline | clear_inference_units, case_structure, opaque_large_jump |
| 0cht | discrete_algebra | scope_clarification | keep_borderline | case_structure, multi_premise_merge, opaque_large_jump, scope_ambiguous |
| 046v | complex_algebra | source_recovery | keep_borderline | source_mojibake, opaque_large_jump |
| 0483 | complex_algebra | source_recovery | keep_borderline | source_mojibake, opaque_large_jump |
| 0cud | polynomials | source_recovery | keep_borderline | complete_proof, clear_inference_units, traceable_dependencies, excessive_repetition |
| 0gji | functional_equations | bounded_proof_repair | keep_borderline | opaque_large_jump, alternative_paths |
| 046d | inequalities | bounded_proof_repair | keep_borderline | opaque_large_jump, case_structure |
| 06wc | functional_equations | source_recovery | keep_borderline | proof_corrupted, opaque_large_jump, unresolved_reference |
| 03wa | recurrences_sequences | source_recovery | keep_borderline | proof_corrupted, alternative_paths |
| 07et | functional_equations | source_recovery | keep_borderline | source_mojibake, opaque_large_jump, case_structure |
| 0etl | polynomials | source_recovery | keep_borderline | source_mojibake, complete_proof, clear_inference_units |
| 09kg | inequalities | source_recovery | keep_borderline | excessive_repetition, opaque_large_jump |
| 00c4 | inequalities | bounded_proof_repair | keep_borderline | opaque_large_jump |
| 01st | functional_equations | scope_clarification | keep_borderline | scope_ambiguous, opaque_large_jump |
| 03y0 | inequalities | source_recovery | keep_borderline | proof_corrupted, opaque_large_jump |
| 03z3 | inequalities | source_recovery | keep_borderline | proof_truncated |
| 0hi8 | polynomials | scope_clarification | keep_borderline | opaque_large_jump, scope_ambiguous |
| 04bk | polynomials | bounded_proof_repair | keep_borderline | opaque_large_jump |
| 01ik | functional_equations | bounded_proof_repair | keep_borderline | opaque_large_jump, case_structure, scope_clear |
| 07vf | polynomials | source_recovery | keep_borderline | proof_corrupted, alternative_paths, multi_premise_merge |
| 0fm4 | polynomials | hard_source_failure | downgrade_unsuitable | opaque_large_jump, case_structure, clean_linear_proof |
| 0le3 | recurrences_sequences | bounded_proof_repair | keep_borderline | opaque_large_jump |
| 0601 | recurrences_sequences | source_recovery | keep_borderline | source_mojibake |
| 09vy | recurrences_sequences | bounded_proof_repair | keep_borderline | unresolved_reference |
| 0ggr | functional_equations | bounded_proof_repair | keep_borderline | unresolved_reference, opaque_large_jump |
| 06ur | functional_equations | source_recovery | keep_borderline | proof_corrupted, opaque_large_jump |
| 0esd | polynomials | bounded_proof_repair | keep_borderline | opaque_large_jump |
| 0evc | functional_equations | scope_clarification | keep_borderline | opaque_large_jump, scope_ambiguous |
| 0get | inequalities | source_recovery | keep_borderline | source_mojibake, complete_proof, clear_inference_units, alternative_paths |
| 0lfb | functional_equations | bounded_proof_repair | keep_borderline | opaque_large_jump, complete_proof, case_structure |
| 04yf | functional_equations | bounded_proof_repair | keep_borderline | opaque_large_jump, case_structure, clear_inference_units |
| 07qs | recurrences_sequences | bounded_proof_repair | keep_borderline | opaque_large_jump, case_structure, clear_inference_units |
| 099e | functional_equations | scope_clarification | keep_borderline | opaque_large_jump, scope_ambiguous, too_long_unstructured |
| 0hht | functional_equations | scope_clarification | keep_borderline | opaque_large_jump, scope_ambiguous |
| 0l9j | recurrences_sequences | source_recovery | keep_borderline | source_mojibake, opaque_large_jump |
| 00he | functional_equations | bounded_proof_repair | keep_borderline | unresolved_reference, opaque_large_jump |
| 03wf | recurrences_sequences | source_recovery | keep_borderline | source_mojibake |
| 08t2 | unclassified_algebra | low_dag_yield | keep_borderline | opaque_large_jump, pure_computation |
| 00ec | functional_equations | source_recovery | keep_borderline | proof_corrupted, opaque_large_jump |
| 07km | inequalities | scope_clarification | keep_borderline | opaque_large_jump, scope_ambiguous |
| 0fxf | inequalities | source_recovery | keep_borderline | source_mojibake |
| 0h64 | polynomials | source_recovery | keep_borderline | proof_truncated, opaque_large_jump |
| 01xk | polynomials | source_recovery | keep_borderline | source_mojibake |
| 03rt | recurrences_sequences | source_recovery | keep_borderline | source_mojibake, proof_corrupted, opaque_large_jump |
| 03un | inequalities | source_recovery | keep_borderline | source_mojibake |
| 03xn | complex_algebra | source_recovery | keep_borderline | source_mojibake |
| 03sm | recurrences_sequences | scope_clarification | keep_borderline | opaque_large_jump, scope_ambiguous |
| 0agg | inequalities | source_recovery | keep_borderline | proof_corrupted, opaque_large_jump |
| 0g8l | functional_equations | source_recovery | keep_borderline | source_mojibake, complete_proof, clear_inference_units, traceable_dependencies, scope_clear, case_structure |
| 0h02 | inequalities | bounded_proof_repair | keep_borderline | opaque_large_jump, complete_proof, clear_inference_units, scope_clear, case_structure, multi_premise_merge |
| 0le5 | polynomials | bounded_proof_repair | keep_borderline | opaque_large_jump, scope_clear, case_structure |
| 02fr | functional_equations | bounded_proof_repair | keep_borderline | opaque_large_jump, scope_clear, case_structure |
| 0421 | inequalities | bounded_proof_repair | keep_borderline | opaque_large_jump, case_structure, multi_premise_merge |
