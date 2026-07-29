#!/usr/bin/env python3
"""Check a v0.4 graph, formal mapping, candidate mutation, and Lean build."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from dag_core import evaluate_graph, read_graph, validate_graph, write_json
from validate_dag import validate_json_schema


DECLARATION_RE = re.compile(
    r"^\s*(?:private\s+)?(?:theorem|lemma|def|abbrev)\s+"
    r"([A-Za-z_][A-Za-z0-9_']*)",
    re.MULTILINE,
)
PLACEHOLDER_RE = re.compile(r"\b(?:sorry|admit)\b")


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def check_formal_mapping(
    graph: dict[str, Any],
    formal_mapping: dict[str, Any],
    project_dir: Path,
    run_build: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if formal_mapping.get("formal_backend") != "lean":
        return {
            "passed": False,
            "errors": ["Only the Lean backend is implemented by this checker"],
            "warnings": [],
        }
    if formal_mapping.get("graph_id") != graph.get("graph_id"):
        errors.append("formal mapping graph_id does not match reference graph")

    facts = {fact["id"]: fact for fact in graph["facts"]}
    inferences = {
        inference["id"]: inference for inference in graph["inferences"]
    }
    source_file = project_dir / formal_mapping.get("source_file", "")
    source_text = ""
    source_declarations: set[str] = set()
    if not source_file.is_file():
        errors.append(f"Lean source file does not exist: {source_file}")
    else:
        source_text = source_file.read_text(encoding="utf-8")
        source_declarations = set(DECLARATION_RE.findall(source_text))
        if PLACEHOLDER_RE.search(source_text):
            errors.append("Lean source contains sorry or admit")

    mappings = formal_mapping.get("mapping")
    if not isinstance(mappings, list):
        errors.append("formal_mapping.mapping must be a list")
        mappings = []
    mapped: dict[str, dict[str, Any]] = {}
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            errors.append(f"mapping[{index}] must be an object")
            continue
        inference_id = mapping.get("inference_id")
        output_fact_id = mapping.get("output_fact_id")
        declaration = mapping.get("declaration")
        if inference_id not in inferences:
            errors.append(f"mapping[{index}]: unknown Inference {inference_id}")
            continue
        if inference_id in mapped:
            errors.append(f"{inference_id}: mapped more than once")
            continue
        mapped[inference_id] = mapping
        expected_output = inferences[inference_id]["output_fact_id"]
        if output_fact_id != expected_output or output_fact_id not in facts:
            errors.append(
                f"{inference_id}: output mapping must name {expected_output}"
            )
        if not isinstance(declaration, str) or not declaration:
            errors.append(f"{inference_id}: declaration is missing")
            continue
        terminal_name = declaration.rsplit(".", 1)[-1]
        if source_text and terminal_name not in source_declarations:
            errors.append(f"{declaration}: declaration not found in Lean source")
        if mapping.get("expected_compile_result") != "pass":
            errors.append(f"{inference_id}: expected compile result must be pass")

    unmapped = sorted(set(inferences) - set(mapped))
    coverage = formal_mapping.get("formal_coverage")
    if coverage == "end_to_end" and unmapped:
        errors.append(
            "end_to_end mapping leaves Inferences unmapped: " + ", ".join(unmapped)
        )
    elif unmapped:
        warnings.append("Unmapped Inferences: " + ", ".join(unmapped))

    build: dict[str, Any] = {
        "ran": run_build,
        "command": formal_mapping.get("command", "lake build"),
    }
    if run_build:
        completed = subprocess.run(
            ["lake", "build"],
            cwd=project_dir,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        build.update(
            {
                "exit_status": completed.returncode,
                "passed": completed.returncode == 0,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
            }
        )
        if completed.returncode != 0:
            errors.append(f"lake build failed with exit status {completed.returncode}")
        declaration_names = sorted(
            {
                item["declaration"]
                for item in mappings
                if isinstance(item, dict)
                and isinstance(item.get("declaration"), str)
            }
        )
        module_name = formal_mapping.get("source_file", "").replace("\\", "/")
        if module_name.endswith(".lean"):
            module_name = module_name[:-5].replace("/", ".")
        check_source = "\n".join(
            [f"import {module_name}", *(f"#check {name}" for name in declaration_names)]
        ) + "\n"
        check_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".lean",
                prefix="ProofDagMappingCheck_",
                dir=project_dir,
                delete=False,
            ) as handle:
                handle.write(check_source)
                check_path = Path(handle.name)
            checked = subprocess.run(
                ["lake", "env", "lean", str(check_path)],
                cwd=project_dir,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            build["declaration_check"] = {
                "count": len(declaration_names),
                "exit_status": checked.returncode,
                "passed": checked.returncode == 0,
            }
            if checked.returncode != 0:
                build["declaration_check"]["stdout_tail"] = checked.stdout[-2000:]
                build["declaration_check"]["stderr_tail"] = checked.stderr[-2000:]
                errors.append("Lean #check failed for mapped declarations")
        finally:
            if check_path is not None:
                check_path.unlink(missing_ok=True)
    else:
        recorded_ok = (
            formal_mapping.get("exit_status") == 0
            and formal_mapping.get("result") == "compiled"
        )
        build.update({"passed": recorded_ok, "source": "recorded_evidence"})
        if not recorded_ok:
            warnings.append("No successful recorded Lean build")

    total = len(inferences)
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "formal_backend": "lean",
        "formal_coverage": coverage,
        "source_file": str(source_file),
        "source_declaration_count": len(source_declarations),
        "mapped_inference_count": len(mapped),
        "total_inference_count": total,
        "inference_coverage": len(mapped) / total if total else 1.0,
        "unmapped_inference_ids": unmapped,
        "build": build,
        "semantic_translation_automatically_proved": False,
    }


def check_mutation(candidate: dict[str, Any]) -> dict[str, Any]:
    errors = validate_json_schema(candidate) + validate_graph(candidate)
    evaluation: dict[str, Any] | None = None
    if not errors:
        evaluation = evaluate_graph(candidate)
        if not evaluation.get("first_break_match"):
            errors.append("computed First Break differs from declared value")
        mutation = candidate["mutation"]
        target_effect = (
            "target_preserving"
            if evaluation["all_targets_derivable"]
            else "target_breaking"
        )
        if target_effect != mutation["target_effect"]:
            errors.append("computed target effect differs from declared value")
        intrinsic_invalid = [
            item["inference_id"]
            for item in evaluation["inference_evaluations"]
            if item["intrinsic_status"] == "invalid"
        ]
        anchor = mutation["injection_anchor"]
        if anchor.get("type") == "inference":
            if intrinsic_invalid != [anchor.get("id")]:
                errors.append(
                    "candidate must have exactly one primary intrinsically invalid "
                    "Inference"
                )
    return {
        "passed": not errors,
        "errors": errors,
        "computed_first_break": (
            evaluation.get("computed_first_break") if evaluation else None
        ),
        "first_break_match": (
            evaluation.get("first_break_match") if evaluation else False
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True)
    parser.add_argument("--formal-mapping", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--candidate-graph")
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    graph = read_graph(args.graph)
    schema_errors = validate_json_schema(graph)
    semantic_errors = validate_graph(graph)
    evaluation = evaluate_graph(graph) if not semantic_errors else None
    mapping = read_json(args.formal_mapping)
    formal = check_formal_mapping(
        graph, mapping, Path(args.project).resolve(), args.run_build
    )
    mutation = (
        check_mutation(read_graph(args.candidate_graph))
        if args.candidate_graph
        else {"passed": True, "status": "not_applicable", "errors": []}
    )
    report = {
        "graph_id": graph.get("graph_id"),
        "schema_version": graph.get("schema_version"),
        "automatic_checks": {
            "dag_schema_validation": {
                "passed": not schema_errors,
                "errors": schema_errors,
            },
            "dag_structural_validation": {
                "passed": not semantic_errors,
                "errors": semantic_errors,
            },
            "dag_derivability_validation": {
                "passed": bool(evaluation and evaluation["all_targets_derivable"]),
                "errors": (
                    []
                    if evaluation and evaluation["all_targets_derivable"]
                    else ["reference target is not derivable"]
                ),
            },
            "scope_structural_validation": (
                evaluation["scope_check"]
                if evaluation
                else {"passed": False, "violations": []}
            ),
            "formal_mapping": formal,
            "mutation_structural_validation": mutation,
        },
        "human_only_checks": {
            "proof_review": "not automatically proved",
            "dag_semantic_faithfulness_review": "not automatically proved",
            "scope_semantic_review": "not automatically proved",
            "formal_translation_review": "not automatically proved",
            "mutation_semantic_review": "not automatically proved",
            "student_text_graph_consistency_review": "not automatically proved",
        },
    }
    report["all_automatic_checks_passed"] = all(
        check["passed"] for check in report["automatic_checks"].values()
    )
    write_json(report, args.output)
    return 0 if report["all_automatic_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
