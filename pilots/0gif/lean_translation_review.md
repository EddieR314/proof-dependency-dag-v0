# 0gif Lean Translation Human Review

## Artifact

- Problem ID: `0gif`
- Reference graph: `0gif-reference-v0.1`
- Lean source: `ProofDag0gif/Basic.lean`
- Formal mapping: `formal_mapping.json`
- Automatic build: passed
- Mapping coverage: 18/18 Inferences
- Human decision: passed

## Domain and Main Statement

- [x] `Satisfies` restricts all hypotheses to positive real inputs and requires
      positive outputs.
- [x] The encoded inequality is exactly
      `(f(f(x)) + y) f(y) <= x (f(x) + f(y))`.
- [x] `all_solutions` states necessity and sufficiency of
      `f(x) = c/x` with `c > 0`.

## Necessity Route

| Check | DAG output | Lean declaration |
| --- | --- | --- |
| [x] | `I1 -> F6`: every orbit term is positive | `positive_forward_orbit` |
| [x] | `I2 -> F7`: `f(f(x)) <= x` | `two_step_descent` |
| [x] | `I3 -> F8`: `x_(n+2) <= x_n` | `iterate_two_step_descent` |
| [x] | `I4 -> F9`: adjacent-orbit inequality | `adjacent_drop_comparison` |
| [x] | `I5 -> F10`: `0 <= d_n` | `drops_nonnegative` |
| [x] | `I6 -> F11`: `d_n <= d_(n+1)` | `drops_nondecreasing` |
| [x] | `I7 -> F12`: even-index telescoping | `even_telescoping` |
| [x] | `I8 -> F13`: bounded even-index drop sums | `even_drop_sum_bound` |
| [x] | `I9 -> F14`: every `d_n` vanishes | `monotone_drops_vanish` |
| [x] | `I10 -> F15`: `f(f(x)) = x` | `composition_identity` |
| [x] | `I11 -> F16`: `x f(x) >= y f(y)` | `product_order` |
| [x] | `I12 -> F17`: reverse product inequality | `reverse_product_order` |
| [x] | `I13 -> F18`: `x f(x) = y f(y)` | `product_constant` |
| [x] | `I14 -> F19`: `f(x)=c/x`, `c>0` | `reciprocal_necessity` |

`I7` and `I8` are stated in the DAG for `N>=1`; Lean proves the harmless
stronger statements for every natural `N`, including `N=0`.

## Sufficiency Route

| Check | DAG output | Lean declaration |
| --- | --- | --- |
| [x] | `I15 -> F20`: `c/x` is positive | `candidate_positive` |
| [x] | `I16 -> F21`: `g_c(g_c(x))=x` | `candidate_involution` |
| [x] | `I17 -> F22`: candidate satisfies the original condition | `candidate_satisfies` |
| [x] | `I18 -> F23`: exact classification | `all_solutions` |

## Formal Hygiene

- [x] Every mapped declaration has the intended quantifiers and premise roles.
- [x] No DAG Fact is strengthened or weakened in a way that changes later use.
- [x] No division or multiplication cancellation omits positivity/nonzero
      conditions.
- [x] No `sorry` or `admit` occurs.

## Sign-Off

- Reviewer: Ruan Haochen (Eddie)
- Date: 2026-07-28
- Decision: `passed`
- Notes: Natural-language statements, DAG outputs, premise roles, quantifiers,
  positivity conditions, and all 18 mapped Lean declarations were reviewed
  with no semantic mismatch found.
