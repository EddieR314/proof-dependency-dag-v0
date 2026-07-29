# Current Status

## Frozen Setup

- The deterministic 100-problem statements-only sample is frozen.
- Calibration and earlier heldout IDs and normalized hashes are excluded.
- The frozen Skill is `olympiad-algebra-expert-v0.2`.
- The model-run protocol is fixed at prompt
  `scale-pilot-proof-v0.3-state-machine`.
- The model configuration is `gpt-5.6-terra`, medium reasoning, priority
  service tier, read-only sandbox, and no reference access.
- Thirty audit problems were selected before predictions were generated.

## Partial Model Run

- Completed predictions: 91/100.
- Candidate proof status among completed predictions:
  - `passed`: 72
  - `blocked`: 19
  - `failed`: 0
- All 91 stored predictions pass the output schema, ASCII, identity, and
  component-state checks.
- Partial predictions SHA256:
  `16a97fee5eaab56b2f8733b6134c8bb8410e4425a8ac11595c2b1a4275c57947`
- The run stopped because the ChatGPT Codex usage limit was reached. The
  client reported that usage becomes available again at 2026-08-05 14:07.

## Pending Retry

Nine records remain incomplete:

`06y4`, `06qx`, `046d`, `00ht`, `06p9`, `0dg9`, `040g`, `04v7`, `0et7`.

Resume with the same model, prompt, schema, and output directory. The runner
will skip the 91 completed records and attempt only the missing records.

## Reference and Human Review State

- No reference solution has been opened for this 100-problem sample.
- Of the 30 preselected audit records, 27 have predictions and 3 are in the
  pending retry list.
- Human review must not start until the 100-row prediction file is complete,
  validated, and re-hashed.
- No downstream 12-problem DAG sample or 3-problem Lean sample has been
  selected.

## Next Command

After usage is restored:

```powershell
python scripts\run_algebra_scale_predictions.py `
  --statements outputs\algebra_scale_pilot_100_v0.1\statements_only.jsonl `
  --config outputs\algebra_scale_pilot_100_v0.1\run_config.json `
  --schema outputs\algebra_scale_pilot_100_v0.1\prediction.schema.json `
  --output-dir outputs\algebra_scale_pilot_100_v0.1\model_run_v0.3 `
  --count 100 --concurrency 1
```

Do not change the Skill or open references before this retry completes.
