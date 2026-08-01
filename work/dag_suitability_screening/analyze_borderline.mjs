import fs from "node:fs/promises";

const root = process.cwd();
const paths = {
  calibration: `${root}/outputs/dag_suitability_screening/calibration_human_reviewed_v0.1.jsonl`,
  expansion: `${root}/outputs/dag_suitability_screening/expansion_v0.1/expansion_predictions_v0.1.jsonl`,
  source: `${root}/data/dag_suitability_screening/prepared_algebra_v0.1.jsonl`,
};

const readJsonl = async (path) => (await fs.readFile(path, "utf8"))
  .split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));

const [calibration, expansion, sourceRows] = await Promise.all([
  readJsonl(paths.calibration), readJsonl(paths.expansion), readJsonl(paths.source),
]);
const sourceById = new Map(sourceRows.map((row) => [row.problem_id, row]));

const selected = [];
for (const row of calibration) {
  const reviewedDecision = row.human_decision ?? row.decision;
  if (reviewedDecision === "borderline") selected.push({ ...row, set: "calibration", reviewed_decision: reviewedDecision });
}
for (const row of expansion) {
  if (row.decision === "borderline") selected.push({ ...row, set: "expansion", reviewed_decision: row.decision });
}

const hasAny = (codes, options) => options.some((code) => codes.includes(code));
const sourceCodes = ["proof_corrupted", "proof_truncated", "source_mojibake", "excessive_repetition"];
const gapCodes = ["opaque_large_jump", "unresolved_reference"];
const scopeCodes = ["scope_ambiguous"];
const poorStructureCodes = ["pure_computation", "too_short_for_dag", "too_long_unstructured"];

const triage = selected.map((row) => {
  const codes = row.reason_codes ?? [];
  const repairs = row.repair_actions ?? [];
  const source = sourceById.get(row.problem_id) ?? {};
  let bucket = "bounded_proof_repair";
  let recommendation = "keep_borderline";
  let nextAction = "Expand the omitted inference or resolve the named reference, then re-screen.";

  const hardFailure = row.input_quality?.proof_integrity === "corrupt"
    || row.scores?.source_integrity === 0
    || row.scores?.proof_completeness === 0;
  if (hardFailure) {
    bucket = "hard_source_failure";
    recommendation = "downgrade_unsuitable";
    nextAction = "Reject this copy; recover a clean source before any DAG work.";
  } else if (hasAny(codes, sourceCodes)) {
    bucket = "source_recovery";
    nextAction = "Clean or recover the source, then verify that no mathematical step was lost.";
  } else if (hasAny(codes, scopeCodes)) {
    bucket = "scope_clarification";
    nextAction = "Make cases, quantifiers, or local assumptions explicit before DAG construction.";
  } else if (hasAny(codes, poorStructureCodes)) {
    bucket = "low_dag_yield";
    nextAction = "Use only if module coverage is needed; otherwise deprioritize this record.";
  } else if (hasAny(codes, gapCodes)) {
    bucket = "bounded_proof_repair";
  } else if (Object.values(row.scores ?? {}).every((score) => score === 2)) {
    bucket = "promotion_candidate";
    recommendation = "promote_suitable_after_spot_check";
    nextAction = "One final proof-level spot check; no source repair appears necessary.";
  }

  return {
    problem_id: row.problem_id,
    set: row.set,
    algebra_module: row.human_algebra_module ?? row.algebra_module,
    confidence: row.confidence,
    reason_codes: codes,
    repair_actions: repairs,
    scores: row.scores,
    proof_integrity: row.input_quality?.proof_integrity,
    estimated_inference_count: row.estimated_inference_count,
    second_stage_bucket: bucket,
    recommendation,
    next_action: nextAction,
    statement: source.statement ?? "",
    solution: source.solution ?? "",
    original_notes: row.notes ?? "",
  };
});

const countBy = (key) => Object.fromEntries([...triage.reduce((map, row) => {
  const value = row[key]; map.set(value, (map.get(value) ?? 0) + 1); return map;
}, new Map()).entries()].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]))));

const reasonCounts = {};
for (const row of triage) for (const code of row.reason_codes) reasonCounts[code] = (reasonCounts[code] ?? 0) + 1;
const summary = {
  total_borderline: triage.length,
  by_set: countBy("set"),
  by_module: countBy("algebra_module"),
  by_bucket: countBy("second_stage_bucket"),
  by_recommendation: countBy("recommendation"),
  reason_counts: Object.fromEntries(Object.entries(reasonCounts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))),
};

const outDir = `${root}/outputs/dag_suitability_screening/borderline_review_v0.1`;
await fs.mkdir(outDir, { recursive: true });
await fs.writeFile(`${outDir}/borderline_triage_v0.1.jsonl`, triage.map((row) => JSON.stringify(row)).join("\n") + "\n", "utf8");
await fs.writeFile(`${outDir}/borderline_triage_summary_v0.1.json`, JSON.stringify(summary, null, 2) + "\n", "utf8");

const lines = [
  "# Borderline second-stage triage v0.1", "", `Total: ${summary.total_borderline}`, "",
  "## Buckets", "",
  ...Object.entries(summary.by_bucket).map(([name, count]) => `- ${name}: ${count}`), "",
  "## Recommendations", "",
  ...Object.entries(summary.by_recommendation).map(([name, count]) => `- ${name}: ${count}`), "",
  "## Records", "",
  "| ID | Module | Bucket | Recommendation | Reasons |", "| --- | --- | --- | --- | --- |",
  ...triage.map((row) => `| ${row.problem_id} | ${row.algebra_module} | ${row.second_stage_bucket} | ${row.recommendation} | ${row.reason_codes.join(", ")} |`), "",
];
await fs.writeFile(`${outDir}/borderline_triage_report_v0.1.md`, lines.join("\n"), "utf8");
console.log(JSON.stringify(summary, null, 2));
