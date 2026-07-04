"""Heuristic geometry object and relation extraction."""

from __future__ import annotations

import re
from typing import Any


RELATION_PATTERNS = [
    ("parallel", re.compile(r"\b([A-Z]{1,3})\s*(?:is\s*)?parallel to\s*([A-Z]{1,3})|\b([A-Z]{1,3})\s*∥\s*([A-Z]{1,3})", re.I)),
    ("perpendicular", re.compile(r"\b([A-Z]{1,3})\s*(?:is\s*)?perpendicular to\s*([A-Z]{1,3})|\b([A-Z]{1,3})\s*⊥\s*([A-Z]{1,3})", re.I)),
    ("equal_length", re.compile(r"\b([A-Z]{1,3})\s*=\s*([A-Z]{1,3})")),
    ("tangent", re.compile(r"\b([A-Z]{1,3})\s*(?:is\s*)?tangent to\s*(?:the\s*)?(?:circle\s*)?\(?([A-Z]{2,4})\)?", re.I)),
    ("concyclic", re.compile(r"\b([A-Z](?:,\s*[A-Z]){2,})\s+are\s+concyclic", re.I)),
]


def geometry_tables(problem: str, correct_spus: list[dict[str, Any]], wrong_spus: list[dict[str, Any]]) -> dict[str, Any]:
    text = " ".join([problem] + [spu.get("text", "") for spu in correct_spus + wrong_spus])
    objects = _extract_objects(text)
    relations = _extract_relations(correct_spus, wrong_spus)
    return {"objects": objects, "relations": relations}


def _extract_objects(text: str) -> list[dict[str, str]]:
    names = sorted(set(re.findall(r"\b[A-Z]\b|Gamma|Omega|\\Gamma|\\Omega", text)))
    objects = []
    for name in names:
        if name in {"I", "R", "N"}:
            continue
        objects.append(
            {
                "name": name,
                "type": _infer_object_type(name, text),
                "definition": _definition_snippet(name, text),
            }
        )
    return objects


def _infer_object_type(name: str, text: str) -> str:
    lowered = text.lower()
    if name.lower() in {"gamma", "omega", "\\gamma", "\\omega"}:
        return "circle"
    if re.search(rf"circle\s+{re.escape(name)}|{re.escape(name)}\s+circle", lowered):
        return "circle"
    if len(name) >= 2:
        return "line"
    return "point"


def _definition_snippet(name: str, text: str) -> str:
    sentences = re.split(r"(?<=[.!?。])\s+", text)
    for sentence in sentences:
        if re.search(rf"\b{re.escape(name)}\b", sentence):
            return sentence[:240]
    return ""


def _extract_relations(correct_spus: list[dict[str, Any]], wrong_spus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relations = []
    correct_text = " ".join(spu.get("text", "") for spu in correct_spus)
    wrong_text = " ".join(spu.get("text", "") for spu in wrong_spus)

    for status, text in (("proved", correct_text), ("unproved", wrong_text)):
        for relation_type, pattern in RELATION_PATTERNS:
            for match in pattern.finditer(text):
                objs = [g for g in match.groups() if g]
                if len(objs) >= 1:
                    relations.append(
                        {
                            "type": relation_type,
                            "objects": objs,
                            "status": status,
                        }
                    )

    return _dedupe_relations(relations)


def _dedupe_relations(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for rel in relations:
        key = (rel["type"], tuple(rel["objects"]), rel["status"])
        if key in seen:
            continue
        seen.add(key)
        out.append(rel)
    return out
