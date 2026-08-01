import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "../..");
const INPUT = path.join(ROOT, "data/dag_suitability_screening/prepared_algebra_v0.1.jsonl");
const OUTPUT_DIR = path.join(
  ROOT,
  "outputs/dag_suitability_screening/borderline_cleanup_v0.1",
);

const TARGET_IDS = [
  "040g", "0fs7", "09s9", "0cud", "0etl", "07vf", "0get",
  "03wf", "0fxf", "01xk", "03un", "03xn", "0g8l",
];

const LANGUAGES = {
  "0fs7": "de",
  "09s9": "nl",
  "0fxf": "de",
};

function sha256(text) {
  return crypto.createHash("sha256").update(text, "utf8").digest("hex");
}

function readJsonl(file) {
  return fs.readFileSync(file, "utf8").trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
}

function secondOccurrence(text, marker) {
  const first = text.indexOf(marker);
  if (first < 0) throw new Error(`Missing marker: ${marker}`);
  const second = text.indexOf(marker, first + marker.length);
  if (second < 0) throw new Error(`Missing second marker: ${marker}`);
  return second;
}

function cutBefore(text, marker) {
  const index = text.indexOf(marker);
  if (index < 0) throw new Error(`Missing marker: ${marker}`);
  return text.slice(0, index).trim();
}

function cutThrough(text, marker) {
  const index = text.indexOf(marker);
  if (index < 0) throw new Error(`Missing marker: ${marker}`);
  return text.slice(0, index + marker.length).trim();
}

function replaceExact(text, from, to) {
  if (!text.includes(from)) throw new Error(`Missing replacement source: ${from}`);
  return text.replace(from, to);
}

function clean(record) {
  let solution = record.solution;
  const transformations = [];

  switch (record.problem_id) {
    case "040g":
      solution = cutThrough(solution, "The proof is complete.");
      transformations.push("Removed a duplicated proof copy after the first complete proof.");
      break;
    case "0fs7": {
      solution = solution.slice(0, secondOccurrence(solution, "Solution:")).trim();
      const preamble = "Es gibt sehr viele Wege, diese Ungleichung zu beweisen. Wir geben 10 verschiedene Lösungen als Auswahl. ";
      solution = replaceExact(solution, preamble, "");
      transformations.push("Retained the first complete German solution and removed nine alternatives.");
      transformations.push("Adjusted the multi-solution preamble to match the retained single route.");
      break;
    }
    case "09s9":
      solution = cutBefore(solution, "Oplossing II.");
      transformations.push("Retained the first complete Dutch solution and removed later alternatives.");
      break;
    case "0cud":
      solution = cutBefore(solution, "Ответ.");
      transformations.push("Retained the complete English proof and removed the duplicated Russian route.");
      break;
    case "0etl":
      transformations.push("No content change; prior source-corruption flag was a false positive.");
      break;
    case "07vf": {
      const marker = "The key observation is that two numbers are determined by their product and sum.";
      const index = solution.indexOf(marker);
      if (index < 0) throw new Error(`Missing marker: ${marker}`);
      solution = `Solution.\n${solution.slice(index).trim()}`;
      transformations.push("Removed the earlier matrix-placeholder route and retained the later self-contained route.");
      break;
    }
    case "0get":
      solution = cutBefore(solution, "**Solution 2.**");
      transformations.push("Retained Solution 1 and removed two alternative solutions.");
      break;
    case "03wf":
      solution = replaceExact(solution, "\\qquad \\textcircled{1}", "\\qquad \\tag{1}");
      if (!solution.includes("inequality ①")) throw new Error("03wf: missing circled equation reference.");
      solution = solution.replaceAll("inequality ①", "inequality (1)");
      transformations.push("Normalized the mixed equation label to LaTeX tag (1).");
      break;
    case "0fxf":
      solution = solution.slice(0, secondOccurrence(solution, "Solution:")).trim();
      transformations.push("Retained the first complete German solution and removed three alternatives.");
      break;
    case "01xk":
      solution = replaceExact(
        solution,
        "the two remaining variants $x = 0$ and $x = 1$ easily lead us to the triples from the answer.",
        "the two remaining variants $x = 0$ and $x = -1$ easily lead us to the triples from the answer.",
      );
      transformations.push("Corrected the final unambiguous typo x=1 to x=-1, consistent with the stated answer and preceding derivation.");
      break;
    case "03un":
      solution = cutThrough(solution, "So the problem is proved.");
      transformations.push("Retained the first complete proof and removed the alternative route.");
      break;
    case "03xn":
      for (let i = 1; i <= 6; i += 1) {
        solution = solution.replaceAll(`\\textcircled{${i}}`, `\\tag{${i}}`);
      }
      for (const [symbol, label] of [["①", "(1)"], ["②", "(2)"], ["③", "(3)"], ["④", "(4)"], ["⑤", "(5)"], ["⑥", "(6)"]]) {
        solution = solution.replaceAll(symbol, label);
      }
      transformations.push("Normalized mixed circled equation labels to LaTeX tags and ASCII prose references.");
      break;
    case "0g8l":
      transformations.push("No content change; prior source-corruption flag was a false positive.");
      break;
    default:
      throw new Error(`Unexpected target: ${record.problem_id}`);
  }

  const contentChanged = solution !== record.solution;
  return {
    problem_id: record.problem_id,
    source_index: record.source_index,
    source: record.source,
    domain: record.domain,
    candidate_algebra_module: record.candidate_algebra_module,
    source_language: LANGUAGES[record.problem_id] ?? "en",
    statement: record.statement,
    solution,
    source_provenance: {
      original_record_ref: path.relative(ROOT, INPUT).replaceAll("\\", "/"),
      original_statement_sha256: sha256(record.statement),
      original_solution_sha256: sha256(record.solution),
      cleaned_statement_sha256: sha256(record.statement),
      cleaned_solution_sha256: sha256(solution),
      content_changed: contentChanged,
      transformations,
    },
    screening_status: {
      source_gate: "cleaned_and_machine_validated",
      proposed_decision: "suitable",
      mathematical_review: "not_changed_by_cleanup",
      dag_semantic_review: "not_started",
    },
  };
}

function validate(originalById, cleaned) {
  const errors = [];
  if (cleaned.length !== TARGET_IDS.length) errors.push(`Expected 13 records, got ${cleaned.length}.`);
  if (new Set(cleaned.map((x) => x.problem_id)).size !== cleaned.length) errors.push("Duplicate problem_id found.");

  for (const row of cleaned) {
    const original = originalById.get(row.problem_id);
    if (!original) errors.push(`${row.problem_id}: original record missing.`);
    if (!row.statement.trim() || !row.solution.trim()) errors.push(`${row.problem_id}: empty statement or solution.`);
    if (row.source_provenance.original_solution_sha256 !== sha256(original.solution)) {
      errors.push(`${row.problem_id}: original solution hash mismatch.`);
    }
    if (row.source_provenance.cleaned_solution_sha256 !== sha256(row.solution)) {
      errors.push(`${row.problem_id}: cleaned solution hash mismatch.`);
    }
    for (const bad of ["????", "�", "①", "②", "③", "④", "⑤", "⑥", "\\textcircled{"]) {
      if (row.solution.includes(bad)) errors.push(`${row.problem_id}: residual placeholder ${JSON.stringify(bad)}.`);
    }
  }

  const expectedUnchanged = new Set(["0etl", "0g8l"]);
  for (const row of cleaned) {
    if (expectedUnchanged.has(row.problem_id) === row.source_provenance.content_changed) {
      errors.push(`${row.problem_id}: unexpected content_changed state.`);
    }
  }
  return errors;
}

const rows = readJsonl(INPUT);
const byId = new Map(rows.map((row) => [row.problem_id, row]));
for (const id of TARGET_IDS) {
  if (!byId.has(id)) throw new Error(`Target record not found: ${id}`);
}

const cleaned = TARGET_IDS.map((id) => clean(byId.get(id)));
const validationErrors = validate(byId, cleaned);
if (validationErrors.length) throw new Error(`Validation failed:\n${validationErrors.join("\n")}`);

fs.mkdirSync(OUTPUT_DIR, { recursive: true });
const jsonlPath = path.join(OUTPUT_DIR, "cleaned_promotable_borderlines_v0.1.jsonl");
const manifestPath = path.join(OUTPUT_DIR, "cleanup_manifest_v0.1.json");
const reportPath = path.join(OUTPUT_DIR, "cleanup_report_v0.1.md");

fs.writeFileSync(jsonlPath, `${cleaned.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");

const changed = cleaned.filter((row) => row.source_provenance.content_changed).length;
const manifest = {
  version: "borderline-cleanup-v0.1",
  input: path.relative(ROOT, INPUT).replaceAll("\\", "/"),
  output: path.relative(ROOT, jsonlPath).replaceAll("\\", "/"),
  record_count: cleaned.length,
  content_changed_count: changed,
  unchanged_false_positive_count: cleaned.length - changed,
  post_second_pass_screening_counts: {
    suitable: 186,
    borderline: 44,
    unsuitable: 20,
    total: 250,
    derivation: "173/59/18 before second pass; 13 promoted after cleanup, 44 retained borderline, and 2 downgraded.",
  },
  validation: {
    passed: true,
    checks: [
      "target IDs unique and complete",
      "statement and solution nonempty",
      "original and cleaned SHA-256 hashes consistent",
      "no residual ???? or Unicode replacement-character placeholders",
      "expected changed/unchanged records match the cleanup plan",
    ],
  },
  boundary: "Source cleanup only; it does not certify proof correctness or DAG semantics.",
  records: cleaned.map((row) => ({
    problem_id: row.problem_id,
    source_language: row.source_language,
    content_changed: row.source_provenance.content_changed,
    original_solution_sha256: row.source_provenance.original_solution_sha256,
    cleaned_solution_sha256: row.source_provenance.cleaned_solution_sha256,
    transformations: row.source_provenance.transformations,
  })),
};
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

const lines = [
  "# Borderline Source Cleanup Report v0.1",
  "",
  `- Input records: ${cleaned.length}`,
  `- Content changed: ${changed}`,
  `- Unchanged false-positive flags: ${cleaned.length - changed}`,
  "- Machine validation: passed",
  "- Updated 250-record screening counts: 186 suitable / 44 borderline / 20 unsuitable",
  "- Boundary: source cleanup only; mathematical correctness and DAG semantics are not promoted here.",
  "",
  "| Problem | Language | Changed | Cleanup |",
  "|---|---:|---:|---|",
  ...cleaned.map((row) => `| ${row.problem_id} | ${row.source_language} | ${row.source_provenance.content_changed ? "yes" : "no"} | ${row.source_provenance.transformations.join(" ")} |`),
  "",
  "## Promotion Recommendation",
  "",
  "All 13 records now pass the bounded source-integrity gate and may enter the next DAG-suitability stage. This recommendation does not replace mathematical proof review, Fact-Inference decomposition, or DAG semantic review.",
  "",
];
fs.writeFileSync(reportPath, lines.join("\n"), "utf8");

console.log(JSON.stringify({ jsonlPath, manifestPath, reportPath, recordCount: cleaned.length, changed }, null, 2));
