from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


DROP_FIELDS = {
    "solution",
    "final_answer",
    "proof_review_status",
    "dag_status",
    "formal_status",
}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--skill-version", default="0.2")
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    public_rows = []
    for row in rows:
        public = {key: value for key, value in row.items() if key not in DROP_FIELDS}
        public["heldout_protocol"] = {
            "skill_version": args.skill_version,
            "reference_fields_removed": sorted(DROP_FIELDS),
            "prediction_status": "not_run",
        }
        public_rows.append(public)

    public_path = args.output_dir / "statements_only.jsonl"
    write_jsonl(public_path, public_rows)

    manifest = {
        "protocol": "postfreeze-heldout-v0.1",
        "skill_version": args.skill_version,
        "source": str(args.input),
        "num_samples": len(public_rows),
        "module_counts_from_source_labels": dict(
            sorted(Counter(row["algebra_module"] for row in public_rows).items())
        ),
        "removed_reference_fields": sorted(DROP_FIELDS),
        "statements_only_sha256": sha256(public_path),
        "known_reference_exposure": {
            "problem_ids": ["03te", "0get", "0404"],
            "policy": "Exclude these records from blind-proof metrics.",
        },
        "result_policy": (
            "Store results outside the frozen Skill. Do not revise v0.2 from this run."
        ),
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
