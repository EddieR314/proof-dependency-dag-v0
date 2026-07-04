import argparse
import json
import math
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


def is_special_dependency(dep):
    return dep in SPECIAL_DEPS or dep.startswith("external:")


def make_error(error_type, **kwargs):
    err = {"type": error_type}
    err.update(kwargs)
    return err


def validate_record_schema(record, record_index=None, side=None):
    """Return schema errors without dropping optional fields from the record."""
    errors = []

    location = {}
    if record_index is not None:
        location["record_index"] = record_index
    if side is not None:
        location["side"] = side

    if "sample_id" not in record:
        errors.append(make_error("missing_sample_id", **location))

    if "spus" not in record:
        errors.append(make_error("missing_spus", **location))
        spus = []
    else:
        spus = record.get("spus")
        if not isinstance(spus, list):
            errors.append(make_error("invalid_spus_type", **location))
            spus = []

    if "first_break" not in record:
        errors.append(make_error("missing_first_break", **location))

    seen_ids = set()
    duplicate_ids = set()

    for idx, spu in enumerate(spus):
        spu_location = dict(location)
        spu_location["spu_index"] = idx

        if not isinstance(spu, dict):
            errors.append(make_error("invalid_spu_type", **spu_location))
            continue

        sid = spu.get("id")
        if "id" not in spu:
            errors.append(make_error("missing_spu_id", **spu_location))
        elif sid in seen_ids:
            duplicate_ids.add(sid)
            errors.append(
                make_error("duplicate_spu_id", spu_id=sid, **spu_location)
            )
        else:
            seen_ids.add(sid)

        if "text" not in spu:
            errors.append(make_error("missing_spu_text", spu_id=sid, **spu_location))

        if "depends_on" not in spu:
            errors.append(make_error("missing_depends_on", spu_id=sid, **spu_location))
        elif not isinstance(spu.get("depends_on"), list):
            errors.append(
                make_error(
                    "invalid_depends_on_type",
                    spu_id=sid,
                    actual_type=type(spu.get("depends_on")).__name__,
                    **spu_location,
                )
            )
        else:
            for dep_index, dep in enumerate(spu.get("depends_on", [])):
                if not isinstance(dep, str):
                    errors.append(
                        make_error(
                            "invalid_depends_on_type",
                            spu_id=sid,
                            dep_index=dep_index,
                            actual_type=type(dep).__name__,
                            **spu_location,
                        )
                    )

    return errors


def spu_ids(record):
    ids = []
    for spu in record.get("spus", []):
        if isinstance(spu, dict) and "id" in spu:
            ids.append(spu["id"])
    return ids


def valid_spus(record):
    return [
        spu
        for spu in record.get("spus", [])
        if isinstance(spu, dict) and isinstance(spu.get("id"), str)
    ]


def safe_depends_on(spu):
    deps = spu.get("depends_on", [])
    if not isinstance(deps, list):
        return []
    return [dep for dep in deps if isinstance(dep, str)]


def dependency_errors(record, allow_forward_dependency=False):
    ids = spu_ids(record)
    id_set = set(ids)
    seen = set()
    errors = []

    for spu in valid_spus(record):
        sid = spu["id"]
        for dep in safe_depends_on(spu):
            if is_special_dependency(dep):
                continue
            if dep not in id_set:
                errors.append(
                    {"spu_id": sid, "dependency": dep, "type": "unknown_dependency"}
                )
            elif not allow_forward_dependency and dep not in seen:
                errors.append(
                    {"spu_id": sid, "dependency": dep, "type": "forward_dependency"}
                )
        seen.add(sid)

    return errors


def dependency_edges(record):
    """Return internal dependency edges as (dep, sid), excluding special deps."""
    id_set = set(spu_ids(record))
    edges = set()
    for spu in valid_spus(record):
        sid = spu["id"]
        for dep in safe_depends_on(spu):
            if is_special_dependency(dep):
                continue
            if dep in id_set:
                edges.add((dep, sid))
    return edges


def build_internal_graph(record):
    ids = list(dict.fromkeys(spu_ids(record)))
    id_set = set(ids)
    graph = {sid: [] for sid in ids}
    reverse_graph = {sid: [] for sid in ids}
    edge_set = dependency_edges(record)

    for dep, sid in edge_set:
        if dep in id_set and sid in id_set:
            graph[dep].append(sid)
            reverse_graph[sid].append(dep)

    return ids, graph, reverse_graph, edge_set


def has_cycle(record):
    ids, graph, reverse_graph, _ = build_internal_graph(record)
    indeg = {sid: len(reverse_graph[sid]) for sid in ids}

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
    if not isinstance(fb, dict):
        return False
    sid = fb.get("spu_id")
    return sid in set(spu_ids(record))


def edge_scores(gold_record, pred_record):
    gold_edges = dependency_edges(gold_record)
    pred_edges = dependency_edges(pred_record)
    true_positive = len(gold_edges & pred_edges)

    if len(pred_edges) == 0:
        precision = 1.0 if len(gold_edges) == 0 else 0.0
    else:
        precision = true_positive / len(pred_edges)

    if len(gold_edges) == 0:
        recall = 1.0 if len(pred_edges) == 0 else 0.0
    else:
        recall = true_positive / len(gold_edges)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        "edge_precision": precision,
        "edge_recall": recall,
        "edge_f1": f1,
        "gold_edge_count": len(gold_edges),
        "pred_edge_count": len(pred_edges),
        "edge_true_positive_count": true_positive,
    }


def graph_features(record):
    ids, graph, reverse_graph, edge_set = build_internal_graph(record)

    if not ids:
        return {
            "num_nodes": 0,
            "num_dependency_edges": 0,
            "num_source_nodes": 0,
            "num_sink_nodes": 0,
            "max_out_degree": 0,
            "max_in_degree": 0,
        }

    out_degrees = {sid: len(graph[sid]) for sid in ids}
    in_degrees = {sid: len(reverse_graph[sid]) for sid in ids}

    return {
        "num_nodes": len(ids),
        "num_dependency_edges": len(edge_set),
        "num_source_nodes": sum(1 for sid in ids if in_degrees[sid] == 0),
        "num_sink_nodes": sum(1 for sid in ids if out_degrees[sid] == 0),
        "max_out_degree": max(out_degrees.values()),
        "max_in_degree": max(in_degrees.values()),
    }


def reachable_count_from(graph, start):
    seen = set()
    stack = list(graph.get(start, []))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, []))
    return len(seen)


def critical_nodes(record):
    ids, graph, _, _ = build_internal_graph(record)
    if not ids:
        return []

    counts = {sid: reachable_count_from(graph, sid) for sid in ids}
    positive_counts = [count for count in counts.values() if count > 0]
    if not positive_counts:
        return []

    top_k = max(1, math.ceil(0.2 * len(ids)))
    sorted_counts = sorted(counts.values(), reverse=True)
    cutoff = sorted_counts[min(top_k, len(sorted_counts)) - 1]

    return [
        {"spu_id": sid, "reachable_count": counts[sid]}
        for sid in ids
        if counts[sid] >= cutoff and counts[sid] > 0
    ]


def first_break(record):
    fb = record.get("first_break", {})
    return fb if isinstance(fb, dict) else {}


def index_by_sample_id(records):
    by_id = {}
    missing_sample_id_records = []
    for idx, record in enumerate(records, 1):
        sample_id = record.get("sample_id")
        if sample_id is None:
            missing_sample_id_records.append((idx, record))
        elif sample_id not in by_id:
            by_id[sample_id] = record
        else:
            # Keep the first record for backward compatibility. The schema validator
            # is record-local, so duplicate sample_id is only reported as metadata.
            pass
    return by_id, missing_sample_id_records


def eval_records(gold_records, pred_records, allow_forward_dependency=False):
    gold_by_id, gold_missing_ids = index_by_sample_id(gold_records)
    pred_by_id, pred_missing_ids = index_by_sample_id(pred_records)

    gold_schema_by_id = {
        record.get("sample_id"): validate_record_schema(record, i, "gold")
        for i, record in enumerate(gold_records, 1)
        if record.get("sample_id") is not None
    }
    pred_schema_by_id = {
        record.get("sample_id"): validate_record_schema(record, i, "pred")
        for i, record in enumerate(pred_records, 1)
        if record.get("sample_id") is not None
    }

    rows = []

    for sample_id, gold in gold_by_id.items():
        pred = pred_by_id.get(sample_id)
        gold_fb = first_break(gold)

        if pred is None:
            rows.append(
                {
                    "sample_id": sample_id,
                    "missing_pred": True,
                    "gold_schema_errors": gold_schema_by_id.get(sample_id, []),
                    "pred_schema_errors": [],
                    "schema_errors": gold_schema_by_id.get(sample_id, []),
                    "gold_first_break": gold_fb.get("spu_id"),
                    "pred_first_break": None,
                    "first_break_correct": False,
                    "gold_break_type": gold_fb.get("break_type"),
                    "pred_break_type": None,
                    "break_type_correct": False,
                    "dag_ok": False,
                    "first_break_exists": False,
                    "dependency_error_count": None,
                    "dependency_errors": [],
                    "edge_precision": 0.0,
                    "edge_recall": 0.0,
                    "edge_f1": 0.0,
                    "gold_edge_count": len(dependency_edges(gold)),
                    "pred_edge_count": 0,
                    "edge_true_positive_count": 0,
                    "graph_features": None,
                    "critical_nodes": [],
                }
            )
            continue

        pred_fb = first_break(pred)
        dep_errs = dependency_errors(
            pred, allow_forward_dependency=allow_forward_dependency
        )
        pred_schema_errors = pred_schema_by_id.get(sample_id, [])
        gold_schema_errors = gold_schema_by_id.get(sample_id, [])
        scores = edge_scores(gold, pred)

        rows.append(
            {
                "sample_id": sample_id,
                "missing_pred": False,
                "gold_schema_errors": gold_schema_errors,
                "pred_schema_errors": pred_schema_errors,
                "schema_errors": gold_schema_errors + pred_schema_errors,
                "gold_first_break": gold_fb.get("spu_id"),
                "pred_first_break": pred_fb.get("spu_id"),
                "first_break_correct": gold_fb.get("spu_id") == pred_fb.get("spu_id"),
                "gold_break_type": gold_fb.get("break_type"),
                "pred_break_type": pred_fb.get("break_type"),
                "break_type_correct": gold_fb.get("break_type")
                == pred_fb.get("break_type"),
                "dag_ok": not has_cycle(pred),
                "first_break_exists": first_break_exists(pred),
                "dependency_error_count": len(dep_errs),
                "dependency_errors": dep_errs,
                **scores,
                "graph_features": graph_features(pred),
                "critical_nodes": critical_nodes(pred),
            }
        )

    for idx, record in gold_missing_ids:
        schema_errors = validate_record_schema(record, idx, "gold")
        rows.append(
            {
                "sample_id": None,
                "record_index": idx,
                "missing_pred": True,
                "gold_schema_errors": schema_errors,
                "pred_schema_errors": [],
                "schema_errors": schema_errors,
                "first_break_correct": False,
                "break_type_correct": False,
                "dag_ok": False,
                "first_break_exists": False,
                "dependency_error_count": None,
                "dependency_errors": [],
                "edge_precision": 0.0,
                "edge_recall": 0.0,
                "edge_f1": 0.0,
                "graph_features": None,
                "critical_nodes": [],
            }
        )

    extra_prediction_ids = sorted(set(pred_by_id) - set(gold_by_id))
    extra_prediction_rows = []
    for sample_id in extra_prediction_ids:
        pred = pred_by_id[sample_id]
        pred_schema_errors = pred_schema_by_id.get(sample_id, [])
        dep_errs = dependency_errors(
            pred, allow_forward_dependency=allow_forward_dependency
        )
        extra_prediction_rows.append(
            {
                "sample_id": sample_id,
                "extra_prediction": True,
                "pred_schema_errors": pred_schema_errors,
                "schema_errors": pred_schema_errors,
                "dag_ok": not has_cycle(pred),
                "first_break_exists": first_break_exists(pred),
                "dependency_error_count": len(dep_errs),
                "dependency_errors": dep_errs,
                "graph_features": graph_features(pred),
                "critical_nodes": critical_nodes(pred),
            }
        )

    for idx, record in pred_missing_ids:
        pred_schema_errors = validate_record_schema(record, idx, "pred")
        extra_prediction_rows.append(
            {
                "sample_id": None,
                "record_index": idx,
                "extra_prediction": True,
                "pred_schema_errors": pred_schema_errors,
                "schema_errors": pred_schema_errors,
                "dag_ok": not has_cycle(record),
                "first_break_exists": first_break_exists(record),
                "dependency_error_count": len(
                    dependency_errors(
                        record, allow_forward_dependency=allow_forward_dependency
                    )
                ),
                "dependency_errors": dependency_errors(
                    record, allow_forward_dependency=allow_forward_dependency
                ),
                "graph_features": graph_features(record),
                "critical_nodes": critical_nodes(record),
            }
        )

    return rows, extra_prediction_rows


def mean(values):
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def summarize(rows, extra_prediction_rows=None):
    n = len(rows)
    if n == 0:
        return {
            "num_samples": 0,
            "extra_predictions": len(extra_prediction_rows or []),
        }

    extra_prediction_rows = extra_prediction_rows or []

    return {
        "num_samples": n,
        "first_break_accuracy": sum(r["first_break_correct"] for r in rows) / n,
        "break_type_accuracy": sum(r["break_type_correct"] for r in rows) / n,
        "dag_ok_rate": sum(r["dag_ok"] for r in rows) / n,
        "first_break_exists_rate": sum(r["first_break_exists"] for r in rows) / n,
        "missing_predictions": sum(r["missing_pred"] for r in rows),
        "extra_predictions": len(extra_prediction_rows),
        "extra_prediction_ids": [
            r.get("sample_id") for r in extra_prediction_rows if r.get("sample_id")
        ],
        "schema_error_count": sum(len(r.get("schema_errors", [])) for r in rows)
        + sum(len(r.get("schema_errors", [])) for r in extra_prediction_rows),
        "mean_edge_precision": mean(r["edge_precision"] for r in rows),
        "mean_edge_recall": mean(r["edge_recall"] for r in rows),
        "mean_edge_f1": mean(r["edge_f1"] for r in rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--pred", required=True)
    parser.add_argument(
        "--allow-forward-dependency",
        action="store_true",
        help="Do not count dependencies on later SPUs as dependency errors.",
    )
    parser.add_argument(
        "--out",
        help="Optional JSON output path containing summary and detail rows.",
    )
    args = parser.parse_args()

    gold = read_jsonl(args.gold)
    pred = read_jsonl(args.pred)

    rows, extra_prediction_rows = eval_records(
        gold, pred, allow_forward_dependency=args.allow_forward_dependency
    )
    summary = summarize(rows, extra_prediction_rows)

    print("SUMMARY")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print("\nDETAILS")
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))

    if extra_prediction_rows:
        print("\nEXTRA_PREDICTIONS")
        for r in extra_prediction_rows:
            print(json.dumps(r, ensure_ascii=False))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": summary,
                    "details": rows,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")


if __name__ == "__main__":
    main()
