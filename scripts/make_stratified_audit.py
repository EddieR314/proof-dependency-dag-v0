from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


HARD_REASONS = {"missing_solution", "answer_only", "proof_corrupted", "proof_truncated", "image_required", "non_proof_content"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-stratum", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    records = {r["problem_id"]: r for r in read_jsonl(args.records)}
    predictions = read_jsonl(args.predictions)
    strata: dict[tuple[str, str], list[dict]] = defaultdict(list)
    mandatory: list[dict] = []
    for row in predictions:
        key = (row["algebra_module"], row["decision"], row["confidence"])
        if (
            row["decision"] == "borderline"
            or row["confidence"] == "low"
            or HARD_REASONS.intersection(row["reason_codes"])
        ):
            mandatory.append(row)
        else:
            strata[key].append(row)

    rng = random.Random(args.seed)
    chosen = {r["problem_id"]: r for r in mandatory}
    if args.all:
        chosen = {r["problem_id"]: r for r in predictions}
    else:
        for rows in strata.values():
            rng.shuffle(rows)
            for row in rows[: args.per_stratum]:
                chosen[row["problem_id"]] = row

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["problem_id", "candidate_algebra_module", "model_algebra_module", "model_decision", "model_confidence", "reason_codes", "prefilter_flags", "statement", "solution", "human_algebra_module", "human_decision", "human_reason_codes", "reviewer", "review_notes"]
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for problem_id in sorted(chosen):
            pred = chosen[problem_id]
            source = records.get(problem_id, {})
            writer.writerow({"problem_id": problem_id, "candidate_algebra_module": source.get("candidate_algebra_module", ""), "model_algebra_module": pred["algebra_module"], "model_decision": pred["decision"], "model_confidence": pred["confidence"], "reason_codes": "|".join(pred["reason_codes"]), "prefilter_flags": "|".join(source.get("prefilter", {}).get("flags", [])), "statement": source.get("statement", ""), "solution": source.get("solution", ""), "human_algebra_module": "", "human_decision": "", "human_reason_codes": "", "reviewer": "", "review_notes": ""})

    print(json.dumps({"audit_rows": len(chosen), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
