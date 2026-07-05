#!/usr/bin/env python3
"""Repair reviewed wrong-solution samples that were marked needs_revision."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ERROR_GENERATOR = ROOT.parent / "error-generator"
sys.path.insert(0, str(ERROR_GENERATOR))

from dag_build import edges_from_spus  # noqa: E402
from wrong_solution_writer import write_wrong_solution, write_wrong_solution_steps  # noqa: E402

try:
    from spu_quality import clean_or_drop_spu, normalize_spu_text, quality_issues  # type: ignore  # noqa: E402
except ModuleNotFoundError:
    def normalize_spu_text(text: str) -> str:
        return " ".join(str(text).split())

    def quality_issues(spu: dict[str, Any], target_context: bool = False) -> list[str]:
        text = normalize_spu_text(str(spu.get("text", "")))
        issues: list[str] = []
        if not text:
            issues.append("empty_spu_text")
        if "cid:" in text.lower() or "\ufffd" in text:
            issues.append("malformed_or_cid_text")
        if not target_context and text.lower().startswith(("source:", "note:", "remark:")):
            issues.append("commentary_or_source_note")
        return issues

    def clean_or_drop_spu(spu: dict[str, Any]) -> dict[str, Any] | None:
        cleaned = copy.deepcopy(spu)
        cleaned["text"] = normalize_spu_text(str(cleaned.get("text", "")))
        issues = quality_issues(cleaned)
        if "empty_spu_text" in issues or "commentary_or_source_note" in issues:
            return None
        return cleaned


PRESERVE_FIELDS = {
    "sample_id",
    "problem_id",
    "topic",
    "problem",
    "correct_solution",
    "injected_error",
    "generated_first_break",
    "human_corrected_first_break",
    "human_review",
    "review_status",
    "reviewer_id",
    "reviewed_at",
    "label_status",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Bad JSON on line {line_no}: {exc}") from exc
    return records


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def repair_record(record: dict[str, Any]) -> dict[str, Any]:
    repaired = copy.deepcopy(record)
    wrong_spus = repaired.get("wrong_spus", [])
    if not isinstance(wrong_spus, list):
        wrong_spus = []

    first_break_id = _first_break_id(repaired)
    cleaned_spus: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for spu in wrong_spus:
        if not isinstance(spu, dict):
            continue
        original_id = spu.get("id")
        cleaned = clean_or_drop_spu(spu)
        if cleaned is None:
            removed.append(
                {
                    "spu_id": original_id,
                    "issues": quality_issues(spu, target_context=False),
                    "text": str(spu.get("text", ""))[:160],
                }
            )
            continue
        cleaned_spus.append(cleaned)

    kept_ids = {
        str(spu["id"])
        for spu in cleaned_spus
        if isinstance(spu, dict) and spu.get("id") is not None
    }
    for cleaned in cleaned_spus:
        cleaned["depends_on"] = [
            dep
            for dep in cleaned.get("depends_on", [])
            if dep in kept_ids
            or dep in {"problem", "given", "definition"}
            or str(dep).startswith("external:")
        ]

    if not cleaned_spus:
        repaired["repair_status"] = "needs_manual_review"
        repaired["repair_notes"] = ["all_wrong_spus_removed_by_quality_filter"]
        return repaired

    repaired["wrong_spus"] = cleaned_spus
    repaired["wrong_edges"] = edges_from_spus(cleaned_spus)
    repaired["wrong_solution"] = write_wrong_solution(repaired.get("problem", ""), cleaned_spus)
    repaired["wrong_solution_steps"] = write_wrong_solution_steps(cleaned_spus)

    if "correct_spus" in repaired and isinstance(repaired["correct_spus"], list):
        repaired["correct_spus"] = [
            cleaned
            for spu in repaired["correct_spus"]
            if isinstance(spu, dict)
            for cleaned in [clean_or_drop_spu(spu)]
            if cleaned is not None
        ]
        repaired["correct_edges"] = edges_from_spus(repaired["correct_spus"])

    repair_notes = []
    if removed:
        repair_notes.append(f"removed_{len(removed)}_low_quality_spu")
    if first_break_id and first_break_id not in {spu.get("id") for spu in cleaned_spus}:
        repaired["repair_status"] = "needs_manual_review"
        repair_notes.append("first_break_spu_removed")
    else:
        repaired["repair_status"] = "repaired"

    if first_break_id:
        target = next((spu for spu in cleaned_spus if spu.get("id") == first_break_id), None)
        if target is not None:
            detail = repaired.get("first_break_detail", {})
            if isinstance(detail, dict):
                detail["spu_text"] = normalize_spu_text(target.get("text", ""))
                repaired["first_break_detail"] = detail
            generated = repaired.get("generated_first_break", {})
            if isinstance(generated, dict):
                generated.setdefault("spu_id", first_break_id)
                repaired["generated_first_break"] = generated

    repaired["repair_notes"] = repair_notes
    repaired["removed_spus_during_repair"] = removed
    return repaired


def _first_break_id(record: dict[str, Any]) -> str:
    corrected = record.get("human_corrected_first_break")
    if isinstance(corrected, dict) and corrected.get("spu_id"):
        return str(corrected["spu_id"])
    first_break = record.get("first_break")
    if isinstance(first_break, dict) and first_break.get("spu_id"):
        return str(first_break["spu_id"])
    generated = record.get("generated_first_break")
    if isinstance(generated, dict) and generated.get("spu_id"):
        return str(generated["spu_id"])
    injected = record.get("injected_error")
    if isinstance(injected, dict) and injected.get("target_spu_id"):
        return str(injected["target_spu_id"])
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="wrong_solutions_needs_revision.jsonl")
    parser.add_argument("--out", default="wrong_solutions_needs_revision_repaired.jsonl")
    parser.add_argument("--out-manual", default="wrong_solutions_needs_manual_review.jsonl")
    args = parser.parse_args()

    repaired = [repair_record(record) for record in read_jsonl(Path(args.input))]
    manual = [record for record in repaired if record.get("repair_status") == "needs_manual_review"]
    write_jsonl(repaired, Path(args.out))
    write_jsonl(manual, Path(args.out_manual))
    print(
        json.dumps(
            {
                "input_records": len(repaired),
                "repaired": sum(record.get("repair_status") == "repaired" for record in repaired),
                "needs_manual_review": len(manual),
                "out": args.out,
                "out_manual": args.out_manual,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
