import fs from "node:fs/promises";

const root = process.cwd();
const inputPath = `${root}/outputs/dag_suitability_screening/borderline_review_v0.1/borderline_triage_v0.1.jsonl`;
const outDir = `${root}/outputs/dag_suitability_screening/borderline_review_v0.2`;
const rows = (await fs.readFile(inputPath, "utf8")).split(/\r?\n/).filter(Boolean).map(JSON.parse);

const promoteAfterCleanup = new Set([
  "040g", "0fs7", "09s9", "0cud", "0etl", "07vf", "0get",
  "03wf", "0fxf", "01xk", "03un", "03xn", "0g8l",
]);
const downgrade = new Set(["0fm4", "08t2"]);

const reviewed = rows.map((row) => {
  let second_pass_decision = "keep_borderline";
  let second_pass_reason = "Requires bounded source, proof-gap, or scope repair before DAG construction.";
  if (promoteAfterCleanup.has(row.problem_id)) {
    second_pass_decision = "promote_after_cleanup";
    second_pass_reason = "The proof is complete and structurally traceable; the remaining defect is removable source noise or a discardable corrupted duplicate route.";
  } else if (downgrade.has(row.problem_id)) {
    second_pass_decision = "downgrade_unsuitable";
    second_pass_reason = row.problem_id === "0fm4"
      ? "Proof completeness and dependency explicitness are both scored 0; numerical examples replace the decisive general argument."
      : "The decisive classification is asserted as opaque computation, with dependency explicitness scored 0 and low DAG yield.";
  }
  return { ...row, second_pass_decision, second_pass_reason };
});

const count = (decision) => reviewed.filter((row) => row.second_pass_decision === decision).length;
const summary = {
  total_reviewed: reviewed.length,
  promote_after_cleanup: count("promote_after_cleanup"),
  keep_borderline: count("keep_borderline"),
  downgrade_unsuitable: count("downgrade_unsuitable"),
  important_metadata_corrections: [
    { problem_id: "05xg", issue: "notes report pervasive mojibake but reason_codes omit source_mojibake" },
    { problem_id: "0fm4", issue: "borderline conflicts with proof_completeness=0 and dependency_explicitness=0" },
  ],
};

await fs.mkdir(outDir, { recursive: true });
await fs.writeFile(`${outDir}/borderline_second_pass_v0.2.jsonl`, reviewed.map((row) => JSON.stringify(row)).join("\n") + "\n", "utf8");
await fs.writeFile(`${outDir}/borderline_second_pass_summary_v0.2.json`, JSON.stringify(summary, null, 2) + "\n", "utf8");

const ids = (decision) => reviewed.filter((row) => row.second_pass_decision === decision).map((row) => `\`${row.problem_id}\``).join(", ");
const report = `# Borderline second-pass review v0.2

## Outcome

- Total reviewed: ${reviewed.length}
- Promote after bounded cleanup: ${summary.promote_after_cleanup}
- Keep borderline pending real repair: ${summary.keep_borderline}
- Downgrade to unsuitable: ${summary.downgrade_unsuitable}

## Promote after cleanup

${ids("promote_after_cleanup")}

These records have complete proofs and traceable dependency structure. Their remaining problems are source mojibake, duplicated proof text, or a corrupted route that can be removed while retaining another self-contained route. Promotion is conditional on actually producing a cleaned source record and verifying its hash.

## Keep borderline

${ids("keep_borderline")}

These records still require a mathematical repair: expand an omitted inference, resolve an unavailable reference, clarify case or quantifier scope, or reconcile an internal inconsistency. They should not enter Reference DAG construction yet.

## Downgrade to unsuitable

${ids("downgrade_unsuitable")}

- \`0fm4\`: the decisive general exclusion is absent; examples are used instead. This conflicts with the rubric because proof completeness and dependency explicitness are both 0.
- \`08t2\`: the decisive enumeration is treated as an opaque computation, dependency explicitness is 0, and the record offers little useful DAG structure.

## Metadata corrections

- \`05xg\`: add \`source_mojibake\` and \`recover_source\`; the existing note already says mojibake is pervasive.
- \`0fm4\`: remove \`clean_linear_proof\`; it contradicts the missing decisive argument.

## Interpretation

This is a source-suitability review, not a proof-correctness certificate. A record marked \`promote_after_cleanup\` becomes \`suitable\` only after the cleaned proof is saved and checked. A record remaining \`borderline\` is not approved for automatic DAG construction.
`;
await fs.writeFile(`${outDir}/borderline_second_pass_report_v0.2.md`, report, "utf8");
console.log(JSON.stringify(summary, null, 2));
