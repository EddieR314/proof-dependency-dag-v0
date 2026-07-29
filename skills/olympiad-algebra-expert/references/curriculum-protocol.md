# Curriculum Protocol

## Source Gate

Select records whose proof domain is algebra, whose statement and solution are
present, and whose source is traceable. Exclude image-dependent records for the
text-first calibration stage.

## Deduplication

Group by `normalized_hash`; fall back to `problem_id` only when the hash is
missing. Keep one canonical record and preserve alternate-source metadata.
Never place duplicate hashes across calibration, expansion, and held-out sets.

## Splits

- **Calibration**: small, balanced, manually reviewed set used to discover
  patterns and revise the Skill.
- **Expansion**: broader set used after the module workflow stabilizes.
- **Held-out**: untouched problems used only for forward testing.

Balance six modules: functional equations, inequalities, polynomials,
recurrences/sequences, complex algebra, and discrete algebra. Limit repeated
competition sources inside each module.

## Per-Problem Evidence

Record:

- source and normalized hash;
- primary/secondary module;
- proof-review status;
- discovered proof pattern;
- discovered failure mode;
- proposed SPUs and Rule Schemas;
- formalization coverage and blockers;
- per-component verification results.

Do not promote a module from a count of generated artifacts alone.
