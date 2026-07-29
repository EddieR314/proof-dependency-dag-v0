#!/usr/bin/env python3
"""Record the 2026-07-28 human adjudication of 13 algebra proofs."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REVIEWER = "Ruan Haochen (Eddie)"
REVIEW_DATE = "2026-07-28"
PASSED = {"0chi", "00q2", "06od", "0le0", "0gif", "06og", "01xk", "0ldq", "042l"}
NEEDS_REVISION = {"08x4", "03un", "03xn", "03rt"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    data = root / "data" / "algebra_skill_curriculum"
    results_path = data / "human_review_13_results_v0.1.csv"
    results = read_csv(results_path)

    ids = {row["problem_id"] for row in results}
    expected = PASSED | NEEDS_REVISION
    if ids != expected:
        raise ValueError(
            f"adjudication coverage mismatch: missing={sorted(ids - expected)}, "
            f"stale={sorted(expected - ids)}"
        )

    for row in results:
        problem_id = row["problem_id"]
        row["reviewer"] = REVIEWER
        row["review_date"] = REVIEW_DATE
        if problem_id in PASSED:
            for field in (
                "statement_correct",
                "reference_proof_correct",
                "blind_proof_correct",
                "route_correct",
                "pattern_correct",
                "risk_flags_correct",
                "spu_reasonable",
            ):
                row[field] = "yes"
            row["decision"] = "passed"
            row["notes"] = (
                "Natural-language proof and proposed proof mechanism accepted "
                "in the submitted deep-review report."
            )
        else:
            row["decision"] = "needs_revision"
            row["blind_proof_correct"] = "not_reviewable"
            row["notes"] = (
                "Original blind-draft body is missing. Restore it or run a new "
                "versioned blind generation before mathematical adjudication."
            )

    write_csv(results_path, results)

    source_rows = read_csv(data / "calibration_reviewed_v0.2.csv")
    output_rows = []
    result_by_id = {row["problem_id"]: row for row in results}
    for row in source_rows:
        result = result_by_id[row["problem_id"]]
        updated = dict(row)
        updated["proof_review_status"] = result["decision"]
        updated["proof_review_method"] = "human"
        updated["proof_reviewer"] = result["reviewer"]
        updated["proof_review_date"] = result["review_date"]
        updated["proof_review_notes"] = result["notes"]
        output_rows.append(updated)

    write_csv(data / "calibration_human_reviewed_v0.3.csv", output_rows)
    write_jsonl(data / "calibration_human_reviewed_v0.3.jsonl", output_rows)

    summary = {
        "reviewer": REVIEWER,
        "review_date": REVIEW_DATE,
        "scope": "natural_language_proof_layer",
        "counts": {
            "passed": len(PASSED),
            "needs_revision": len(NEEDS_REVISION),
        },
        "passed": sorted(PASSED),
        "needs_revision": sorted(NEEDS_REVISION),
        "text_integrity": {
            "0gif": (
                "The bilingual statement contains valid Traditional Chinese "
                "code points; no source-text cleaning was required."
            )
        },
        "not_implied": [
            "Fact-Inference DAG passed",
            "controlled mutation passed",
            "First Break passed",
            "Lean mapping or build passed",
        ],
    }
    (data / "human_review_13_summary_v0.1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
