# 00q2 Controlled Mutation Review

## Mutation

- Operation: remove required premise edge `F6 -> I5`
- Intended First Break: `I5`
- Error type: `missing_dependency`
- Target effect: `target_breaking`
- Human decision: pending

## Review

- [ ] The Reference DAG is mathematically valid before mutation.
- [ ] Exactly one primary graph intervention occurs.
- [ ] Removing `F6` leaves `I5` without the fact that `f_n` has distinct
      extreme homogeneous components of degrees `2` and `2n`.
- [ ] The remaining claim at `I5` is not justified merely by
      `g_n=f_n h` and the existence of extreme pieces of `h`.
- [ ] This models the realistic shortcut “a divisor of a homogeneous
      polynomial is homogeneous” or an equivalent omitted extreme-degree
      argument.
- [ ] Computed First Break is `I5`.
- [ ] Later blocked steps are propagation, not additional injected errors.
- [ ] The independent `n=1` sufficiency branch remains executable.

## Sign-Off

- Reviewer:
- Date:
- Decision: `pending`
- Notes:
