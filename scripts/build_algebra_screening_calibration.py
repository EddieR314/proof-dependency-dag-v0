from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ANCHORS = {
    "0gif": "functional_equations",
    "00q2": "polynomials",
    "06og": "inequalities",
    "0ldq": "recurrences_sequences",
    "0le0": "discrete_algebra",
    "0chi": "complex_algebra",
}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stable_rank(seed: int, problem_id: str) -> bytes:
    return hashlib.sha256(f"{seed}:{problem_id}".encode()).digest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--clean-per-module", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260801)
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    by_id = {row["problem_id"]: row for row in rows}
    missing_anchors = sorted(set(ANCHORS) - set(by_id))
    if missing_anchors:
        raise ValueError(f"Missing reviewed anchors: {missing_anchors}")

    selected: dict[str, dict] = {problem_id: by_id[problem_id] for problem_id in ANCHORS}
    selection_reason = {problem_id: "reviewed_positive_anchor" for problem_id in ANCHORS}

    for row in rows:
        if row["prefilter"]["flags"]:
            selected[row["problem_id"]] = row
            selection_reason.setdefault(row["problem_id"], "machine_risk_flag")

    pools: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["problem_id"] not in selected and not row["prefilter"]["flags"]:
            pools[row["candidate_algebra_module"]].append(row)
    for module, pool in pools.items():
        ranked = sorted(pool, key=lambda row: stable_rank(args.seed, row["problem_id"]))
        for row in ranked[: args.clean_per_module]:
            selected[row["problem_id"]] = row
            selection_reason[row["problem_id"]] = f"clean_stratum:{module}"

    ordered = sorted(selected.values(), key=lambda row: (selection_reason[row["problem_id"]], row["problem_id"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.output_dir / "calibration_input_v0.1.jsonl"
    write_jsonl(input_path, ordered)

    manifest = {
        "protocol": "algebra-dag-suitability-calibration-v0.1",
        "source": str(args.input),
        "seed": args.seed,
        "num_records": len(ordered),
        "reviewed_positive_anchors": ANCHORS,
        "anchor_evidence": "Each anchor already has a human-reviewed Reference DAG in pilots/. This establishes suitability only, not a negative class.",
        "selection": [
            {"problem_id": row["problem_id"], "reason": selection_reason[row["problem_id"]]}
            for row in ordered
        ],
        "integrity_warning": "All non-anchor decisions remain unlabelled until human review. Prefilter flags are not gold labels.",
    }
    (args.output_dir / "calibration_manifest_v0.1.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"calibration_rows": len(ordered), "output": str(input_path)}, indent=2))


if __name__ == "__main__":
    main()

