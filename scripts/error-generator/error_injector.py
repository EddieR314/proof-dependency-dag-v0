"""Controlled mutations from a correct SPU DAG to a wrong SPU DAG."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from dag_build import edges_from_spus
from target_selector import select_target_spu


TAXONOMY_PATH = Path(__file__).with_name("error_taxonomy.json")


def load_error_taxonomy(path: str | Path = TAXONOMY_PATH) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inject_error(
    correct_spus: list[dict[str, Any]],
    error_type: str = "auto",
    taxonomy: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    taxonomy = taxonomy or load_error_taxonomy()
    taxonomy_by_name = {item["name"]: item for item in taxonomy}

    if error_type == "auto":
        ordered_names = [
            "missing_step",
            "wrong_theorem",
            "false_claim",
            "case_missing",
            "sign_error",
            "invalid_dependency",
        ]
    else:
        ordered_names = [error_type]

    for name in ordered_names:
        if name not in taxonomy_by_name:
            continue
        target = select_target_spu(correct_spus, taxonomy_by_name[name])
        if target is None:
            continue
        mutation = _apply_named_mutation(correct_spus, name, target)
        if mutation is not None:
            return mutation

    raise ValueError("No applicable error injection could be generated.")


def _apply_named_mutation(
    correct_spus: list[dict[str, Any]],
    error_type: str,
    target: dict[str, Any],
) -> dict[str, Any] | None:
    if error_type in {"missing_step", "missing_dependency"}:
        return _missing_step(correct_spus, target, error_type)
    if error_type == "wrong_theorem":
        return _wrong_theorem(correct_spus, target)
    if error_type == "false_claim":
        return _false_claim(correct_spus, target)
    if error_type in {"case_missing", "missing_case"}:
        return _case_missing(correct_spus, target, error_type)
    if error_type == "sign_error":
        return _sign_error(correct_spus, target)
    if error_type in {"invalid_dependency", "wrong_dependency"}:
        return _invalid_dependency(correct_spus, target, error_type)
    if error_type == "circular_reasoning":
        return _circular_reasoning(correct_spus, target)
    if error_type == "invalid_wlog":
        return _text_mutation(correct_spus, target, error_type, _invalid_wlog_text)
    if error_type == "overgeneralization":
        return _text_mutation(correct_spus, target, error_type, _overgeneralize_text)
    if error_type == "domain_error":
        return _text_mutation(correct_spus, target, error_type, _domain_error_text)
    if error_type == "quantifier_error":
        return _text_mutation(correct_spus, target, error_type, _quantifier_error_text)
    if error_type == "unproved_existence":
        return _text_mutation(correct_spus, target, error_type, _unproved_existence_text)
    if error_type == "case_overlap":
        return _text_mutation(correct_spus, target, error_type, _case_overlap_text)
    if error_type == "diagram_assumption":
        return _text_mutation(correct_spus, target, error_type, _diagram_assumption_text)
    return None


def _base_payload(
    wrong_spus: list[dict[str, Any]],
    error_type: str,
    target_spu_id: str,
    description: str,
) -> dict[str, Any]:
    return {
        "wrong_spus": wrong_spus,
        "wrong_edges": edges_from_spus(wrong_spus),
        "first_break": {"spu_id": target_spu_id, "break_type": error_type},
        "injected_error": {
            "error_type": error_type,
            "target_spu_id": target_spu_id,
            "description": description,
        },
    }


def _missing_step(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    error_type: str = "missing_step",
) -> dict[str, Any] | None:
    wrong = copy.deepcopy(spus)
    by_id = {spu["id"]: spu for spu in wrong}
    target_id = target["id"]
    internal_ids = {spu["id"] for spu in wrong}
    if len([dep for dep in by_id[target_id].get("depends_on", []) if dep in internal_ids]) < 2:
        better = next(
            (
                spu
                for spu in wrong
                if spu.get("type") in {"TheoremUse", "Claim", "Algebra", "Lemma"}
                and len([dep for dep in spu.get("depends_on", []) if dep in internal_ids]) >= 2
            ),
            None,
        )
        if better is None:
            return None
        target_id = better["id"]
    wtarget = by_id[target_id]
    deps = [dep for dep in wtarget.get("depends_on", []) if dep not in {"problem", "given"}]
    if not deps:
        return None
    removed = deps[0]
    wtarget["depends_on"] = [dep for dep in wtarget.get("depends_on", []) if dep != removed]
    return _base_payload(
        wrong,
        error_type,
        wtarget["id"],
        f"Removed necessary dependency {removed} from SPU {wtarget['id']}.",
    )


def _wrong_theorem(spus: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    wtarget = _find(wrong, target["id"])
    original = wtarget["text"]
    wtarget["text"] = _replace_theorem_text(original)
    return _base_payload(
        wrong,
        "wrong_theorem",
        wtarget["id"],
        "Replaced the theorem/rule used in the target step with a similar but invalid one.",
    )


def _replace_theorem_text(text: str) -> str:
    replacements = [
        (r"\bSSS\b", "AAA"),
        (r"\bSAS\b", "SSA"),
        (r"\bAM-GM\b", "the arithmetic mean is always equal to the geometric mean"),
        (r"\bgcd\b", "lcm"),
        (r"\bdivides\b", "is divisible by"),
        (r"\bmodulo\b", "ordinary equality after division"),
    ]
    for pattern, repl in replacements:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return re.sub(pattern, repl, text, count=1, flags=re.IGNORECASE)
    return text + " This follows by applying the converse of the previous theorem."


def _false_claim(spus: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    idx = _index_of(wrong, target["id"])
    false_id = _next_id(wrong, "F")
    false_spu = {
        "id": false_id,
        "text": "We now use the fact that the strongest local pattern must hold in all remaining cases.",
        "type": "Claim",
        "depends_on": list(target.get("depends_on", [])) or ["problem"],
    }
    wrong.insert(idx, false_spu)
    wtarget = _find(wrong, target["id"])
    wtarget["depends_on"] = _dedupe([false_id] + wtarget.get("depends_on", []))
    return _base_payload(
        wrong,
        "false_claim",
        false_id,
        f"Inserted unsupported claim {false_id} and made {target['id']} depend on it.",
    )


def _case_missing(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    error_type: str = "case_missing",
) -> dict[str, Any] | None:
    case_indices = [i for i, spu in enumerate(spus) if spu.get("type") == "Case"]
    if not case_indices:
        return None

    target_idx = _index_of(spus, target["id"])
    if target_idx not in case_indices:
        target_idx = case_indices[-1]
        target = spus[target_idx]

    next_case_indices = [i for i in case_indices if i > target_idx]
    end = next_case_indices[0] if next_case_indices else len(spus) - 1

    remove_ids = {spu["id"] for spu in spus[target_idx:end] if spu.get("type") != "Final"}
    if not remove_ids:
        return None

    wrong = [copy.deepcopy(spu) for spu in spus if spu["id"] not in remove_ids]
    for spu in wrong:
        spu["depends_on"] = [dep for dep in spu.get("depends_on", []) if dep not in remove_ids]

    surviving_target = wrong[min(target_idx, len(wrong) - 1)]["id"]
    return _base_payload(
        wrong,
        error_type,
        surviving_target,
        f"Removed case branch beginning at {target['id']}.",
    )


def _sign_error(spus: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    wtarget = _find(wrong, target["id"])
    wtarget["text"] = _flip_sign_or_inequality(wtarget["text"])
    return _base_payload(
        wrong,
        "sign_error",
        wtarget["id"],
        "Changed an algebraic sign or inequality direction in the target SPU.",
    )


def _flip_sign_or_inequality(text: str) -> str:
    ordered_replacements = [
        ("\\le", "\\ge"),
        ("\\ge", "\\le"),
        ("<=", ">="),
        (">=", "<="),
        ("<", ">"),
        (">", "<"),
        (" - ", " + "),
        ("+", "-"),
    ]
    for old, new in ordered_replacements:
        if old in text:
            return text.replace(old, new, 1)
    return text + " after changing the sign of one term."


def _invalid_dependency(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    error_type: str = "invalid_dependency",
) -> dict[str, Any] | None:
    wrong = copy.deepcopy(spus)
    allowed_types = {"TheoremUse", "Claim", "Algebra", "Lemma"}
    ids = [spu["id"] for spu in wrong]
    if len(ids) < 3:
        return None
    target_id = target["id"]
    if _find(wrong, target_id).get("type") not in allowed_types:
        better = next((spu for spu in wrong if spu.get("type") in allowed_types), None)
        if better is None:
            return None
        target_id = better["id"]
    target_idx = _index_of(wrong, target_id)
    candidates = [
        sid
        for sid in ids[:target_idx]
        if sid != target_id and sid not in _find(wrong, target_id).get("depends_on", [])
    ]
    if not candidates:
        for i, spu in enumerate(wrong):
            prior_candidates = [
                sid
                for sid in ids[:i]
                if sid != spu["id"] and sid not in spu.get("depends_on", [])
            ]
            if prior_candidates and spu.get("type") in allowed_types:
                target_id = spu["id"]
                target_idx = i
                candidates = prior_candidates
                break
    if not candidates:
        return None
    wtarget = _find(wrong, target_id)
    wrong_dep = candidates[-1]
    wtarget["depends_on"] = _dedupe([wrong_dep] + wtarget.get("depends_on", []))
    return _base_payload(
        wrong,
        error_type,
        wtarget["id"],
        f"Added logically irrelevant dependency {wrong_dep} to SPU {wtarget['id']}.",
    )


def _circular_reasoning(spus: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    final = next((spu for spu in reversed(wrong) if spu.get("type") == "Final"), wrong[-1])
    wtarget = _find(wrong, target["id"])
    wtarget["depends_on"] = _dedupe([final["id"]] + wtarget.get("depends_on", []))
    return _base_payload(
        wrong,
        "circular_reasoning",
        wtarget["id"],
        f"Made {wtarget['id']} depend on final conclusion {final['id']}.",
    )


def _text_mutation(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    error_type: str,
    mutator,
) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    wtarget = _find(wrong, target["id"])
    old_text = wtarget.get("text", "")
    wtarget["text"] = mutator(old_text)
    return _base_payload(
        wrong,
        error_type,
        wtarget["id"],
        f"Changed SPU {wtarget['id']} from '{old_text}' to '{wtarget['text']}'.",
    )


def _invalid_wlog_text(text: str) -> str:
    if re.search(r"without loss of generality|wlog", text, re.I):
        return text + " We do not need to justify this reduction, since the variables can always be renamed."
    return "Without loss of generality, we impose this special configuration, even though the problem is not symmetric."


def _overgeneralize_text(text: str) -> str:
    return text + " Therefore the same conclusion holds in all remaining cases without further checking."


def _domain_error_text(text: str) -> str:
    return text + " We may divide by the relevant expression and apply the theorem without checking whether it is nonzero or positive."


def _quantifier_error_text(text: str) -> str:
    if re.search(r"\bfor all\b|\bevery\b|all ", text, re.I):
        return re.sub(r"\bfor all\b|\bevery\b|all ", "for some ", text, count=1, flags=re.I)
    return text + " Since this works for one choice, it works for every choice."


def _unproved_existence_text(text: str) -> str:
    return text + " Choose the required object with this property; its existence is clear."


def _case_overlap_text(text: str) -> str:
    if re.search(r"\bcase\b|if |suppose", text, re.I):
        return text + " This case also covers the remaining possibilities."
    return "Split into this case and its complement, and note that they overlap only harmlessly."


def _diagram_assumption_text(text: str) -> str:
    return text + " From the diagram, the needed relation is visually clear."


def _find(spus: list[dict[str, Any]], sid: str) -> dict[str, Any]:
    for spu in spus:
        if spu["id"] == sid:
            return spu
    raise KeyError(sid)


def _index_of(spus: list[dict[str, Any]], sid: str) -> int:
    for i, spu in enumerate(spus):
        if spu["id"] == sid:
            return i
    raise KeyError(sid)


def _next_id(spus: list[dict[str, Any]], prefix: str) -> str:
    used = {spu["id"] for spu in spus}
    i = 1
    while f"{prefix}{i}" in used:
        i += 1
    return f"{prefix}{i}"


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
