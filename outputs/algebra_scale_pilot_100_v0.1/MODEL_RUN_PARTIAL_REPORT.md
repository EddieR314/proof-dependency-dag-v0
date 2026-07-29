# Model Run Partial Report

## Decision

The 100-problem proof-layer run is not complete and has not passed the
predeclared completion gate. The defensible result at this stage is 91 valid
predictions plus 9 pending retries.

## Frozen Provenance

| Artifact | SHA256 |
| --- | --- |
| Statements-only input | `dc5cc1f03cf7792022c0f5c37fbb7e15ac352c445aab678f31f12b4ad9bffa93` |
| Run configuration | `114c4545f956976c1f37cfb7b57b3fac8f8169f71fe49c5ffa6680a7d7b2e939` |
| Prediction schema | `bde04a9bbfddf6ca63893379592d92567729d7c1bab65eec5d7b0d7e4ab67259` |
| Model runner | `d76aebb55873fdbb99afe548b0aa29e9239014b9d78fd5d237f0e627a33f29bd` |
| Partial 91-row predictions | `16a97fee5eaab56b2f8733b6134c8bb8410e4425a8ac11595c2b1a4275c57947` |

## Completed Prediction Summary

| Field | Count |
| --- | ---: |
| Completed | 91 |
| Candidate proof `passed` | 72 |
| Candidate proof `blocked` | 19 |
| Candidate proof `failed` | 0 |
| Missing | 9 |

The labels above are model self-assessments constrained by the output state
machine. They are not human correctness judgments.

## Reviewed Primary Route Candidates

| Route | Count |
| --- | ---: |
| Functional equations | 23 |
| Inequalities | 29 |
| Polynomials | 19 |
| Recurrences and sequences | 13 |
| Complex algebra | 4 |
| Discrete algebra | 3 |

These are model route candidates, not gold labels.

## Failure Accounting

- `06y4` initially produced an internally inconsistent status and was rejected.
- The remaining missing calls encountered local transport or fallback failures.
- A later connectivity probe reported that the ChatGPT Codex usage limit had
  been reached and gave 2026-08-05 14:07 as the reset time.
- No missing prediction was synthesized, copied from a reference, or silently
  counted as completed.

## Audit Readiness

The preselected 30-record double-review sample currently contains 27 completed
predictions. The missing audit records are `0dg9`, `040g`, and `0et7`.
Reference opening and human scoring remain blocked until all 100 predictions
are frozen.

## Interpretation

This partial run validates the engineering pipeline at 91-record scale. It does
not establish proof accuracy, does not pass the >=98/100 completion target, and
does not justify expansion to 500 or 20,000 problems.
