#!/usr/bin/env python3
"""Build a human-review packet for the algebra calibration proofs."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return records


def extract_sections(paths: list[Path]) -> dict[str, str]:
    sections: dict[str, str] = {}
    heading = re.compile(r"^## ([A-Za-z0-9_-]+)\s*$", re.MULTILINE)
    supplemental_heading = re.compile(
        r"^# Supplemental Complex Calibration: ([A-Za-z0-9_-]+)\s*$",
        re.MULTILINE,
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        matches = list(heading.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[match.group(1)] = text[match.end() : end].strip()
        supplemental = supplemental_heading.search(text)
        if supplemental:
            sections[supplemental.group(1)] = text[supplemental.end() :].strip()
    return sections


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    data = root / "data" / "algebra_skill_curriculum"

    with (data / "calibration_reviewed_v0.2.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        problems = list(csv.DictReader(handle))

    reviews = {
        record["problem_id"]: record
        for record in read_jsonl(data / "calibration_reviews_v0.1.jsonl")
    }
    reviews.update(
        {
            record["problem_id"]: record
            for record in read_jsonl(data / "supplemental_reviews_v0.1.jsonl")
        }
    )

    draft_paths = sorted(data.glob("*draft*.md"))
    drafts = extract_sections(draft_paths)

    missing_reviews = sorted({row["problem_id"] for row in problems} - set(reviews))
    if missing_reviews:
        raise ValueError(f"missing review metadata: {missing_reviews}")

    packet_path = data / "human_review_13_proofs_v0.1.md"
    result_path = data / "human_review_13_results_v0.1.csv"

    lines = [
        "# 代数专家 Skill：13 道校准证明人工审核册 v0.1",
        "",
        "## 使用说明",
        "",
        "- 本文件用于人工审核，不代表这些证明已经通过。",
        "- 每题必须核对题面、参考证明、Codex 路由、方法模式、风险点和 SPU。",
        "- 只有审核人实际读过相应材料后才能勾选；不得依据自动汇总直接签字。",
        "- `blind draft provenance` 为 `missing` 时，表示原始 Codex 盲解正文未保留，",
        "  不能勾选“盲解与参考解一致”；应记为 `needs_revision`，直至补回原始正文",
        "  或重新生成并明确标记为新一轮 blind run。",
        "- 本轮只审核自然语言证明层，不等同于 DAG、mutation 或 Lean 已通过。",
        "",
        "## 总表",
        "",
        "| # | Problem ID | 模块 | Blind draft | 人工结论 | 审核人 | 日期 |",
        "|---:|---|---|---|---|---|---|",
    ]

    result_rows = []
    for index, row in enumerate(problems, 1):
        problem_id = row["problem_id"]
        draft_status = "available" if problem_id in drafts else "missing"
        lines.append(
            f"| {index} | `{problem_id}` | `{row['algebra_module']}` | "
            f"`{draft_status}` | `pending` |  |  |"
        )
        result_rows.append(
            {
                "problem_id": problem_id,
                "normalized_hash": row["normalized_hash"],
                "blind_draft_provenance": draft_status,
                "statement_correct": "",
                "reference_proof_correct": "",
                "blind_proof_correct": "",
                "route_correct": "",
                "pattern_correct": "",
                "risk_flags_correct": "",
                "spu_reasonable": "",
                "decision": "pending",
                "reviewer": "",
                "review_date": "",
                "notes": "",
            }
        )

    for index, row in enumerate(problems, 1):
        problem_id = row["problem_id"]
        review = reviews[problem_id]
        route = review["routing"]
        pattern_lines = [
            f"- `{item['name']}`：{item['evidence']}"
            for item in review.get("patterns", [])
        ]
        failure_lines = [
            f"- `{item['name']}`：候选首错为“{item['first_break_candidate']}”；"
            f"真实性 `{item['realism']}`。"
            for item in review.get("failure_modes", [])
        ]
        spu_lines = [
            f"{item['source_order']}. {item['claim']}"
            for item in review.get("spu_proposal", [])
        ]
        blind_text = drafts.get(problem_id)

        lines.extend(
            [
                "",
                f"## {index}. `{problem_id}`",
                "",
                f"- 模块：`{row['algebra_module']}`",
                f"- 来源：{row['source']}",
                f"- 比赛：{row['competition'] or '未填写'}",
                f"- `normalized_hash`：`{row['normalized_hash']}`",
                f"- blind draft provenance："
                f"`{'available' if blind_text else 'missing'}`",
                "",
                "### 题面",
                "",
                row["statement"].strip(),
                "",
                "### 参考证明",
                "",
                row["solution"].strip(),
                "",
                "### Codex 原始盲解",
                "",
            ]
        )
        if blind_text:
            lines.append(blind_text)
        else:
            lines.append(
                "> **缺失：**仓库中没有保留该题原始 blind-draft 正文。现有自动"
                "汇总不能替代原文审核。"
            )

        lines.extend(
            [
                "",
                "### Codex 路由与方法提议",
                "",
                f"- 主模块：`{route['primary_module']}`",
                f"- 次模块：`{', '.join(route['secondary_modules']) or 'none'}`",
                f"- 自动置信度：`{route['confidence']}`",
                *pattern_lines,
                "",
                "### 候选风险点",
                "",
                *(failure_lines or ["- 无"]),
                "",
                "### 候选 SPU 骨架",
                "",
                *spu_lines,
                "",
                "### 人工审核",
                "",
                "- [ ] 题面无缺失、乱码或歧义；定义域和量词完整。",
                "- [ ] 参考证明的每个关键推理都成立，且结论确实回答原题。",
                "- [ ] 已实际阅读原始 Codex 盲解，且其数学结论与推理成立。",
                "- [ ] Codex 盲解与参考解的差异不包含未说明的逻辑缺口。",
                "- [ ] 主模块与次模块按实际证明机制分类正确。",
                "- [ ] 提炼的方法模式确实由本题支持，并具有复用价值。",
                "- [ ] 风险点是真实可能发生的错误，候选 First Break 合理。",
                "- [ ] SPU 粒度是一条规则应用一个单元，顺序和前提关系合理。",
                "",
                "**判定（只选一个）**",
                "",
                "- [ ] `passed`：自然语言证明层可进入后续 DAG 构建。",
                "- [ ] `needs_revision`：材料或证明需补充/修正后重审。",
                "- [ ] `rejected`：题目或证明不适合作为当前 Skill 证据。",
                "",
                "- 审核人：",
                "- 日期：",
                "- 修改意见/证据：",
            ]
        )

    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with result_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result_rows[0]))
        writer.writeheader()
        writer.writerows(result_rows)

    print(
        json.dumps(
            {
                "problems": len(problems),
                "packet": str(packet_path),
                "results": str(result_path),
                "blind_drafts_available": sum(
                    row["blind_draft_provenance"] == "available"
                    for row in result_rows
                ),
                "blind_drafts_missing": [
                    row["problem_id"]
                    for row in result_rows
                    if row["blind_draft_provenance"] == "missing"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
