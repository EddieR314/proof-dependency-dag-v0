"""Heuristics for filtering noisy or non-mathematical SPUs."""

from __future__ import annotations

import re
from typing import Any


BAD_TEXT_PATTERNS = (
    r"\bcid:\d+\b",
    r"\(cid:\d+\)",
    r"\ufffd",
    r"�",
    r"□",
)

COMMENTARY_PATTERNS = (
    r"^\s*remark\.?\s*$",
    r"^\s*note\.?\s*$",
    r"\bsource\b",
    r"\breference\b",
    r"\banecdote\b",
    r"\bcomment\b",
    r"\bfirst solution\b",
    r"\bsecond solution\b",
    r"\bsolution using\b",
    r"\bgood diagram\b",
    r"\bdiagram should betray\b",
    r"\bunsurprisingly\b",
    r"\bmain point of the problem\b",
    r"\bwe omit\b",
    r"\bleft to the reader\b",
    r"\bclaim\.?\s*$",
    r"^\s*setup\.?\s*$",
    r"^\s*\(?\s*setup\.?\s*$",
)

MATH_SIGNAL_PATTERNS = (
    r"[=<>≤≥∠∥⊥∑∏√∞≡∈∉⊂⊆∪∩]",
    r"\\[a-zA-Z]+",
    r"\btherefore\b",
    r"\bhence\b",
    r"\bthus\b",
    r"\bso\b",
    r"\bimplies\b",
    r"\bfollows\b",
    r"\bprove\b",
    r"\bshown?\b",
    r"\bconclude\b",
    r"\bclaim\b",
    r"\blemma\b",
    r"\btheorem\b",
    r"\bcase\b",
    r"\bsuppose\b",
    r"\bassume\b",
    r"\blet\b",
    r"\bchoose\b",
    r"\bdefine\b",
    r"\bconstruct\b",
    r"\bdivide\b",
    r"\bmodulo\b",
    r"\bcongru",
    r"\bdivis",
    r"\bgcd\b",
    r"\bprime\b",
    r"\binteger\b",
    r"\bpositive\b",
    r"\btriangle\b",
    r"\bcircle\b",
    r"\bpoint\b",
    r"\bline\b",
    r"\bsegment\b",
    r"\btangent\b",
    r"\bcyclic\b",
    r"\bharmonic\b",
    r"\borthogon",
    r"\bmidpoint\b",
    r"\bbisect",
    r"\bangle\b",
    r"\bequal\b",
    r"\binequal",
    r"\bparallel\b",
    r"\bperpendicular\b",
    r"\bpolynomial\b",
    r"\bsequence\b",
    r"\bset\b",
    r"\bgraph\b",
    r"\bchain\b",
    r"\bblock\b",
)

DISALLOWED_TARGET_TYPES = {"Given", "Final", "Remark", "Comment", "Citation", "Source"}
PREFERRED_MATH_TYPES = {"TheoremUse", "Claim", "Algebra", "Lemma", "Case"}


def normalize_spu_text(text: str) -> str:
    text = str(text or "")
    replacements = {
        "\u00ad": "",
        "\ufeff": "",
        "Conse- quently": "Consequently",
        "conse- quently": "consequently",
        "L.H.S.": "left-hand side",
        "R.H.S.": "right-hand side",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return text


def quality_issues(spu: dict[str, Any], *, target_context: bool = False) -> list[str]:
    text = normalize_spu_text(spu.get("text", ""))
    lowered = text.lower()
    issues: list[str] = []

    if not text:
        return ["empty_spu_text"]
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in BAD_TEXT_PATTERNS):
        issues.append("malformed_or_cid_text")
    if _ocr_garbage_ratio(text) > 0.18:
        issues.append("high_ocr_garbage_ratio")
    if any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in COMMENTARY_PATTERNS):
        issues.append("commentary_or_source_note")
    if target_context and re.search(r"^\s*(?:\d+\s+)?(?:we\s+)?call\b.+\ba\b.+", lowered):
        issues.append("definition_only_target")
    if target_context and len(_wordish_tokens(text)) < 6:
        issues.append("too_short_for_error_target")
    if not has_math_signal(text):
        issues.append("low_math_signal")
    stype = str(spu.get("type", ""))
    if target_context and stype in DISALLOWED_TARGET_TYPES:
        issues.append("disallowed_target_type")
    return issues


def is_usable_spu(spu: dict[str, Any]) -> bool:
    hard = {
        "empty_spu_text",
        "malformed_or_cid_text",
        "high_ocr_garbage_ratio",
        "commentary_or_source_note",
    }
    return not any(issue in hard for issue in quality_issues(spu, target_context=False))


def is_good_error_target(spu: dict[str, Any]) -> bool:
    return not quality_issues(spu, target_context=True) and str(spu.get("type", "")) in PREFERRED_MATH_TYPES


def has_math_signal(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in MATH_SIGNAL_PATTERNS)


def clean_or_drop_spu(spu: dict[str, Any]) -> dict[str, Any] | None:
    cleaned = dict(spu)
    cleaned["text"] = normalize_spu_text(cleaned.get("text", ""))
    if not is_usable_spu(cleaned):
        return None
    return cleaned


def _wordish_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9α-ωΑ-Ω]+", text)


def _ocr_garbage_ratio(text: str) -> float:
    if not text:
        return 1.0
    suspicious = len(re.findall(r"[_|{}[\]~^`]", text))
    suspicious += len(re.findall(r"\b[A-Z]\s+[A-Z]\s+[A-Z]\b", text))
    suspicious += len(re.findall(r"\d\s+\d\s+\d", text))
    return suspicious / max(1, len(text))
