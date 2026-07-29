#!/usr/bin/env python3
"""Promote reviewed supplemental cases without leaking them into expansion."""

from __future__ import annotations

import csv
import json
from pathlib import Path


SUPPLEMENTAL_IDS = {"042l"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    data = root / "data" / "algebra_skill_curriculum"
    calibration = read_csv(data / "calibration.csv")
    expansion = read_csv(data / "expansion.csv")
    heldout = read_csv(data / "heldout.csv")

    promoted = [row for row in expansion if row["problem_id"] in SUPPLEMENTAL_IDS]
    if {row["problem_id"] for row in promoted} != SUPPLEMENTAL_IDS:
        raise ValueError("not every supplemental problem was found in expansion")

    clean_expansion = [
        row for row in expansion if row["problem_id"] not in SUPPLEMENTAL_IDS
    ]
    reviewed_calibration = [
        {**row, "reviewed_curriculum_split": "calibration"}
        for row in calibration
    ] + [
        {**row, "reviewed_curriculum_split": "supplemental_calibration"}
        for row in promoted
    ]
    reviewed_expansion = [
        {**row, "reviewed_curriculum_split": "expansion"}
        for row in clean_expansion
    ]
    reviewed_heldout = [
        {**row, "reviewed_curriculum_split": "heldout"} for row in heldout
    ]

    outputs = {
        "calibration_reviewed_v0.2": reviewed_calibration,
        "expansion_reviewed_v0.2": reviewed_expansion,
        "heldout_reviewed_v0.2": reviewed_heldout,
    }
    for stem, rows in outputs.items():
        write_csv(data / f"{stem}.csv", rows)
        write_jsonl(data / f"{stem}.jsonl", rows)

    hashes = [
        row["normalized_hash"]
        for rows in outputs.values()
        for row in rows
    ]
    if len(hashes) != len(set(hashes)):
        raise ValueError("cross-split normalized_hash leakage detected")

    summary = {
        "supplemental_promotions": sorted(SUPPLEMENTAL_IDS),
        "counts": {stem: len(rows) for stem, rows in outputs.items()},
        "cross_split_hash_leakage": False,
        "heldout_reference_opened": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
