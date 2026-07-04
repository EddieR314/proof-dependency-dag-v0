"""Select good SPU targets for controlled error injection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


TYPE_PRIORITY = {
    "TheoremUse": 5.0,
    "Claim": 4.0,
    "Case": 4.0,
    "Algebra": 3.5,
    "Lemma": 3.5,
    "Construction": 1.0,
    "Given": -5.0,
    "Final": -5.0,
}


def reachable_counts(spus: list[dict[str, Any]]) -> dict[str, int]:
    graph = defaultdict(list)
    ids = {spu["id"] for spu in spus}
    for spu in spus:
        sid = spu["id"]
        for dep in spu.get("depends_on", []):
            if dep in ids:
                graph[dep].append(sid)
    return {sid: _count_reachable(graph, sid) for sid in ids}


def _count_reachable(graph: dict[str, list[str]], start: str) -> int:
    seen = set()
    stack = list(graph.get(start, []))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, []))
    return len(seen)


def critical_nodes(spus: list[dict[str, Any]], top_fraction: float = 0.2) -> list[str]:
    counts = reachable_counts(spus)
    if not counts:
        return []
    top_k = max(1, int(len(counts) * top_fraction + 0.999))
    sorted_counts = sorted(counts.values(), reverse=True)
    cutoff = sorted_counts[min(top_k, len(sorted_counts)) - 1]
    return [sid for sid, count in counts.items() if count >= cutoff and count > 0]


def select_target_spu(
    spus: list[dict[str, Any]],
    error_type: dict[str, Any] | str | None = None,
) -> dict[str, Any] | None:
    suitable_types = None
    if isinstance(error_type, dict):
        suitable_types = set(error_type.get("suitable_spu_types", []))

    counts = reachable_counts(spus)
    critical = set(critical_nodes(spus))

    candidates = []
    for idx, spu in enumerate(spus):
        stype = spu.get("type", "Claim")
        if stype in {"Given", "Final"}:
            continue
        if suitable_types and stype not in suitable_types:
            continue

        score = TYPE_PRIORITY.get(stype, 0.0)
        score += counts.get(spu["id"], 0)
        if spu["id"] in critical:
            score += 3.0
        if spu.get("depends_on"):
            score += 1.0
        # Stable tie-break: earlier central errors tend to create clearer first breaks.
        score -= idx * 0.01
        candidates.append((score, idx, spu))

    if not candidates and suitable_types:
        return None

    if not candidates:
        fallback = [
            (TYPE_PRIORITY.get(spu.get("type", "Claim"), 0.0), idx, spu)
            for idx, spu in enumerate(spus)
            if spu.get("type") not in {"Given", "Final"}
        ]
        candidates = fallback

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][2]
