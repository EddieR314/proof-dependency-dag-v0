"""Build a first-pass logical dependency DAG over SPUs."""

from __future__ import annotations

import copy
import re
from typing import Any


SOURCE_TYPES = {"Given", "Construction"}
REASONING_TYPES = {"Claim", "TheoremUse", "Algebra", "Lemma", "Case"}


def build_dependency_dag(spus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fill each SPU's depends_on with a conservative heuristic dependency set."""
    result = copy.deepcopy(spus)
    previous_reasoning: list[str] = []
    last_case_id: str | None = None
    token_sets = [_math_tokens(spu.get("text", "")) for spu in result]

    for i, spu in enumerate(result):
        sid = spu["id"]
        stype = spu.get("type", "Claim")
        deps = _clean_existing_deps(spu.get("depends_on", []), sid)

        if i == 0 and not deps:
            deps = ["problem"] if stype != "Given" else []
        elif not deps:
            deps = _infer_deps(result, i, previous_reasoning, last_case_id, token_sets)

        spu["depends_on"] = _dedupe_preserve_order(deps)

        if stype == "Case":
            last_case_id = sid
        if stype in REASONING_TYPES or stype == "Final":
            previous_reasoning.append(sid)

    return result


def _clean_existing_deps(deps: Any, own_id: str) -> list[str]:
    if not isinstance(deps, list):
        return []
    return [dep for dep in deps if isinstance(dep, str) and dep != own_id]


def _infer_deps(
    spus: list[dict[str, Any]],
    index: int,
    previous_reasoning: list[str],
    last_case_id: str | None,
    token_sets: list[set[str]],
) -> list[str]:
    spu = spus[index]
    stype = spu.get("type", "Claim")
    text = spu.get("text", "")
    prior = spus[:index]

    if stype == "Given":
        return []

    if stype == "Construction":
        return ["problem"]

    if stype == "Case":
        return [previous_reasoning[-1]] if previous_reasoning else ["problem"]

    deps: list[str] = []

    referenced = _referenced_prior_spus(text, prior, token_sets[index], token_sets[:index])
    deps.extend(referenced[-2:])

    if last_case_id and stype in {"Claim", "TheoremUse", "Algebra", "Lemma"}:
        deps.append(last_case_id)

    if not referenced and previous_reasoning:
        deps.append(previous_reasoning[-1])

    if stype == "Final" and len(previous_reasoning) >= 2:
        deps.extend(previous_reasoning[-2:])

    if not deps:
        deps.append("problem")

    return deps


def _referenced_prior_spus(
    text: str,
    prior: list[dict[str, Any]],
    tokens: set[str] | None = None,
    prior_token_sets: list[set[str]] | None = None,
) -> list[str]:
    refs = []
    tokens = tokens if tokens is not None else _math_tokens(text)
    prior_token_sets = prior_token_sets or [_math_tokens(spu.get("text", "")) for spu in prior]
    if not tokens:
        return refs
    for spu, prior_tokens in zip(prior, prior_token_sets):
        if tokens & prior_tokens:
            refs.append(spu["id"])
    return refs


LAYOUT_LATEX_COMMANDS = {
    "frac",
    "left",
    "right",
    "cdot",
    "times",
    "mathbb",
    "mathrm",
    "operatorname",
    "begin",
    "end",
    "text",
}
NOISY_SINGLE_LETTERS = {"a", "i"}


def _math_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for command in re.findall(r"\\([A-Za-z]+)", text):
        command = command.lower()
        if command not in LAYOUT_LATEX_COMMANDS:
            tokens.add(f"\\{command}")
    tokens.update(token.lower() for token in re.findall(r"\b[A-Za-z]\d+\b", text))
    tokens.update(token for token in re.findall(r"\b[A-Z]{1,4}\b", text))
    for token in re.findall(r"\b[a-z]\b", text):
        if token not in NOISY_SINGLE_LETTERS:
            tokens.add(token)
    return tokens


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def edges_from_spus(spus: list[dict[str, Any]]) -> list[dict[str, str]]:
    edges = []
    ids = {spu["id"] for spu in spus}
    for spu in spus:
        sid = spu["id"]
        for dep in spu.get("depends_on", []):
            if dep in ids:
                edges.append({"source": dep, "target": sid})
    return edges
