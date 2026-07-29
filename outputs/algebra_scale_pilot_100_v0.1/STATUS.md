# Current Status

## Completed

- Deterministic 100-problem sample selected from a 200-problem candidate pool.
- Old calibration and heldout IDs and normalized hashes excluded.
- Statements-only input frozen with no solution or final-answer fields.
- Module quotas and source diversity recorded.
- Thirty audit problems preselected, five per source bucket.
- Independent reviewer A and reviewer B templates created.
- Prediction validator and audit scorer implemented and tested.
- Pilot gates and model output contract frozen.

## Not Yet Run

- The 100 model predictions are still `not_run`.
- No reference solution has been opened for this 100-problem sample.
- The 30 human reviews have not started.
- The downstream 12 DAG and 3 Lean samples have not been selected.

## Required Run Configuration

Before prediction generation, record:

- model and exact version;
- system and user prompt versions;
- temperature or reasoning setting;
- random seed where supported;
- retry policy;
- concurrency;
- token and monetary budget;
- run timestamp and operator.

The completed predictions must be validated and hashed before any reference is
opened.
