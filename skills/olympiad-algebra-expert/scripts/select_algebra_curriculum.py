#!/usr/bin/env python3
"""Build deterministic, deduplicated olympiad-algebra curriculum splits."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


BUCKETS = (
    "functional_equations",
    "inequalities",
    "polynomials",
    "recurrences_sequences",
    "complex_algebra",
    "discrete_algebra",
)

CLASSIFICATION_PRIORITY = (
    "complex_algebra",
    "discrete_algebra",
    "functional_equations",
    "recurrences_sequences",
    "inequalities",
    "polynomials",
)

KEYWORDS = {
    "functional_equations": (
        "functional equation",
        "injectivity",
        "surjectivity",
    ),
    "inequalities": (
        "inequal",
        "am-gm",
        "qm-am-gm",
        "power mean",
        "cauchy",
        "jensen",
        "smoothing",
        "muirhead",
        "majorization",
    ),
    "polynomials": (
        "polynomial",
        "quadratic function",
        "quadratic equation",
        "vieta",
        "irreducib",
        "rational root",
        "eisenstein",
    ),
    "recurrences_sequences": (
        "recurrence",
        "telescoping",
    ),
    "complex_algebra": (
        "complex number",
        "roots of unity",
    ),
    "discrete_algebra": (
        "floor",
        "ceiling",
    ),
}


def classify(domain: str) -> str | None:
    text = domain.lower()
    for bucket in CLASSIFICATION_PRIORITY:
        if any(keyword in text for keyword in KEYWORDS[bucket]):
            return bucket
    return None


def unclassified_reason(domain: str, statement: str = "") -> str:
    text = f"{domain}\n{statement}".lower()
    if "linear algebra" in text or "matrices" in text or "determinant" in text:
        return "taxonomy_gap: linear_algebra_not_in_current_six_modules"
    if any(
        marker in text
        for marker in (
            "calculus",
            "precalculus",
            "trigonometric",
            "\\sin",
            "\\cos",
            "\\tan",
        )
    ):
        return "source_bucket_noise: primarily_trigonometry_or_calculus"
    return "taxonomy_gap: no_supported_module_keyword"


def stable_jitter(seed: int, problem_id: str) -> float:
    digest = hashlib.sha256(f"{seed}:{problem_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def eligible(
    row: dict[str, str], min_solution_length: int, max_solution_length: int
) -> bool:
    solution_length = int(
        row.get("solution_length") or len(row.get("solution", ""))
    )
    return (
        row.get("proof_domain_bucket", "").strip().lower() == "algebra"
        and truthy(row.get("has_solution", ""))
        and bool(row.get("statement", "").strip())
        and bool(row.get("solution", "").strip())
        and row.get("language_bucket", "").startswith("English")
        and not row.get("text_image_indicators", "").strip()
        and min_solution_length <= solution_length <= max_solution_length
    )


def deduplicate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    chosen: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("normalized_hash", "").strip() or row["problem_id"]
        incumbent = chosen.get(key)
        if incumbent is None:
            chosen[key] = row
            continue
        old_score = float(incumbent.get("proof_sample_score") or 0)
        new_score = float(row.get("proof_sample_score") or 0)
        if new_score > old_score:
            chosen[key] = row
    return list(chosen.values())


def ranked(rows: list[dict[str, str]], seed: int) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row.get("proof_sample_score") or 0),
            stable_jitter(seed, row["problem_id"]),
        ),
    )


def take_diverse(
    rows: list[dict[str, str]],
    count: int,
    source_cap: int,
    max_solution_length: int | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    selected: list[dict[str, str]] = []
    deferred: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    sources: Counter[str] = Counter()
    for row in rows:
        solution_length = int(
            row.get("solution_length") or len(row.get("solution", ""))
        )
        if (
            max_solution_length is not None
            and solution_length > max_solution_length
        ):
            blocked.append(row)
            continue
        source = row.get("competition", "").strip() or row.get("source", "")
        if len(selected) < count and sources[source] < source_cap:
            selected.append(row)
            sources[source] += 1
        else:
            deferred.append(row)
    if len(selected) < count:
        need = count - len(selected)
        selected.extend(deferred[:need])
        deferred = deferred[need:]
    return selected, deferred + blocked


def annotate(
    row: dict[str, str], bucket: str, split: str, rank: int
) -> dict[str, str | int]:
    result: dict[str, str | int] = dict(row)
    result["algebra_module"] = bucket
    result["curriculum_split"] = split
    result["module_rank"] = rank
    result["proof_review_status"] = "not_run"
    result["dag_status"] = "not_run"
    result["formal_status"] = "not_run"
    return result


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--calibration-per-module", type=int, default=2)
    parser.add_argument("--expansion-per-module", type=int, default=8)
    parser.add_argument("--heldout-per-module", type=int, default=4)
    parser.add_argument("--source-cap", type=int, default=2)
    parser.add_argument("--min-solution-length", type=int, default=300)
    parser.add_argument("--max-solution-length", type=int, default=12000)
    parser.add_argument(
        "--calibration-max-solution-length", type=int, default=5000
    )
    parser.add_argument(
        "--calibration-target-solution-length", type=int, default=2500
    )
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        raw = list(csv.DictReader(handle))

    accepted = deduplicate(
        [
            row
            for row in raw
            if eligible(
                row,
                args.min_solution_length,
                args.max_solution_length,
            )
        ]
    )
    by_bucket: dict[str, list[dict[str, str]]] = defaultdict(list)
    unclassified: list[dict[str, str]] = []
    for row in accepted:
        bucket = classify(row.get("domain", ""))
        if bucket is None:
            rejected = dict(row)
            rejected["exclusion_reason"] = unclassified_reason(
                row.get("domain", ""),
                row.get("statement", ""),
            )
            unclassified.append(rejected)
        else:
            by_bucket[bucket].append(row)

    splits: dict[str, list[dict[str, object]]] = {
        "calibration": [],
        "expansion": [],
        "heldout": [],
    }
    requested = {
        "calibration": args.calibration_per_module,
        "expansion": args.expansion_per_module,
        "heldout": args.heldout_per_module,
    }

    shortages: dict[str, dict[str, int]] = defaultdict(dict)
    for bucket in BUCKETS:
        pool = ranked(by_bucket[bucket], args.seed)
        calibration_pool = sorted(
            pool,
            key=lambda row: (
                abs(
                    int(
                        row.get("solution_length")
                        or len(row.get("solution", ""))
                    )
                    - args.calibration_target_solution_length
                ),
                -float(row.get("proof_sample_score") or 0),
                stable_jitter(args.seed, row["problem_id"]),
            ),
        )
        calibration, _ = take_diverse(
            calibration_pool,
            requested["calibration"],
            args.source_cap,
            args.calibration_max_solution_length,
        )
        selected_ids = {row["problem_id"] for row in calibration}
        pool = [row for row in pool if row["problem_id"] not in selected_ids]
        splits["calibration"].extend(
            annotate(row, bucket, "calibration", rank)
            for rank, row in enumerate(calibration, 1)
        )
        if len(calibration) < requested["calibration"]:
            shortages[bucket]["calibration"] = (
                requested["calibration"] - len(calibration)
            )

        for split in ("expansion", "heldout"):
            count = requested[split]
            picked, pool = take_diverse(
                pool,
                count,
                args.source_cap,
            )
            splits[split].extend(
                annotate(row, bucket, split, rank)
                for rank, row in enumerate(picked, 1)
            )
            if len(picked) < count:
                shortages[bucket][split] = count - len(picked)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in splits.items():
        rows.sort(key=lambda row: (str(row["algebra_module"]), int(row["module_rank"])))
        write_jsonl(args.output_dir / f"{split}.jsonl", rows)
        write_csv(args.output_dir / f"{split}.csv", rows)
    write_jsonl(args.output_dir / "unclassified.jsonl", unclassified)
    write_csv(args.output_dir / "unclassified.csv", unclassified)

    summary = {
        "input": str(args.input.resolve()),
        "seed": args.seed,
        "raw_count": len(raw),
        "eligible_deduplicated_count": len(accepted),
        "classified_count": sum(map(len, by_bucket.values())),
        "unclassified_count": len(unclassified),
        "available_by_module": {
            bucket: len(by_bucket[bucket]) for bucket in BUCKETS
        },
        "selected_by_split": {
            split: len(rows) for split, rows in splits.items()
        },
        "selected_by_module_and_split": {
            bucket: {
                split: sum(
                    row["algebra_module"] == bucket for row in rows
                )
                for split, rows in splits.items()
            }
            for bucket in BUCKETS
        },
        "shortages": shortages,
        "selection_policy": {
            "dedup_key": "normalized_hash, fallback problem_id",
            "image_dependent_excluded": True,
            "source_cap_per_module_split": args.source_cap,
            "solution_length_range": [
                args.min_solution_length,
                args.max_solution_length,
            ],
            "calibration_max_solution_length": (
                args.calibration_max_solution_length
            ),
            "calibration_target_solution_length": (
                args.calibration_target_solution_length
            ),
        },
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
