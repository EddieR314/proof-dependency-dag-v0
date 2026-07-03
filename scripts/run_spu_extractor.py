import argparse
import json
import re
from pathlib import Path

from spu_utils import write_jsonl


def read_raw_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if "student_solution" not in record:
                raise ValueError(f"Line {line_number} missing student_solution")
            records.append(record)
    return records


def read_markdown_cases(path):
    text = Path(path).read_text(encoding="utf-8")
    sections = re.split(r"(?=^## Wrong Solution\s+\d+)", text, flags=re.MULTILINE)
    records = []

    for section in sections:
        title_match = re.match(r"^## Wrong Solution\s+(\d+)", section.strip())
        if not title_match:
            continue

        index = title_match.group(1)
        mutation_match = re.search(r"Mutation type:\s*`([^`]+)`", section)
        solution_match = re.search(
            r"### Student-Style Wrong Solution\s*(.*?)(?:\n### Why It Is Wrong|\Z)",
            section,
            flags=re.DOTALL,
        )
        if not solution_match:
            continue

        records.append(
            {
                "sample_id": f"markdown_wrong_{index}",
                "problem_id": "unknown_problem",
                "mutation_type": mutation_match.group(1) if mutation_match else "unknown",
                "student_solution": clean_markdown_math(solution_match.group(1)),
            }
        )

    return records


def clean_markdown_math(text):
    text = re.sub(r"\\\[(.*?)\\\]", lambda m: " " + m.group(1).replace("\n", " ") + " ", text, flags=re.DOTALL)
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text)
    text = text.replace("\\", "")
    return re.sub(r"\s+", " ", text).strip()


def extract_record(raw_record):
    solution = raw_record["student_solution"]
    steps = split_steps(solution)
    spus = []

    for index, step in enumerate(steps, 1):
        sid = f"S{index}"
        role = guess_role(step)
        depends_on = guess_dependencies(index, role)
        status = guess_status(step, role, raw_record.get("mutation_type"))
        spu = {
            "id": sid,
            "text": step,
            "role": role,
            "depends_on": depends_on,
            "case_scope": guess_case_scope(step, role),
            "status": status,
        }

        missing = guess_missing_dependencies(step, raw_record.get("mutation_type"))
        if missing:
            spu["missing_dependencies"] = missing
        if status == "invalid":
            spu["notes"] = "Heuristic extractor flagged this theorem use as invalid."
        elif status == "unsupported" and "missing_dependencies" not in spu:
            spu["notes"] = "Heuristic extractor flagged this step as unsupported."

        spus.append(spu)

    propagate_bad_dependencies(spus)
    first_break = find_first_break(spus, raw_record.get("mutation_type"))

    return {
        "sample_id": raw_record.get("sample_id", "unknown_sample"),
        "problem_id": raw_record.get("problem_id", "unknown_problem"),
        "mutation_type": raw_record.get("mutation_type", "unknown"),
        "spus": spus,
        "first_break": first_break,
        "final_outcome": {
            "proof_valid": first_break is None,
            "answer_valid": first_break is None,
        },
    }


def split_steps(solution):
    normalized = re.sub(r"\s+", " ", solution).strip()
    if not normalized:
        return []

    parts = re.split(r"(?<=[.!?。；;])\s+", normalized)
    steps = [part.strip(" ;。") for part in parts if part.strip(" ;。")]

    merged = []
    buffer = []
    for step in steps:
        buffer.append(step)
        if len(" ".join(buffer)) >= 35 or step.lower().startswith(("therefore", "thus", "hence", "so ")):
            merged.append(" ".join(buffer))
            buffer = []
    if buffer:
        merged.append(" ".join(buffer))

    return merged


def guess_role(text):
    lower = text.lower()
    if "without loss" in lower or "wlog" in lower or "arrange" in lower:
        return "wlog"
    if lower.startswith(("first suppose", "now suppose", "if ", "suppose ")):
        return "case_assumption"
    if "split into" in lower or "consider parity cases" in lower:
        return "case_split"
    if "therefore" in lower or "thus" in lower or "ordered solutions" in lower or "solutions are" in lower:
        return "final_conclusion" if "solution" in lower else "inference"
    if "gcd" in lower or "=" in text or "<=" in text or ">=" in text:
        return "calculation"
    if "power" in lower or "estimate" in lower or "divides" in lower:
        return "theorem_use"
    return "inference"


def guess_dependencies(index, role):
    if index == 1:
        return ["problem"]
    if role == "case_assumption":
        return ["S1"]
    if role == "final_conclusion" and index > 2:
        return [f"S{index - 1}", "S1"]
    return [f"S{index - 1}"]


def guess_case_scope(text, role):
    lower = text.lower()
    if "a is even" in lower:
        return "case_even_a"
    if "all" in lower and "odd" in lower:
        return "case_all_odd"
    if "b,c are even" in lower or "mixed" in lower:
        return "case_mixed_parity"
    if role in {"case_assumption", "case_conclusion"}:
        return "case_unknown"
    return "global"


def guess_status(text, role, mutation_type):
    lower = text.lower()
    compact = re.sub(r"\s+", "", lower)

    if mutation_type == "invalid_theorem_use" and (
        "consecutive powers" in lower or "ab-c=2(ca-b)" in compact
    ):
        return "invalid"
    if mutation_type == "missing_premise_edge" and "a^2-1 is odd" in lower:
        return "unsupported"
    if mutation_type == "case_omission" and "ordered solutions" in lower:
        return "unsupported"
    if mutation_type == "overclaim_final" and "solutions are exactly" in lower:
        return "unsupported"
    if mutation_type == "variable_mismatch" and "mixed case only gives" in lower:
        return "unsupported"
    if role == "final_conclusion" and mutation_type not in {None, "unknown"}:
        return "unsupported"
    return "valid"


def guess_missing_dependencies(text, mutation_type):
    lower = text.lower()
    if mutation_type == "missing_premise_edge" and "a^2-1 is odd" in lower:
        return ["a is even"]
    if mutation_type == "case_omission":
        return ["case a odd and b,c even"]
    if mutation_type == "overclaim_final":
        return ["apply all permutations after WLOG ordering"]
    if mutation_type == "variable_mismatch":
        return ["analysis of ca-b"]
    return []


def find_first_break(spus, mutation_type):
    for spu in spus:
        if spu["status"] in {"invalid", "unsupported"}:
            return {
                "spu_id": spu["id"],
                "break_type": normalize_break_type(mutation_type, spu["status"]),
                "reason": "Heuristic first-break prediction; replace with LLM-backed analysis for production.",
                "gold_confidence": "low",
            }
    return None


def propagate_bad_dependencies(spus):
    by_id = {spu["id"]: spu for spu in spus}
    changed = True

    while changed:
        changed = False
        for spu in spus:
            if spu["status"] in {"invalid", "unsupported"}:
                continue
            bad_deps = [
                dep
                for dep in spu.get("depends_on", [])
                if dep in by_id and by_id[dep]["status"] in {"invalid", "unsupported"}
            ]
            if not bad_deps:
                continue

            spu["status"] = "unsupported"
            spu["missing_dependencies"] = [
                f"valid dependency {dep}" for dep in bad_deps
            ]
            spu["notes"] = "Status propagated from unsupported/invalid dependency."
            changed = True


def normalize_break_type(mutation_type, status):
    if mutation_type == "missing_premise_edge":
        return "missing_dependency"
    if mutation_type in {
        "case_omission",
        "invalid_theorem_use",
        "overclaim_final",
        "variable_mismatch",
    }:
        return mutation_type
    return "unsupported_conclusion" if status == "unsupported" else "invalid_theorem_use"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-jsonl", help="Raw JSONL with student_solution fields.")
    parser.add_argument("--input-md", help="Markdown file containing Wrong Solution sections.")
    parser.add_argument("--output", required=True, help="Output model_pred-style JSONL path.")
    args = parser.parse_args()

    if bool(args.input_jsonl) == bool(args.input_md):
        raise SystemExit("Pass exactly one of --input-jsonl or --input-md.")

    raw_records = read_raw_jsonl(args.input_jsonl) if args.input_jsonl else read_markdown_cases(args.input_md)
    extracted = [extract_record(record) for record in raw_records]
    write_jsonl(args.output, extracted)
    print(f"Wrote {len(extracted)} records to {args.output}")


if __name__ == "__main__":
    main()
