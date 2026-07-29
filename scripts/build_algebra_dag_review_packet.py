"""Render candidate algebra DAGs into one human semantic-review packet."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "algebra_dag_human_review_packet_v0.2-rc1.md"
PROBLEMS = [
    ("00q2", "polynomials", "candidate_evaluation.json", "mutation_check.json"),
    ("06og", "inequalities", "candidate_evaluation.json", "mutation_check.json"),
    ("0ldq", "recurrences_sequences", "candidate_evaluation.json", "mutation_check.json"),
    ("0le0", "discrete_algebra", "candidate_evaluation.json", "mutation_check.json"),
    ("0chi", "complex_algebra", "candidate_evaluation_v04.json", "mutation_check_v04.json"),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluation_payload(payload: dict) -> dict:
    return payload.get("evaluation", payload)


def render_problem(
    problem_id: str,
    module: str,
    evaluation_name: str,
    mutation_check_name: str,
) -> str:
    directory = ROOT / "pilots" / problem_id
    reference = load(directory / "reference_dag.json")
    candidate = load(directory / "candidate_graph.json")
    evaluation = evaluation_payload(load(directory / evaluation_name))
    mutation_check = load(directory / mutation_check_name)
    facts = {item["id"]: item for item in reference["facts"]}

    lines = [
        f"## {problem_id} ({module})",
        "",
        "### Automatic Evidence",
        "",
        f"- Reference target derivable: `{evaluation_payload(load(directory / ('reference_evaluation_v04.json' if problem_id == '0chi' else 'correct_evaluation.json')))['all_targets_derivable']}`",
        f"- Candidate target derivable: `{evaluation['all_targets_derivable']}`",
        f"- Computed First Break: `{evaluation['computed_first_break']['id']}`",
        f"- Declared/computed match: `{evaluation.get('first_break_match')}`",
        f"- Mutation checker passed: `{mutation_check['passed']}`",
        "",
        "These automatic results establish structural consistency only. They do",
        "not establish that the natural-language claims and edges are faithful.",
        "",
        "### Facts",
        "",
        "| ID | Scope | Kind | Statement |",
        "| --- | --- | --- | --- |",
    ]
    for item in reference["facts"]:
        statement = item["statement"].replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{item['id']}` | `{item['scope']}` | "
            f"`{item['introduction_kind']}` | {statement} |"
        )
    lines.extend(
        [
            "",
            "### Inferences",
            "",
            "| ID | Scope | Rule application | Inputs by premise role | Output |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    rules = {item["rule_id"]: item for item in reference["rule_schemas"]}
    for item in sorted(reference["inferences"], key=lambda row: row["source_order"]):
        inputs = "; ".join(
            f"`{binding['premise_role']}={binding['fact_id']}`"
            for binding in item["input_bindings"]
        )
        lines.append(
            f"| `{item['id']}` | `{item['scope']}` | "
            f"{rules[item['rule_id']]['name']} | {inputs} | "
            f"`{item['output_fact_id']}` |"
        )
    mutation = candidate["mutation"]
    lines.extend(
        [
            "",
            "### Controlled Mutation",
            "",
            f"- Operation: `{mutation['operation']}`",
            f"- Primary site: `{mutation['primary_site']['id']}`",
            f"- Injection anchor: `{mutation['injection_anchor']['id']}`",
            f"- Before: `{json.dumps(mutation['before'], ensure_ascii=False)}`",
            f"- After: `{json.dumps(mutation['after'], ensure_ascii=False)}`",
            f"- Expected First Break: `{mutation['declared_expected_first_break']['id']}`",
            "",
            "### Human Decision",
            "",
            "- [ ] Every Fact statement is mathematically correct and atomic enough.",
            "- [ ] Every input edge is genuinely required by the stated rule.",
            "- [ ] No required mathematical premise is absent from the Reference DAG.",
            "- [ ] Scope and source order match the reviewed proof.",
            "- [ ] The mutation introduces exactly one real and plausible primary error.",
            "- [ ] The declared First Break is the earliest invalid inference.",
            "",
            "Reviewer:",
            "",
            "Date:",
            "",
            "DAG semantics: `pending / passed / failed`",
            "",
            "Mutation realism: `pending / passed / failed`",
            "",
            "Notes:",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parts = [
        "# Algebra DAG Human Review Packet v0.2-rc1",
        "",
        "This packet covers only human semantic checks that automatic validators",
        "cannot establish. Mathematical proof review for all five source proofs",
        "has already passed.",
        "",
    ]
    for row in PROBLEMS:
        parts.append(render_problem(*row))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
