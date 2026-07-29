from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTOR_PATH = (
    ROOT
    / "skills"
    / "olympiad-algebra-expert"
    / "scripts"
    / "select_algebra_curriculum.py"
)

MODULES = (
    "functional_equations",
    "inequalities",
    "polynomials",
    "recurrences_sequences",
    "complex_algebra",
    "discrete_algebra",
)

DEFAULT_QUOTAS = {
    "functional_equations": 24,
    "inequalities": 24,
    "polynomials": 18,
    "recurrences_sequences": 17,
    "complex_algebra": 9,
    "discrete_algebra": 8,
}

PUBLIC_FIELDS = (
    "problem_id",
    "source",
    "source_confidence",
    "competition",
    "country",
    "year",
    "language",
    "domain",
    "problem_type",
    "statement",
    "source_url",
    "source_file",
    "raw_hash",
    "normalized_hash",
    "proof_sample_score",
    "statement_length",
    "solution_length",
    "language_bucket",
)


def load_selector():
    spec = importlib.util.spec_from_file_location("algebra_selector", SELECTOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load selector from {SELECTOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def stable_number(seed: int, *parts: str) -> int:
    payload = ":".join((str(seed), *parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_key(row: dict[str, str]) -> str:
    return (
        row.get("competition", "").strip()
        or row.get("contest", "").strip()
        or row.get("source_file", "").strip()
        or row.get("source", "").strip()
    )


def quality_flags(row: dict[str, str]) -> list[str]:
    flags: list[str] = []
    statement = row.get("statement", "")
    if "\ufffd" in statement:
        flags.append("replacement_character")
    mojibake_markers = ("Ã", "鈥", "锛", "鐨", "灏", "茅", "脿", "霉")
    if any(marker in statement for marker in mojibake_markers):
        flags.append("possible_mojibake")
    if len(statement.strip()) < 60:
        flags.append("very_short_statement")
    if not row.get("competition", "").strip():
        flags.append("competition_missing")
    return flags


def select_diverse(
    rows: list[dict[str, str]],
    count: int,
    seed: int,
    module: str,
    source_cap: int,
) -> list[dict[str, str]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -float(row.get("proof_sample_score") or 0),
            stable_number(seed, module, row["problem_id"]),
        ),
    )
    selected: list[dict[str, str]] = []
    deferred: list[dict[str, str]] = []
    sources: Counter[str] = Counter()
    for row in ranked:
        key = source_key(row)
        if len(selected) < count and sources[key] < source_cap:
            selected.append(row)
            sources[key] += 1
        else:
            deferred.append(row)
    if len(selected) < count:
        selected.extend(deferred[: count - len(selected)])
    return selected[:count]


def public_record(
    row: dict[str, str], module: str, module_rank: int, pilot_order: int
) -> dict:
    record = {field: row.get(field, "") for field in PUBLIC_FIELDS}
    record.update(
        {
            "pilot_id": f"algebra-scale-100-{pilot_order:03d}",
            "pilot_order": pilot_order,
            "source_bucket": module,
            "module_rank": module_rank,
            "quality_flags": quality_flags(row),
            "reference_access": "sealed",
            "prediction_status": "not_run",
        }
    )
    return record


def prediction_template(row: dict) -> dict:
    return {
        "problem_id": row["problem_id"],
        "pilot_id": row["pilot_id"],
        "prediction_status": "not_run",
        "routing": {
            "primary_module": "",
            "secondary_modules": [],
            "confidence": "",
        },
        "candidate_answer": "",
        "proof_result": "not_run",
        "proof": "",
        "risk_flags": [],
        "spu_outline": [],
        "dag_lean_handoff_readiness": "not_run",
        "component_status": {
            "proof_review": "not_run",
            "dag": "not_run",
            "formal_mapping": "not_run",
            "lean_build": "not_run",
        },
    }


def audit_template(row: dict, reviewer_slot: str) -> dict:
    return {
        "problem_id": row["problem_id"],
        "pilot_id": row["pilot_id"],
        "source_bucket": row["source_bucket"],
        "reviewer_slot": reviewer_slot,
        "reviewer": "",
        "routing_decision": "pending",
        "reviewed_primary_module": "",
        "proof_decision": "pending",
        "reference_match": "not_opened",
        "spu_decision": "pending",
        "risk_flags_decision": "pending",
        "severity": "",
        "failure_type": "",
        "notes": "",
    }


def build_audit_sample(rows: list[dict], seed: int) -> list[dict]:
    by_module: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_module[row["source_bucket"]].append(row)
    selected: list[dict] = []
    for module in MODULES:
        ranked = sorted(
            by_module[module],
            key=lambda row: stable_number(seed, "audit", row["problem_id"]),
        )
        selected.extend(ranked[:5])
    return sorted(selected, key=lambda row: row["pilot_order"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--heldout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument("--source-cap", type=int, default=3)
    parser.add_argument("--skill-version", default="0.2")
    args = parser.parse_args()

    selector = load_selector()
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        raw = list(csv.DictReader(handle))

    accepted = selector.deduplicate(
        [row for row in raw if selector.eligible(row, 300, 12000)]
    )
    excluded_rows = read_jsonl(args.calibration) + read_jsonl(args.heldout)
    excluded_ids = {row["problem_id"] for row in excluded_rows}
    excluded_hashes = {
        row.get("normalized_hash", "").strip()
        for row in excluded_rows
        if row.get("normalized_hash", "").strip()
    }

    by_module: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in accepted:
        normalized_hash = row.get("normalized_hash", "").strip()
        if row["problem_id"] in excluded_ids or normalized_hash in excluded_hashes:
            continue
        module = selector.classify(row.get("domain", ""))
        if module is not None:
            by_module[module].append(row)

    selected_by_module: dict[str, list[dict[str, str]]] = {}
    shortages: dict[str, int] = {}
    for module in MODULES:
        quota = DEFAULT_QUOTAS[module]
        selected_by_module[module] = select_diverse(
            by_module[module],
            quota,
            args.seed,
            module,
            args.source_cap,
        )
        if len(selected_by_module[module]) < quota:
            shortages[module] = quota - len(selected_by_module[module])

    if shortages:
        raise RuntimeError(f"Cannot satisfy fixed quotas: {shortages}")

    public_rows: list[dict] = []
    pilot_order = 1
    for module in MODULES:
        for module_rank, row in enumerate(selected_by_module[module], 1):
            public_rows.append(
                public_record(row, module, module_rank, pilot_order)
            )
            pilot_order += 1

    if len(public_rows) != 100:
        raise AssertionError(f"Expected 100 rows, got {len(public_rows)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    statements_path = args.output_dir / "statements_only.jsonl"
    predictions_path = args.output_dir / "predictions_template.jsonl"
    audit_a_path = args.output_dir / "human_audit_30_reviewer_a.jsonl"
    audit_b_path = args.output_dir / "human_audit_30_reviewer_b.jsonl"
    reference_index_path = args.output_dir / "reference_index.jsonl"

    write_jsonl(statements_path, public_rows)
    write_jsonl(
        predictions_path, [prediction_template(row) for row in public_rows]
    )
    audit_sample = build_audit_sample(public_rows, args.seed)
    write_jsonl(
        audit_a_path, [audit_template(row, "A") for row in audit_sample]
    )
    write_jsonl(
        audit_b_path, [audit_template(row, "B") for row in audit_sample]
    )
    write_jsonl(
        reference_index_path,
        [
            {
                "problem_id": row["problem_id"],
                "normalized_hash": row["normalized_hash"],
                "source_file": row["source_file"],
                "reference_access": "sealed_in_original_source",
            }
            for row in public_rows
        ],
    )

    manifest = {
        "protocol": "algebra-scale-pilot-100-v0.1",
        "skill_version": args.skill_version,
        "seed": args.seed,
        "source": str(args.input),
        "raw_source_count": len(raw),
        "eligible_deduplicated_count": len(accepted),
        "excluded_splits": ["calibration", "heldout"],
        "excluded_problem_count": len(excluded_ids),
        "candidate_pool_count": sum(len(rows) for rows in by_module.values()),
        "sample_count": len(public_rows),
        "module_quotas": DEFAULT_QUOTAS,
        "module_available_after_exclusion": {
            module: len(by_module[module]) for module in MODULES
        },
        "human_audit_count": len(audit_sample),
        "human_audit_per_module": 5,
        "quality_flag_counts": dict(
            sorted(
                Counter(
                    flag
                    for row in public_rows
                    for flag in row["quality_flags"]
                ).items()
            )
        ),
        "unique_source_keys_by_module": {
            module: len(
                {
                    source_key(row)
                    for row in selected_by_module[module]
                }
            )
            for module in MODULES
        },
        "reference_policy": (
            "Keep references sealed until predictions are frozen and hashed."
        ),
        "frozen_skill_policy": (
            "Do not revise olympiad-algebra-expert-v0.2 from pilot outputs."
        ),
        "checksums": {
            "statements_only": sha256(statements_path),
            "predictions_template": sha256(predictions_path),
            "human_audit_30_reviewer_a": sha256(audit_a_path),
            "human_audit_30_reviewer_b": sha256(audit_b_path),
            "reference_index": sha256(reference_index_path),
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
