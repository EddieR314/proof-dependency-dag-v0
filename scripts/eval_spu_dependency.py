import argparse
import json

from spu_utils import (
    case_scope_errors,
    dependency_closure_errors,
    dependency_errors,
    first_break_exists,
    has_cycle,
    read_jsonl,
)


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
        closure_errs = dependency_closure_errors(pred)
        scope_errs = case_scope_errors(pred)

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
            "dependency_errors": dep_errs,
            "closure_ok": not closure_errs,
            "closure_error_count": len(closure_errs),
            "closure_errors": closure_errs,
            "case_scope_ok": not scope_errs,
            "case_scope_error_count": len(scope_errs),
            "case_scope_errors": scope_errs,
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
        "closure_ok_rate": sum(r.get("closure_ok", False) for r in rows) / n,
        "case_scope_ok_rate": sum(r.get("case_scope_ok", False) for r in rows) / n,
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
