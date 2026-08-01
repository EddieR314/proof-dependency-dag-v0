# Algebra DAG Screening Task

Read each prepared algebra record independently. Inspect the statement, supplied solution, and machine prefilter flags. Apply `suitability-rubric.md` and return one compact JSON object per record conforming to `screening-schema.json`.

Do not solve the problem from scratch, silently repair the proof, or infer that a polished answer is correct. Judge whether the supplied proof can be normalized into a faithful Fact-Inference DAG. Route by the proof mechanism, not merely by the source domain label. Keep `human_review_status` equal to `not_reviewed`.

Important checks:

1. Is the statement readable and self-contained?
2. Is the supplied text a proof rather than an answer or commentary?
3. Can it be separated into atomic propositions and identifiable rule applications without inventing missing mathematics?
4. Can local assumptions, cases, quantifiers, and conclusions be scoped?
5. Are dependencies traceable enough for later human correction?
6. Is any missing image or external reference essential?

Do not reject a clean proof merely because it is linear or difficult to formalize in Lean.

