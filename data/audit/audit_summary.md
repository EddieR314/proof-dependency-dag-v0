# Audit Summary

- reviewed_samples: 59
- first_break_valid_rate: 1.000
- break_type_valid_rate: 1.000
- single_error_valid_rate: 0.983
- usable_as_gold_rate: 0.746
- average_naturalness_score: 3.644
- average_plausibility_before_break_score: 3.220
- average_post_break_consistency_score: 3.559

## Accuracy By Topic

| group | n | first_break | break_type | single_error | usable_as_gold |
|---|---:|---:|---:|---:|---:|
| algebra | 20 | 1.000 | 1.000 | 1.000 | 0.900 |
| combinatorics | 5 | 1.000 | 1.000 | 1.000 | 0.600 |
| geometry | 21 | 1.000 | 1.000 | 1.000 | 0.667 |
| number_theory | 13 | 1.000 | 1.000 | 0.923 | 0.692 |

## Accuracy By Error Type

| group | n | first_break | break_type | single_error | usable_as_gold |
|---|---:|---:|---:|---:|---:|
| case_overlap | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| circular_reasoning | 20 | 1.000 | 1.000 | 0.950 | 0.400 |
| diagram_assumption | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| domain_error | 3 | 1.000 | 1.000 | 1.000 | 0.667 |
| false_claim | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| invalid_wlog | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| missing_case | 3 | 1.000 | 1.000 | 1.000 | 0.667 |
| missing_dependency | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| overgeneralization | 3 | 1.000 | 1.000 | 1.000 | 0.667 |
| quantifier_error | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| sign_error | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| unproved_existence | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| wrong_dependency | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| wrong_theorem | 3 | 1.000 | 1.000 | 1.000 | 1.000 |

## Accuracy By Generator

| group | n | first_break | break_type | single_error | usable_as_gold |
|---|---:|---:|---:|---:|---:|
| generate_wrong_solutions.py | 59 | 1.000 | 1.000 | 0.983 | 0.746 |

## Corrected Break Types

_None._

## Failure Modes

- usable_as_gold:revise: 9
- usable_as_gold:no: 6
- reviewer_note:reject: first break/type are detectable, but the sample is too malformed and answer text is incomplete.: 1
- reviewer_note:needs revision: circular dependency is correct, but ocr fragments make the steps hard to audit cleanly.: 1
- reviewer_note:reject: circular dependency is detectable, but the generated proof contains irrelevant anecdotal material and is not gol: 1
- single_error_valid:no: 1
- reviewer_note:reject: the wrong solution is mostly an unverified computational assertion, so the injected dependency is not the only m: 1
- reviewer_note:needs revision: first break/type are correct, but long commentary and ocr artifacts reduce gold quality.: 1
- reviewer_note:needs revision: first break/type are correct, but mathematical text is heavily fragmented.: 1
- reviewer_note:reject: the injected overgeneralization sits in a meta-comment/source citation rather than a mathematical step.: 1
- reviewer_note:needs revision: circular dependency is valid but the selected spu is ocr-corrupted.: 1
- reviewer_note:reject: the selected break is a diagram aside/fractured sentence, not a clean mathematical spu.: 1
- reviewer_note:needs revision: missing case is plausible, but the very long dependency chain should be cleaned before silver use.: 1
- reviewer_note:reject: first break is just a remark marker, so the sample is not useful as gold despite the dependency metadata.: 1
- reviewer_note:needs revision: circular dependency is detectable, but the sample is too long/ocr-heavy for clean silver.: 1
- reviewer_note:needs revision: circular dependency is correct, but notation is too garbled for direct gold use.: 1
- reviewer_note:needs revision: domain error is identifiable, but the theorem statement is mangled and should be cleaned.: 1
- reviewer_note:needs revision: circular dependency is present, but first-break text is vague and proof needs cleanup.: 1
