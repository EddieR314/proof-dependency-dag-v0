"""Enrichment helpers for wrong-solution training samples."""

from __future__ import annotations

from typing import Any

from dag_build import edges_from_spus
from error_injector import canonicalize_error_type


STRUCTURAL_ERROR_TYPES = {
    "missing_dependency",
    "wrong_dependency",
    "missing_case",
    "circular_reasoning",
    "false_claim",
}


TEXT_ONLY_ERROR_TYPES = {
    "wrong_theorem",
    "sign_error",
    "domain_error",
    "quantifier_error",
    "overgeneralization",
    "diagram_assumption",
    "unproved_existence",
    "case_overlap",
}


WRONG_FINAL_ANSWER_TYPES = {
    "sign_error",
    "missing_case",
    "overgeneralization",
    "domain_error",
    "case_overlap",
}


SUBTLETY = {
    "missing_dependency": 3,
    "wrong_dependency": 4,
    "wrong_theorem": 2,
    "false_claim": 3,
    "missing_case": 3,
    "sign_error": 2,
    "circular_reasoning": 4,
    "overgeneralization": 4,
    "domain_error": 4,
    "quantifier_error": 4,
    "unproved_existence": 3,
    "case_overlap": 4,
    "invalid_wlog": 5,
    "diagram_assumption": 3,
}


def wrong_solution_steps(wrong_spus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "step_number": idx + 1,
            "spu_id": spu.get("id"),
            "text": spu.get("text", ""),
        }
        for idx, spu in enumerate(wrong_spus)
    ]


def build_diff(
    correct_spus: list[dict[str, Any]],
    wrong_spus: list[dict[str, Any]],
) -> dict[str, Any]:
    correct_by_id = {spu["id"]: spu for spu in correct_spus}
    wrong_by_id = {spu["id"]: spu for spu in wrong_spus}
    correct_ids = set(correct_by_id)
    wrong_ids = set(wrong_by_id)

    changed_spus = []
    for sid in sorted(correct_ids & wrong_ids, key=_id_sort_key):
        old = correct_by_id[sid]
        new = wrong_by_id[sid]
        changes = {}
        if old.get("text") != new.get("text"):
            changes["old_text"] = old.get("text", "")
            changes["new_text"] = new.get("text", "")
        if old.get("depends_on", []) != new.get("depends_on", []):
            changes["old_depends_on"] = old.get("depends_on", [])
            changes["new_depends_on"] = new.get("depends_on", [])
        if changes:
            changed_spus.append({"spu_id": sid, **changes})

    inserted_spus = [
        wrong_by_id[sid] for sid in sorted(wrong_ids - correct_ids, key=_id_sort_key)
    ]
    deleted_spus = [
        correct_by_id[sid] for sid in sorted(correct_ids - wrong_ids, key=_id_sort_key)
    ]

    correct_edges = {_edge_tuple(edge) for edge in edges_from_spus(correct_spus)}
    wrong_edges = {_edge_tuple(edge) for edge in edges_from_spus(wrong_spus)}
    added_edges = sorted(wrong_edges - correct_edges)
    removed_edges = sorted(correct_edges - wrong_edges)
    changed_edges = {
        "added": [{"source": a, "target": b} for a, b in added_edges],
        "removed": [{"source": a, "target": b} for a, b in removed_edges],
    }

    parts = []
    if changed_spus:
        parts.append(f"changed {len(changed_spus)} SPU(s)")
    if inserted_spus:
        parts.append(f"inserted {len(inserted_spus)} SPU(s)")
    if deleted_spus:
        parts.append(f"deleted {len(deleted_spus)} SPU(s)")
    if added_edges or removed_edges:
        parts.append(
            f"changed edges (+{len(added_edges)}, -{len(removed_edges)})"
        )
    description = "; ".join(parts) if parts else "no structural or text diff detected"

    return {
        "changed_spus": changed_spus,
        "inserted_spus": inserted_spus,
        "deleted_spus": deleted_spus,
        "changed_edges": changed_edges,
        "description": description,
    }


def build_first_break_detail(
    wrong_spus: list[dict[str, Any]],
    first_break: dict[str, Any],
    injected_error: dict[str, Any],
) -> dict[str, Any]:
    spu_id = first_break.get("spu_id")
    target = next((spu for spu in wrong_spus if spu.get("id") == spu_id), {})
    break_type = canonicalize_error_type(first_break.get("break_type") or injected_error.get("error_type"))
    why_wrong = injected_error.get("description", "")
    minimal_fix = minimal_fix_for_error(break_type, injected_error)
    return {
        "spu_id": spu_id,
        "spu_text": target.get("text", ""),
        "break_type": break_type,
        "why_wrong": why_wrong,
        "minimal_fix": minimal_fix,
    }


def expected_feedback_for_error(
    first_break_detail: dict[str, Any],
    injected_error: dict[str, Any],
) -> dict[str, str]:
    break_type = canonicalize_error_type(first_break_detail.get("break_type", ""))
    diagnosis = first_break_detail.get("why_wrong") or f"The step has a {break_type} error."
    minimal_fix = first_break_detail.get("minimal_fix", "")
    missing_reasoning = _missing_reasoning_for_error(break_type, injected_error)
    return {
        "diagnosis": diagnosis,
        "minimal_fix": minimal_fix,
        "missing_reasoning": missing_reasoning,
    }


def minimal_fix_for_error(error_type: str, injected_error: dict[str, Any]) -> str:
    error_type = canonicalize_error_type(error_type)
    target = injected_error.get("target_spu_id", "the target step")
    if error_type == "missing_dependency":
        return f"Restore the omitted prerequisite before using {target}."
    if error_type == "wrong_dependency":
        return f"Replace the irrelevant dependency with the actual premise needed for {target}."
    if error_type == "wrong_theorem":
        return "Use a theorem whose hypotheses match the established premises."
    if error_type == "false_claim":
        return "Either prove the inserted claim or remove it from the proof."
    if error_type == "missing_case":
        return "Add the omitted case branch and aggregate all cases only after every branch is proved."
    if error_type == "sign_error":
        return "Correct the sign, inequality direction, or arithmetic transformation at the marked step."
    if error_type == "circular_reasoning":
        return "Remove the dependence on the final conclusion and prove the step from earlier facts."
    if error_type == "overgeneralization":
        return "Restrict the claim to the conditions actually proved, or prove the general version."
    if error_type == "domain_error":
        return "Verify the expression or theorem is valid on the stated domain before applying it."
    if error_type == "quantifier_error":
        return "Fix the universal/existential quantifier and prove the statement at the required strength."
    if error_type == "unproved_existence":
        return "Construct the required object or prove it exists before using it."
    if error_type == "case_overlap":
        return "Make the cases disjoint and prove that their union covers all possibilities."
    if error_type == "invalid_wlog":
        return "Justify the WLOG reduction by symmetry or handle the non-symmetric cases separately."
    if error_type == "diagram_assumption":
        return "Replace the diagram-based assumption with a proved geometric relation."
    return "Repair the marked step so it follows from earlier SPUs."


def classify_difficulty(error_type: str, variant: str) -> tuple[str, int]:
    error_type = canonicalize_error_type(error_type)
    subtlety = SUBTLETY.get(error_type, 3)
    if variant == "wrong_final_answer" and subtlety <= 2:
        difficulty = "easy"
    elif subtlety <= 2:
        difficulty = "medium"
    elif subtlety == 3:
        difficulty = "medium"
    elif subtlety == 4:
        difficulty = "hard"
    else:
        difficulty = "adversarial"
    return difficulty, subtlety


def classify_variant(error_type: str) -> str:
    error_type = canonicalize_error_type(error_type)
    if error_type in WRONG_FINAL_ANSWER_TYPES:
        return "wrong_final_answer"
    return "invalid_proof_same_answer"


def _missing_reasoning_for_error(error_type: str, injected_error: dict[str, Any]) -> str:
    error_type = canonicalize_error_type(error_type)
    if error_type in STRUCTURAL_ERROR_TYPES:
        return "The dependency graph does not supply the required earlier support for the marked SPU."
    if error_type in TEXT_ONLY_ERROR_TYPES:
        return "The local mathematical statement must be justified or corrected while preserving the dependency structure."
    return injected_error.get("description", "")


def _edge_tuple(edge: dict[str, str]) -> tuple[str, str]:
    return edge["source"], edge["target"]


def _id_sort_key(value: str) -> tuple[str, int | str]:
    prefix = "".join(ch for ch in value if not ch.isdigit())
    suffix = "".join(ch for ch in value if ch.isdigit())
    return prefix, int(suffix) if suffix else value
