# Borderline second-pass review v0.2

## Outcome

- Total reviewed: 59
- Promote after bounded cleanup: 13
- Keep borderline pending real repair: 44
- Downgrade to unsuitable: 2

## Promote after cleanup

`040g`, `0fs7`, `09s9`, `0cud`, `0etl`, `07vf`, `0get`, `03wf`, `0fxf`, `01xk`, `03un`, `03xn`, `0g8l`

These records have complete proofs and traceable dependency structure. Their remaining problems are source mojibake, duplicated proof text, or a corrupted route that can be removed while retaining another self-contained route. Promotion is conditional on actually producing a cleaned source record and verifying its hash.

## Keep borderline

`042l`, `05xg`, `07e6`, `02m4`, `0cht`, `046v`, `0483`, `0gji`, `046d`, `06wc`, `03wa`, `07et`, `09kg`, `00c4`, `01st`, `03y0`, `03z3`, `0hi8`, `04bk`, `01ik`, `0le3`, `0601`, `09vy`, `0ggr`, `06ur`, `0esd`, `0evc`, `0lfb`, `04yf`, `07qs`, `099e`, `0hht`, `0l9j`, `00he`, `00ec`, `07km`, `0h64`, `03rt`, `03sm`, `0agg`, `0h02`, `0le5`, `02fr`, `0421`

These records still require a mathematical repair: expand an omitted inference, resolve an unavailable reference, clarify case or quantifier scope, or reconcile an internal inconsistency. They should not enter Reference DAG construction yet.

## Downgrade to unsuitable

`0fm4`, `08t2`

- `0fm4`: the decisive general exclusion is absent; examples are used instead. This conflicts with the rubric because proof completeness and dependency explicitness are both 0.
- `08t2`: the decisive enumeration is treated as an opaque computation, dependency explicitness is 0, and the record offers little useful DAG structure.

## Metadata corrections

- `05xg`: add `source_mojibake` and `recover_source`; the existing note already says mojibake is pervasive.
- `0fm4`: remove `clean_linear_proof`; it contradicts the missing decisive argument.

## Interpretation

This is a source-suitability review, not a proof-correctness certificate. A record marked `promote_after_cleanup` becomes `suitable` only after the cleaned proof is saved and checked. A record remaining `borderline` is not approved for automatic DAG construction.
