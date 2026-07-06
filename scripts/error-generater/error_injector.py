"""Controlled mutations from a correct SPU DAG to a wrong SPU DAG."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from random import Random
from typing import Any

from dag_build import edges_from_spus
from spu_quality import is_good_error_target
from target_selector import select_target_spu


TAXONOMY_PATH = Path(__file__).with_name("error_taxonomy.json")

ERROR_TYPE_ALIASES = {
    "missing_step": "missing_dependency",
    "invalid_dependency": "wrong_dependency",
    "case_missing": "missing_case",
    "case_omission": "missing_case",
    "invalid_theorem_use": "wrong_theorem",
}


def canonicalize_error_type(error_type: str | None) -> str:
    if not error_type:
        return ""
    return ERROR_TYPE_ALIASES.get(error_type, error_type)


def load_error_taxonomy(path: str | Path = TAXONOMY_PATH) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def taxonomy_by_name(taxonomy: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for item in taxonomy:
        name = canonicalize_error_type(item["name"])
        canonical = dict(item)
        canonical["name"] = name
        aliases = set(canonical.get("aliases", []))
        aliases.add(item["name"])
        canonical["aliases"] = sorted(aliases)
        by_name[name] = canonical
        for alias in aliases:
            by_name[alias] = canonical
    return by_name


def inject_error(
    correct_spus: list[dict[str, Any]],
    error_type: str = "auto",
    taxonomy: list[dict[str, Any]] | None = None,
    rng: Random | None = None,
) -> dict[str, Any]:
    taxonomy = taxonomy or load_error_taxonomy()
    by_name = taxonomy_by_name(taxonomy)
    rng = rng or Random(0)

    if error_type == "auto":
        ordered_names = [
            "missing_dependency",
            "wrong_theorem",
            "false_claim",
            "missing_case",
            "sign_error",
            "wrong_dependency",
        ]
    else:
        ordered_names = [canonicalize_error_type(error_type)]

    for name in ordered_names:
        if name not in by_name:
            continue
        target = select_target_spu(correct_spus, by_name[name], rng=rng)
        if target is None:
            continue
        mutation = _apply_named_mutation(correct_spus, name, target, rng)
        if mutation is not None:
            return mutation

    raise ValueError("No applicable error injection could be generated.")


def _apply_named_mutation(
    correct_spus: list[dict[str, Any]],
    error_type: str,
    target: dict[str, Any],
    rng: Random,
) -> dict[str, Any] | None:
    error_type = canonicalize_error_type(error_type)
    if error_type == "missing_dependency":
        return _missing_step(correct_spus, target, error_type, rng)
    if error_type == "wrong_theorem":
        return _wrong_theorem(correct_spus, target, rng)
    if error_type == "false_claim":
        return _false_claim(correct_spus, target, rng)
    if error_type == "missing_case":
        return _case_missing(correct_spus, target, error_type)
    if error_type == "sign_error":
        return _sign_error(correct_spus, target)
    if error_type == "wrong_dependency":
        return _invalid_dependency(correct_spus, target, error_type, rng)
    if error_type == "circular_reasoning":
        return _circular_reasoning(correct_spus, target)
    if error_type == "invalid_wlog":
        return _text_mutation(correct_spus, target, error_type, _invalid_wlog_text, rng)
    if error_type == "overgeneralization":
        return _text_mutation(correct_spus, target, error_type, _overgeneralize_text, rng)
    if error_type == "domain_error":
        return _text_mutation(correct_spus, target, error_type, _domain_error_text, rng)
    if error_type == "quantifier_error":
        return _text_mutation(correct_spus, target, error_type, _quantifier_error_text, rng)
    if error_type == "unproved_existence":
        return _text_mutation(correct_spus, target, error_type, _unproved_existence_text, rng)
    if error_type == "case_overlap":
        return _text_mutation(correct_spus, target, error_type, _case_overlap_text, rng)
    if error_type == "diagram_assumption":
        return _text_mutation(correct_spus, target, error_type, _diagram_assumption_text, rng)
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
    error_type: str = "missing_dependency",
    rng: Random | None = None,
) -> dict[str, Any] | None:
    rng = rng or Random(0)
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
    removed = rng.choice(deps)
    wtarget["depends_on"] = [dep for dep in wtarget.get("depends_on", []) if dep != removed]
    return _base_payload(
        wrong,
        error_type,
        wtarget["id"],
        f"Removed necessary dependency {removed} from SPU {wtarget['id']}.",
    )


def _wrong_theorem(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    rng: Random,
) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    wtarget = _find(wrong, target["id"])
    original = wtarget["text"]
    wtarget["text"] = _replace_theorem_text(original, rng)
    return _base_payload(
        wrong,
        "wrong_theorem",
        wtarget["id"],
        "Replaced the theorem/rule used in the target step with a similar but invalid one.",
    )


def _replace_theorem_text(text: str, rng: Random) -> str:
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
    return text + " " + rng.choice(
        [
            "The converse of the same theorem gives the needed implication.",
            "The reverse implication of this criterion can be applied here.",
            "This criterion also works in the opposite direction in the present setting.",
        ]
    )


def _false_claim(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    rng: Random,
) -> dict[str, Any]:
    wrong = copy.deepcopy(spus)
    idx = _index_of(wrong, target["id"])
    false_id = _next_id(wrong, "F")
    false_spu = {
        "id": false_id,
        "text": rng.choice(
            [
                "The strongest local pattern must persist through the remaining cases.",
                "The extremal configuration found here is representative of every possible configuration.",
                "The same relation may be used for the unresolved part of the proof.",
            ]
        ),
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
    error_type: str = "missing_case",
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
    if not wrong:
        return None
    first_bad = next(
        (
            spu["id"]
            for spu in spus
            if spu["id"] not in remove_ids
            and any(dep in remove_ids for dep in spu.get("depends_on", []))
        ),
        None,
    )
    if first_bad is None:
        first_bad = next(
            (spu["id"] for spu in wrong if spu.get("type") == "Final"),
            wrong[-1]["id"],
        )
    for spu in wrong:
        spu["depends_on"] = [dep for dep in spu.get("depends_on", []) if dep not in remove_ids]

    return _base_payload(
        wrong,
        error_type,
        first_bad,
        f"Removed case branch beginning at {target['id']}.",
    )


def _sign_error(spus: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any] | None:
    wrong = copy.deepcopy(spus)
    wtarget = _find(wrong, target["id"])
    changed = _flip_sign_or_inequality(wtarget["text"])
    if changed is None:
        return None
    wtarget["text"] = changed
    return _base_payload(
        wrong,
        "sign_error",
        wtarget["id"],
        "Changed an algebraic sign or inequality direction in the target SPU.",
    )


def _flip_sign_or_inequality(text: str) -> str | None:
    ordered_replacements = [
        ("\\le", "\\ge"),
        ("\\ge", "\\le"),
        ("≤", "≥"),
        ("≥", "≤"),
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
    return None


def _invalid_dependency(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    error_type: str = "wrong_dependency",
    rng: Random | None = None,
) -> dict[str, Any] | None:
    rng = rng or Random(0)
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
    wrong_dep = rng.choice(candidates)
    wtarget["depends_on"] = _dedupe([wrong_dep] + wtarget.get("depends_on", []))
    return _base_payload(
        wrong,
        error_type,
        wtarget["id"],
        f"Added logically irrelevant dependency {wrong_dep} to SPU {wtarget['id']}.",
    )


def _circular_reasoning(spus: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any] | None:
    wrong = copy.deepcopy(spus)
    final = next((spu for spu in reversed(wrong) if spu.get("type") == "Final"), wrong[-1])
    target_ids = {
        spu["id"]
        for spu in wrong
        if spu.get("id") != final.get("id") and is_good_error_target(spu)
    }
    if not target_ids:
        return None
    if target.get("id") not in target_ids:
        target = _best_circular_target([spu for spu in wrong if spu["id"] in target_ids])
    wtarget = _find(wrong, target["id"])
    if final["id"] in wtarget.get("depends_on", []):
        return None
    wtarget["depends_on"] = _dedupe([final["id"]] + wtarget.get("depends_on", []))
    return _base_payload(
        wrong,
        "circular_reasoning",
        wtarget["id"],
        f"Made {wtarget['id']} depend on final conclusion {final['id']}.",
    )


def _best_circular_target(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    type_score = {"TheoremUse": 4, "Lemma": 3, "Algebra": 2, "Claim": 1, "Case": 1}
    return sorted(
        candidates,
        key=lambda spu: (
            type_score.get(spu.get("type", ""), 0),
            len(str(spu.get("text", ""))),
        ),
        reverse=True,
    )[0]


def _text_mutation(
    spus: list[dict[str, Any]],
    target: dict[str, Any],
    error_type: str,
    mutator,
    rng: Random,
) -> dict[str, Any] | None:
    wrong = copy.deepcopy(spus)
    wtarget = _find(wrong, target["id"])
    old_text = wtarget.get("text", "")
    new_text = mutator(old_text, rng)
    if not new_text or new_text == old_text:
        return None
    wtarget["text"] = new_text
    return _base_payload(
        wrong,
        error_type,
        wtarget["id"],
        f"Changed SPU {wtarget['id']} from '{old_text}' to '{wtarget['text']}'.",
    )


def _invalid_wlog_text(text: str, rng: Random) -> str:
    if re.search(r"without loss of generality|wlog", text, re.I):
        return text + " " + rng.choice(
            [
                "No separate symmetry argument is needed for the other orderings.",
                "The remaining arrangements behave the same way after relabeling.",
                "This reduction covers the other configurations automatically.",
            ]
        )
    return rng.choice(
        [
            "Without loss of generality, impose this special configuration.",
            "We may assume this ordering from now on.",
            "It is enough to handle this particular arrangement.",
        ]
    )


def _overgeneralize_text(text: str, rng: Random) -> str:
    return text + " " + rng.choice(
        [
            "The same conclusion then extends to the remaining cases.",
            "This representative case is enough for the general situation.",
            "No additional distinction is needed for the other possibilities.",
            "The argument applies unchanged once the local pattern is present.",
        ]
    )


def _domain_error_text(text: str, rng: Random) -> str:
    return text + " " + rng.choice(
        [
            "We may divide by the relevant expression at this point.",
            "The usual inequality applies to these terms directly.",
            "The formula can be used here without separating boundary cases.",
            "The denominator is harmless for the argument.",
        ]
    )


def _quantifier_error_text(text: str, rng: Random) -> str:
    if re.search(r"\bfor all\b|\bevery\b|all ", text, re.I):
        return re.sub(r"\bfor all\b|\bevery\b|all ", "for some ", text, count=1, flags=re.I)
    return text + " " + rng.choice(
        [
            "A single valid choice is enough to establish the assertion.",
            "Once one object has the property, the claimed statement follows.",
            "The constructed instance represents the full quantifier.",
        ]
    )


def _unproved_existence_text(text: str, rng: Random) -> str:
    return text + " " + rng.choice(
        [
            "Choose an object satisfying the needed property.",
            "Take the required point with this relation.",
            "Select such a parameter and continue with the proof.",
            "Let the desired construction be available.",
        ]
    )


def _case_overlap_text(text: str, rng: Random) -> str:
    if re.search(r"\bcase\b|if |suppose", text, re.I):
        return text + " " + rng.choice(
            [
                "This case also accounts for the remaining possibilities.",
                "The boundary between this case and the next one causes no issue.",
                "The same situation covers the adjacent alternatives.",
            ]
        )
    return rng.choice(
        [
            "Split into this case and its complement; any overlap is harmless.",
            "These cases cover the proof even though their boundary is shared.",
            "It remains only to consider this case and the complementary one.",
        ]
    )


def _diagram_assumption_text(text: str, rng: Random) -> str:
    return text + " " + rng.choice(
        [
            "The diagram indicates the required incidence relation.",
            "The configuration shows the needed parallelism.",
            "The relative position of the points makes this relation apparent.",
            "The drawn figure gives the angle relation we need.",
        ]
    )


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
