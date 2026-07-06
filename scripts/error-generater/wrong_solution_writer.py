"""Render wrong SPUs into a natural-language attempted proof."""

from __future__ import annotations

from typing import Any

from spu_quality import normalize_spu_text

REVEALING_PHRASES = (
    "this step is wrong",
    "intentional error",
    "injected error",
    "wrong solution",
    "false on purpose",
    "deliberately",
    "after changing the sign",
    "this error",
    "the injected",
    "the intended mistake",
    "invalid step",
    "mistake is",
)


def write_wrong_solution(
    problem: str,
    wrong_spus: list[dict[str, Any]],
    style: str = "student",
) -> str:
    """Convert wrong SPUs to a normal-looking attempted proof."""
    lines = []
    for spu in wrong_spus:
        text = _clean_spu_text(spu.get("text", ""))
        if not text:
            continue
        stype = spu.get("type", "Claim")
        if stype == "Case" and not text.lower().startswith(("case", "if", "suppose", "assume")):
            text = f"Consider the case where {text[0].lower() + text[1:]}"
        elif stype == "Final" and not text.lower().startswith(("therefore", "hence", "thus")):
            text = f"Therefore, {text[0].lower() + text[1:]}"
        lines.append(text)

    solution = " ".join(lines)
    solution = _remove_revealing_phrases(solution)
    return solution.strip()


def write_wrong_solution_steps(wrong_spus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "step_number": idx + 1,
            "spu_id": spu.get("id"),
            "text": _clean_spu_text(spu.get("text", "")),
        }
        for idx, spu in enumerate(wrong_spus)
    ]


def _clean_spu_text(text: str) -> str:
    text = normalize_spu_text(text)
    if not text:
        return ""
    if text[-1] not in ".!?。":
        text += "."
    return text


def _remove_revealing_phrases(text: str) -> str:
    lowered = text.lower()
    for phrase in REVEALING_PHRASES:
        if phrase in lowered:
            text = text.replace(phrase, "")
            text = text.replace(phrase.capitalize(), "")
            lowered = text.lower()
    return " ".join(text.split())
