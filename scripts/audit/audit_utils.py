#!/usr/bin/env python3
"""Shared helpers for human auditing of synthetic wrong-solution samples."""

from __future__ import annotations

import json
import csv
import importlib.util
from collections import deque
from pathlib import Path
from typing import Any, Iterable


SPECIAL_DEPS = {"problem", "given", "definition"}
STRUCTURAL_ERROR_TYPES = {
    "missing_step",
    "missing_dependency",
    "wrong_dependency",
    "invalid_dependency",
    "case_missing",
    "missing_case",
    "circular_reasoning",
    "false_claim",
}
REVIEW_ALLOWED_VALUES = {
    "first_break_valid": ["yes", "no", "unclear"],
    "break_type_valid": ["yes", "no", "unclear"],
    "single_error_valid": ["yes", "no", "unclear"],
    "usable_as_gold": ["yes", "no", "revise"],
}
HUMAN_REVIEW_FIELDS = [
    "first_break_valid",
    "correct_first_break_spu_id",
    "break_type_valid",
    "correct_break_type",
    "single_error_valid",
    "solution_naturalness_1_to_5",
    "mathematical_plausibility_before_break_1_to_5",
    "post_break_consistency_1_to_5",
    "usable_as_gold",
    "reviewer_notes",
]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Bad JSON on line {line_no} in {path}: {exc}") from exc
    return records


def read_audit_tasks(path: str | Path) -> list[dict[str, Any]]:
    """Read reviewed audit tasks from JSONL or the CSV emitted by the sampler."""
    path = Path(path)
    if path.suffix.lower() != ".csv":
        return read_jsonl(path)

    tasks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(
                {
                    "sample_id": row.get("sample_id", ""),
                    "problem_id": row.get("problem_id", ""),
                    "topic": row.get("topic", ""),
                    "error_type": row.get("error_type", ""),
                    "break_type": row.get("break_type", ""),
                    "generator_name": row.get("generator_name", ""),
                    "difficulty": row.get("difficulty", ""),
                    "structural_error_type": row.get("structural_error_type", ""),
                    "problem": row.get("problem", ""),
                    "correct_solution": row.get("correct_solution", ""),
                    "wrong_solution": row.get("wrong_solution", ""),
                    "wrong_solution_steps": parse_json_cell(
                        row.get("wrong_solution_steps_json", ""), []
                    ),
                    "generated_first_break": parse_json_cell(
                        row.get("generated_first_break_json", ""), {}
                    ),
                    "injected_error": parse_json_cell(row.get("injected_error_json", ""), {}),
                    "evaluator_result": parse_json_cell(
                        row.get("evaluator_result_json", ""), {}
                    ),
                    "human_review": {
                        field: row.get(field, "") for field in HUMAN_REVIEW_FIELDS
                    },
                }
            )
    return tasks


def parse_json_cell(value: str, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def write_jsonl(records: Iterable[dict[str, Any]], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_nested(record: dict[str, Any], *keys: str, default: Any = "") -> Any:
    cur: Any = record
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return cur


def field_value(record: dict[str, Any], field: str) -> str:
    if field == "error_type":
        return str(record.get("error_type") or get_nested(record, "injected_error", "error_type"))
    if field == "break_type":
        return str(
            record.get("break_type")
            or get_nested(record, "first_break", "break_type")
            or get_nested(record, "first_break_detail", "break_type")
        )
    if field == "generator_name":
        return str(record.get("generator_name") or get_nested(record, "metadata", "generator"))
    if field == "structural_error_type":
        return str(
            record.get("structural_error_type")
            or get_nested(record, "injected_error", "structural_error_type")
            or structural_error_type(record)
        )
    if field == "warning_flag":
        warnings = evaluator_result(record).get("evaluator_warnings", [])
        return "|".join(sorted(str(w.get("type", w)) for w in warnings)) if warnings else ""
    if field == "quality_warning_flag":
        warnings = evaluator_result(record).get("quality_warnings", [])
        return "|".join(sorted(str(w.get("type", w)) for w in warnings)) if warnings else ""
    if field == "first_break_spu_type":
        return first_break_spu(record).get("type", "")
    if field == "long_proof":
        return "yes" if proof_length(record) >= 30 else "no"
    value = record.get(field, "")
    return "" if value is None else str(value)


def structural_error_type(record: dict[str, Any]) -> str:
    error_type = field_value(record, "error_type")
    if error_type in STRUCTURAL_ERROR_TYPES:
        return error_type
    return ""


def normalized_sample_id(record: dict[str, Any], fallback_index: int = 0) -> str:
    return str(record.get("sample_id") or f"sample_{fallback_index:06d}")


def normalized_wrong_steps(record: dict[str, Any]) -> list[dict[str, Any]]:
    wrong_spus = {
        str(spu.get("id")): spu
        for spu in record.get("wrong_spus", [])
        if isinstance(spu, dict) and spu.get("id") is not None
    }
    steps = record.get("wrong_solution_steps") or record.get("wrong_spus") or []
    normalized: list[dict[str, Any]] = []

    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            continue
        spu_id = str(step.get("spu_id") or step.get("id") or f"S{index}")
        spu = wrong_spus.get(spu_id, {})
        normalized.append(
            {
                "spu_id": spu_id,
                "text": step.get("text", spu.get("text", "")),
                "type": step.get("type", spu.get("type", "")),
                "depends_on": step.get("depends_on", spu.get("depends_on", [])),
            }
        )
    return normalized


def first_break_spu(record: dict[str, Any]) -> dict[str, Any]:
    first_break = record.get("first_break")
    sid = first_break.get("spu_id") if isinstance(first_break, dict) else ""
    for key in ("wrong_spus", "correct_spus"):
        for spu in record.get(key, []) or []:
            if isinstance(spu, dict) and spu.get("id") == sid:
                return spu
    return {}


def proof_length(record: dict[str, Any]) -> int:
    for key in ("correct_spus", "wrong_spus", "wrong_solution_steps"):
        value = record.get(key)
        if isinstance(value, list) and value:
            return len(value)
    return 0


def generated_first_break(record: dict[str, Any]) -> dict[str, Any]:
    detail = record.get("first_break_detail") if isinstance(record.get("first_break_detail"), dict) else {}
    first_break = record.get("first_break") if isinstance(record.get("first_break"), dict) else {}
    injected = record.get("injected_error") if isinstance(record.get("injected_error"), dict) else {}
    return {
        "spu_id": detail.get("spu_id") or first_break.get("spu_id") or injected.get("target_spu_id") or "",
        "break_type": detail.get("break_type") or first_break.get("break_type") or injected.get("error_type") or "",
        "why_wrong": detail.get("why_wrong") or injected.get("description") or "",
    }


def make_human_review() -> dict[str, str]:
    return {field: "" for field in HUMAN_REVIEW_FIELDS}


def make_audit_task(record: dict[str, Any], fallback_index: int = 0) -> dict[str, Any]:
    return {
        "sample_id": normalized_sample_id(record, fallback_index),
        "problem_id": str(record.get("problem_id", "")),
        "topic": field_value(record, "topic"),
        "error_type": field_value(record, "error_type"),
        "break_type": field_value(record, "break_type"),
        "generator_name": field_value(record, "generator_name"),
        "difficulty": field_value(record, "difficulty"),
        "structural_error_type": field_value(record, "structural_error_type"),
        "first_break_spu_type": field_value(record, "first_break_spu_type"),
        "proof_spu_count": proof_length(record),
        "problem": record.get("problem", ""),
        "correct_solution": record.get("correct_solution", ""),
        "wrong_solution": record.get("wrong_solution", ""),
        "wrong_solution_steps": normalized_wrong_steps(record),
        "generated_first_break": generated_first_break(record),
        "injected_error": record.get("injected_error", {}),
        "evaluator_result": evaluator_result(record),
        "human_review": make_human_review(),
    }


def evaluator_result(record: dict[str, Any]) -> dict[str, Any]:
    existing = record.get("evaluator_result")
    if isinstance(existing, dict):
        return {
            "dag_ok": bool(existing.get("dag_ok", True)),
            "case_scope_ok": bool(existing.get("case_scope_ok", True)),
            "dependency_closure_ok": bool(existing.get("dependency_closure_ok", True)),
            "first_break_exists": bool(existing.get("first_break_exists", True)),
            "evaluator_warnings": list(existing.get("evaluator_warnings", [])),
            "quality_warnings": list(existing.get("quality_warnings", [])),
        }

    wrong_spus = record.get("wrong_spus", [])
    first_break = record.get("first_break", {})
    warnings: list[dict[str, Any]] = []

    schema_warnings = schema_errors(record)
    warnings.extend(schema_warnings)

    dag_ok = not has_cycle(wrong_spus)
    if not dag_ok:
        warnings.append({"type": "dag_structure_check_failed"})

    dep_errors = dependency_errors(wrong_spus)
    dependency_closure_ok = not dep_errors
    if dep_errors:
        warnings.append({"type": "dependency_closure_check_failed", "errors": dep_errors})

    fb_exists = first_break_exists(wrong_spus, first_break)
    if not fb_exists:
        warnings.append({"type": "first_break_existence_check_failed"})

    quality_errors = get_nested(record, "metadata", "quality_errors", default=[])
    if not isinstance(quality_errors, list):
        quality_errors = []
    warnings.extend({"type": "quality_warning", "detail": err} for err in quality_errors)
    quality_warnings = spu_quality_warnings(record)

    case_warnings = [
        warning
        for warning in warnings
        if "case" in str(warning.get("type", "")).lower()
        or "case" in json.dumps(warning, ensure_ascii=False).lower()
    ]
    case_scope_ok = not case_warnings

    return {
        "dag_ok": dag_ok,
        "case_scope_ok": case_scope_ok,
        "dependency_closure_ok": dependency_closure_ok,
        "first_break_exists": fb_exists,
        "evaluator_warnings": warnings,
        "quality_warnings": quality_warnings,
    }


def spu_quality_warnings(record: dict[str, Any]) -> list[dict[str, Any]]:
    module = _load_spu_quality_module()
    if module is None:
        return []
    warnings: list[dict[str, Any]] = []
    hard = {
        "empty_spu_text",
        "malformed_or_cid_text",
        "high_ocr_garbage_ratio",
        "commentary_or_source_note",
    }
    for spu in record.get("wrong_spus", []) or []:
        if not isinstance(spu, dict):
            continue
        issues = module.quality_issues(spu, target_context=False)
        hard_issues = [issue for issue in issues if issue in hard]
        if hard_issues:
            warnings.append(
                {
                    "type": "low_quality_spu",
                    "spu_id": spu.get("id"),
                    "issues": hard_issues,
                }
            )
    target = first_break_spu(record)
    if target:
        issues = module.quality_issues(target, target_context=True)
        if issues:
            warnings.append(
                {
                    "type": "low_quality_first_break_spu",
                    "spu_id": target.get("id"),
                    "issues": issues,
                }
            )
    return warnings


def _load_spu_quality_module():
    path = Path(__file__).resolve().parent.parent / "error-generator" / "spu_quality.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("audit_spu_quality", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_errors(record: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not record.get("sample_id"):
        errors.append({"type": "missing_sample_id"})
    if not isinstance(record.get("wrong_spus"), list):
        errors.append({"type": "missing_wrong_spus"})
    if not isinstance(record.get("first_break"), dict):
        errors.append({"type": "missing_first_break"})
    return errors


def dependency_errors(spus: list[Any]) -> list[dict[str, Any]]:
    valid = [spu for spu in spus if isinstance(spu, dict) and isinstance(spu.get("id"), str)]
    ids = [spu["id"] for spu in valid]
    id_set = set(ids)
    seen: set[str] = set()
    errors: list[dict[str, Any]] = []

    for spu in valid:
        sid = spu["id"]
        deps = spu.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append({"type": "invalid_depends_on_type", "spu_id": sid})
            deps = []
        for dep in deps:
            if not isinstance(dep, str):
                errors.append({"type": "invalid_dependency_type", "spu_id": sid, "dependency": dep})
            elif dep in SPECIAL_DEPS or dep.startswith("external:"):
                continue
            elif dep not in id_set:
                errors.append({"type": "unknown_dependency", "spu_id": sid, "dependency": dep})
            elif dep not in seen:
                errors.append({"type": "forward_dependency", "spu_id": sid, "dependency": dep})
        seen.add(sid)
    return errors


def has_cycle(spus: list[Any]) -> bool:
    valid = [spu for spu in spus if isinstance(spu, dict) and isinstance(spu.get("id"), str)]
    ids = [spu["id"] for spu in valid]
    graph = {sid: [] for sid in ids}
    indegree = {sid: 0 for sid in ids}
    id_set = set(ids)

    for spu in valid:
        sid = spu["id"]
        deps = spu.get("depends_on", [])
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if dep in id_set:
                graph[dep].append(sid)
                indegree[sid] += 1

    queue = deque([sid for sid in ids if indegree[sid] == 0])
    seen = 0
    while queue:
        sid = queue.popleft()
        seen += 1
        for nxt in graph[sid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return seen != len(ids)


def first_break_exists(spus: list[Any], first_break: Any) -> bool:
    if not isinstance(first_break, dict):
        return False
    sid = first_break.get("spu_id")
    return isinstance(sid, str) and sid in {
        spu.get("id") for spu in spus if isinstance(spu, dict)
    }


def is_warning_sample(record: dict[str, Any]) -> bool:
    result = evaluator_result(record)
    if result.get("evaluator_warnings"):
        return True
    return not (
        result.get("dag_ok")
        and result.get("case_scope_ok")
        and result.get("dependency_closure_ok")
        and result.get("first_break_exists")
    )


def review_value(task: dict[str, Any], field: str) -> str:
    review = task.get("human_review", {})
    if not isinstance(review, dict):
        return ""
    return str(review.get(field, "")).strip()


def is_reviewed(task: dict[str, Any]) -> bool:
    return any(review_value(task, field) for field in HUMAN_REVIEW_FIELDS)
