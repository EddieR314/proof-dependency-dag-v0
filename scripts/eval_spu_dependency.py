import argparse
import json
from collections import defaultdict, deque


SPECIAL_DEPS = {"problem", "given", "definition"}


def read_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Bad JSON on line {i}: {e}")
    return records


def spu_ids(record):
    return [s["id"] for s in record.get("spus", [])]


def dependency_errors(record):
    ids = spu_ids(record)
    id_set = set(ids)
    seen = set()
    errors = []

    for spu in record.get("spus", []):
        sid = spu["id"]
        for dep in spu.get("depends_on", []):
            if dep in SPECIAL_DEPS:
                continue
            if dep.startswith("external:"):
                continue
            if dep not in id_set:
                errors.append((sid, dep, "unknown_dependency"))
            elif dep not in seen:
                errors.append((sid, dep, "forward_dependency"))
        seen.add(sid)

    return errors


def has_cycle(record):
    ids = spu_ids(record)
    id_set = set(ids)

    graph = defaultdict(list)
    indeg = {sid: 0 for sid in ids}

    for spu in record.get("spus", []):
        sid = spu["id"]
        for dep in spu.get("depends_on", []):
            if dep in id_set:
                graph[dep].append(sid)
                indeg[sid] += 1

    q = deque([sid for sid in ids if indeg[sid] == 0])
    seen = 0

    while q:
        x = q.popleft()
        seen += 1
        for y in graph[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                q.append(y)

    return seen != len(ids)


def first_break_exists(record):
    fb = record.get("first_break", {})
    sid = fb.get("spu_id")
    return sid in set(spu_ids(record))


def eval_records(gold_records, pred_records):
    gold_by_id = {r["sample_id"]: r for r in gold_records}
    pred_by_id = {r["sample_id"]: r for r in pred_records}

    rows = []

    for sid, gold in gold_by_id.items():
        pred = pred_by_id.get(sid)

        if pred is None:
            rows.append({
                "sample_id": sid,
                "missing_pred": True,
                "first_break_correct": False,
                "break_type_correct": False,
                "dag_ok": False,
                "first_break_exists": False,
                "dependency_error_count": None
            })
            continue

        gold_fb = gold.get("first_break", {})
        pred_fb = pred.get("first_break", {})

        dep_errs = dependency_errors(pred)

        rows.append({
            "sample_id": sid,
            "missing_pred": False,
            "gold_first_break": gold_fb.get("spu_id"),
            "pred_first_break": pred_fb.get("spu_id"),
            "first_break_correct": gold_fb.get("spu_id") == pred_fb.get("spu_id"),
            "gold_break_type": gold_fb.get("break_type"),
            "pred_break_type": pred_fb.get("break_type"),
            "break_type_correct": gold_fb.get("break_type") == pred_fb.get("break_type"),
            "dag_ok": not has_cycle(pred),
            "first_break_exists": first_break_exists(pred),
            "dependency_error_count": len(dep_errs),
            "dependency_errors": dep_errs
        })

    return rows


def summarize(rows):
    n = len(rows)
    if n == 0:
        return {}

    return {
        "num_samples": n,
        "first_break_accuracy": sum(r["first_break_correct"] for r in rows) / n,
        "break_type_accuracy": sum(r["break_type_correct"] for r in rows) / n,
        "dag_ok_rate": sum(r["dag_ok"] for r in rows) / n,
        "first_break_exists_rate": sum(r["first_break_exists"] for r in rows) / n,
        "missing_predictions": sum(r["missing_pred"] for r in rows)
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--pred", required=True)
    args = parser.parse_args()

    gold = read_jsonl(args.gold)
    pred = read_jsonl(args.pred)

    rows = eval_records(gold, pred)
    summary = summarize(rows)

    print("SUMMARY")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\nDETAILS")
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()