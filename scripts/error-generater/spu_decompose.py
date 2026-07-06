"""Heuristic SPU decomposition for olympiad-style solutions.

This first version is deliberately lightweight. It produces a useful scaffold
for downstream DAG construction and error injection; an LLM-based decomposer can
later replace `decompose_solution` without changing the rest of the pipeline.
"""

from __future__ import annotations

import re
from typing import Any

from spu_quality import clean_or_drop_spu


ALLOWED_SPU_TYPES = {
    "Given",
    "Construction",
    "Claim",
    "TheoremUse",
    "Algebra",
    "Lemma",
    "Case",
    "Final",
}


CASE_PATTERNS = (
    r"\bcase\b",
    r"\bif\b",
    r"\bsuppose\b",
    r"\bassume\b",
    r"\bwhen\b",
    r"若",
    r"如果",
    r"假设",
    r"情况",
)

THEOREM_PATTERNS = (
    r"\bby\b",
    r"\busing\b",
    r"\btheorem\b",
    r"\blemma\b",
    r"\bAM-GM\b",
    r"\bCauchy\b",
    r"\bgcd\b",
    r"\bmodulo\b",
    r"\bcongru",
    r"\bdivis",
    r"由",
    r"根据",
    r"定理",
)

ALGEBRA_PATTERNS = (
    r"=",
    r"\\le|\\ge|<=|>=|≤|≥",
    r"<|>",
    r"\d\s*[-+*/^]\s*\d|\d\s*[-+*/^]|[-+*/^]\s*\d",
    r"\bsum\b",
    r"\bproduct\b",
    r"化简",
    r"代入",
    r"整理",
)

CONSTRUCTION_PATTERNS = (
    r"\bconstruct\b",
    r"\blet\b",
    r"\bchoose\b",
    r"\btake\b",
    r"\bdefine\b",
    r"作",
    r"取",
    r"设",
)

FINAL_PATTERNS = (
    r"\btherefore\b",
    r"\bhence\b",
    r"\bthus\b",
    r"\bwe are done\b",
    r"\bthis proves\b",
    r"因此",
    r"所以",
    r"证毕",
)

COMMENTARY_PATTERNS = (
    r"^\s*remark\.?\s*$",
    r"^\s*note\.?\s*$",
    r"\bfirst solution\b",
    r"\bsecond solution\b",
    r"\bsolution using\b",
    r"\bgood diagram\b",
    r"\bsource\b",
    r"\breference\b",
)


def split_solution_text(solution: str) -> list[str]:
    """Split solution text into coarse atomic proof units."""
    normalized = re.sub(r"\r\n?", "\n", solution.strip())
    if not normalized:
        return []

    chunks: list[str] = []
    for paragraph in re.split(r"\n\s*\n+", normalized):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        bullet_parts = re.split(r"\n\s*(?:[-*•]|\d+[.)])\s+", paragraph)
        for part in bullet_parts:
            part = part.strip()
            if not part:
                continue
            chunks.extend(_split_sentences(part))

    return [chunk for chunk in chunks if chunk]


def _split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?。；;])\s+", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def classify_spu_type(text: str, index: int, total: int) -> str:
    lowered = text.lower()

    if index == total - 1:
        return "Final"
    if _matches(COMMENTARY_PATTERNS, lowered):
        return "Remark"
    if index >= max(0, total - 2) and _matches(FINAL_PATTERNS, lowered):
        return "Final"
    if index == 0 and re.search(r"\bassume\b|假设", lowered):
        return "Construction"
    if _is_case_statement(lowered):
        return "Case"
    if re.search(r"\bclaim\b|命题|断言", lowered):
        return "Claim"
    if re.search(r"\blemma\b|引理", lowered):
        return "Lemma"
    if _matches(THEOREM_PATTERNS, lowered):
        return "TheoremUse"
    if _matches(CONSTRUCTION_PATTERNS, lowered):
        return "Construction"
    if _matches(ALGEBRA_PATTERNS, text):
        return "Algebra"
    return "Claim"


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _is_case_statement(text: str) -> bool:
    return bool(
        re.search(
            r"^\s*(case\b|if\b|suppose\b|assume\b|when\b|consider the case\b|若|如果|假设|情况)",
            text,
            flags=re.IGNORECASE,
        )
        or re.search(r"\bcase\s+\d+\b|\bcase\s+[ivx]+\b", text, flags=re.IGNORECASE)
    )


def decompose_solution(
    correct_solution: str,
    problem: str | None = None,
    prefix: str = "S",
) -> list[dict[str, Any]]:
    """Convert a correct solution into SPUs with empty dependency lists."""
    chunks = split_solution_text(correct_solution)
    spus = []
    total = len(chunks)
    for idx, text in enumerate(chunks):
        spu = {
            "id": f"{prefix}{idx + 1}",
            "text": text,
            "type": classify_spu_type(text, idx, total),
            "depends_on": [],
        }
        cleaned = clean_or_drop_spu(spu)
        if cleaned is not None and cleaned.get("type") != "Remark":
            spus.append(cleaned)

    if problem and not spus:
        spus.append(
            {
                "id": f"{prefix}1",
                "text": "The proof starts from the given problem conditions.",
                "type": "Given",
                "depends_on": ["problem"],
            }
        )

    return spus
