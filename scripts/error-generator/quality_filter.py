"""Quality checks for generated wrong-solution samples."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from wrong_solution_writer import REVEALING_PHRASES


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


def validate_generated_sample(sample: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    first_break = sample.get("first_break", {})
    injected = sample.get("injected_error", {})
    wrong_spus = sample.get("wrong_spus", [])
    wrong_solution = sample.get("wrong_solution", "")
    error_type = injected.get("error_type")
    first_break_detail = sample.get("first_break_detail", {})
    diff = sample.get("diff", {})

    wrong_record = {
        "sample_id": sample.get("sample_id", "generated_sample"),
        "spus": wrong_spus,
        "first_break": first_break,
    }

    eval_mod = _load_eval_module()
    if eval_mod is not None:
        if hasattr(eval_mod, "validate_record_schema"):
            schema_errors = eval_mod.validate_record_schema(wrong_record, side="generated")
        elif hasattr(eval_mod, "validate_generated_record"):
            schema_errors = eval_mod.validate_generated_record(wrong_record)
        else:
            schema_errors = _minimal_schema_errors(wrong_record)
        if schema_errors:
            errors.append({"type": "schema_errors", "errors": schema_errors})

        if error_type != "circular_reasoning" and eval_mod.has_cycle(wrong_record):
            errors.append({"type": "unexpected_cycle"})

        if not eval_mod.first_break_exists(wrong_record):
            errors.append({"type": "first_break_missing"})

        try:
            dep_errors = eval_mod.dependency_errors(wrong_record, allow_forward_dependency=True)
        except TypeError:
            dep_errors = eval_mod.dependency_errors(wrong_record)
        blocking_dep_errors = [
            err for err in dep_errors if _dependency_error_type(err) == "unknown_dependency"
        ]
        if blocking_dep_errors:
            errors.append({"type": "dependency_errors", "errors": blocking_dep_errors})
    else:
        if not _first_break_exists_local(wrong_record):
            errors.append({"type": "first_break_missing"})

    if not isinstance(first_break, dict) or not first_break.get("spu_id"):
        errors.append({"type": "missing_first_break"})
    if not isinstance(injected, dict) or not injected.get("target_spu_id"):
        errors.append({"type": "missing_injected_error"})
    elif first_break.get("spu_id") != injected.get("target_spu_id"):
        errors.append({"type": "first_break_target_mismatch"})

    if not _exactly_one_first_break(first_break, injected):
        errors.append({"type": "not_exactly_one_intended_first_break"})

    target_spu = _find_spu(wrong_spus, first_break.get("spu_id"))
    if target_spu and isinstance(first_break_detail, dict):
        if first_break_detail.get("spu_text") != target_spu.get("text", ""):
            errors.append({"type": "first_break_detail_text_mismatch"})
    else:
        errors.append({"type": "missing_first_break_detail"})

    if not _diff_is_nonempty(diff, error_type):
        errors.append({"type": "empty_diff_for_non_rhetorical_error"})

    if error_type in STRUCTURAL_ERROR_TYPES and not _has_structural_diff(diff):
        errors.append({"type": "structural_error_without_structural_diff"})

    if not _error_type_compatible(error_type, target_spu):
        errors.append(
            {
                "type": "incompatible_error_type",
                "error_type": error_type,
                "target_spu_type": target_spu.get("type") if target_spu else None,
            }
        )

    if not sample.get("wrong_solution_steps"):
        errors.append({"type": "missing_wrong_solution_steps"})

    if _reveals_error(wrong_solution):
        errors.append({"type": "revealing_wrong_solution_text"})

    return len(errors) == 0, errors


def _load_eval_module():
    root = Path(__file__).resolve().parent
    for path in (
        root.parent / "spu_utils.py",
        root.parent / "eval_spu_dependency.py",
        root / "spu_utils.py",
    ):
        if not path.exists():
            continue
        spec = importlib.util.spec_from_file_location("spu_eval_module", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None


def _first_break_exists_local(record: dict[str, Any]) -> bool:
    sid = record.get("first_break", {}).get("spu_id")
    return sid in {spu.get("id") for spu in record.get("spus", [])}


def _dependency_error_type(error: Any) -> str | None:
    if isinstance(error, dict):
        return error.get("type") or error.get("error")
    if isinstance(error, (list, tuple)) and error:
        return str(error[-1])
    return None


def _minimal_schema_errors(record: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    spus = record.get("spus", [])
    if not isinstance(spus, list):
        return [{"type": "invalid_spus_type"}]

    seen: set[str] = set()
    for index, spu in enumerate(spus):
        if not isinstance(spu, dict):
            errors.append({"type": "invalid_spu_type", "index": index})
            continue
        sid = spu.get("id")
        if not sid:
            errors.append({"type": "missing_spu_id", "index": index})
        elif sid in seen:
            errors.append({"type": "duplicate_spu_id", "spu_id": sid})
        else:
            seen.add(sid)
        if "text" not in spu:
            errors.append({"type": "missing_spu_text", "spu_id": sid})
        if not isinstance(spu.get("depends_on", []), list):
            errors.append({"type": "invalid_depends_on", "spu_id": sid})

    if not record.get("first_break", {}).get("spu_id"):
        errors.append({"type": "missing_first_break"})
    return errors


def _reveals_error(text: str) -> bool:
    lowered = str(text).lower()
    return any(phrase in lowered for phrase in REVEALING_PHRASES)


def _find_spu(spus: list[dict[str, Any]], spu_id: str | None) -> dict[str, Any] | None:
    for spu in spus:
        if spu.get("id") == spu_id:
            return spu
    return None


def _exactly_one_first_break(first_break: dict[str, Any], injected: dict[str, Any]) -> bool:
    return (
        isinstance(first_break, dict)
        and isinstance(injected, dict)
        and bool(first_break.get("spu_id"))
        and first_break.get("spu_id") == injected.get("target_spu_id")
    )


def _diff_is_nonempty(diff: dict[str, Any], error_type: str | None) -> bool:
    rhetorical_errors = set()
    if error_type in rhetorical_errors:
        return True
    if not isinstance(diff, dict):
        return False
    return bool(
        diff.get("changed_spus")
        or diff.get("inserted_spus")
        or diff.get("deleted_spus")
        or diff.get("changed_edges", {}).get("added")
        or diff.get("changed_edges", {}).get("removed")
    )


def _has_structural_diff(diff: dict[str, Any]) -> bool:
    if not isinstance(diff, dict):
        return False
    edge_diff = diff.get("changed_edges", {})
    return bool(
        diff.get("inserted_spus")
        or diff.get("deleted_spus")
        or edge_diff.get("added")
        or edge_diff.get("removed")
    )


def _error_type_compatible(error_type: str | None, target_spu: dict[str, Any] | None) -> bool:
    if not error_type or not target_spu:
        return False
    taxonomy = _load_taxonomy()
    entry = taxonomy.get(error_type)
    if not entry:
        return False
    suitable = set(entry.get("suitable_spu_types", []))
    return not suitable or target_spu.get("type") in suitable


def _load_taxonomy() -> dict[str, dict[str, Any]]:
    path = Path(__file__).resolve().with_name("error_taxonomy.json")
    if not path.exists():
        return {}
    return {entry["name"]: entry for entry in json.loads(path.read_text(encoding="utf-8"))}
