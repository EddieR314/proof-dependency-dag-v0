from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


PARAGRAPH_SPLIT = re.compile(r"(?:\r?\n){2,}")
MODULE_KEYWORDS = {
    "functional_equations": ("functional equation", "injectivity", "surjectivity"),
    "inequalities": ("inequal", "am-gm", "qm-am-gm", "power mean", "cauchy", "jensen", "smoothing", "muirhead", "majorization"),
    "polynomials": ("polynomial", "quadratic function", "quadratic equation", "vieta", "irreducib", "rational root", "eisenstein"),
    "recurrences_sequences": ("recurrence", "telescoping", "sequence", "series"),
    "complex_algebra": ("complex number", "roots of unity"),
    "discrete_algebra": ("floor", "ceiling"),
}
MODULE_PRIORITY = ("complex_algebra", "discrete_algebra", "functional_equations", "recurrences_sequences", "inequalities", "polynomials")


def read_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        with path.open(encoding="utf-8-sig") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def repeated_text_suspected(text: str) -> bool:
    paragraphs = [" ".join(part.split()) for part in PARAGRAPH_SPLIT.split(text)]
    substantive = [part for part in paragraphs if len(part) >= 80]
    return any(count >= 3 for count in Counter(substantive).values())


def algebra_module_candidate(row: dict) -> str:
    text = f"{row.get('domain', '')}\n{row.get('statement', '')}".lower()
    for module in MODULE_PRIORITY:
        if any(keyword in text for keyword in MODULE_KEYWORDS[module]):
            return module
    return "unclassified_algebra"


def prefilter(row: dict) -> dict:
    statement = str(row.get("statement", "")).strip()
    solution = str(row.get("solution", "")).strip()
    image_indicator = str(row.get("text_image_indicators", "")).strip()
    flags: list[str] = []
    if not statement:
        flags.append("missing_statement")
    if not solution or not as_bool(row.get("has_solution", bool(solution))):
        flags.append("missing_solution")
    if solution and len(solution) < 200:
        flags.append("very_short_solution")
    if len(solution) > 12000:
        flags.append("very_long_solution")
    if solution and repeated_text_suspected(solution):
        flags.append("repeated_text_suspected")
    if image_indicator and image_indicator not in {"[]", "{}", "None", "none"}:
        flags.append("image_dependency_suspected")
    return {
        "statement_char_count": len(statement),
        "solution_char_count": len(solution),
        "flags": flags,
        "machine_prefilter_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    source_rows = read_rows(args.input)
    rows = [
        row for row in source_rows
        if str(row.get("proof_domain_bucket", "")).strip().lower() == "algebra"
    ]
    selected = rows[args.offset :]
    if args.limit is not None:
        selected = selected[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for index, row in enumerate(selected, args.offset):
            record = {
                "problem_id": str(row.get("problem_id", f"row-{index}")),
                "source_index": index,
                "source": row.get("source", ""),
                "domain": row.get("domain", ""),
                "candidate_algebra_module": algebra_module_candidate(row),
                "statement": row.get("statement", ""),
                "solution": row.get("solution", ""),
                "prefilter": prefilter(row),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({"input_rows": len(source_rows), "algebra_scope_rows": len(rows), "output_rows": len(selected), "out_of_scope_rows": len(source_rows) - len(rows), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
