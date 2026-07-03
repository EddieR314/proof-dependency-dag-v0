import json
import re
from collections import defaultdict, deque


SPECIAL_DEPS = {"problem", "given", "definition"}

VALID_STATUSES = {
    "valid",
    "invalid",
    "unsupported",
    "valid_but_irrelevant",
    "unknown",
}

BAD_STATUSES = {"invalid", "unsupported"}

VALID_BREAK_TYPES = {
    "missing_dependency",
    "missing_premise_edge",
    "case_omission",
    "invalid_theorem_use",
    "overclaim_final",
    "variable_mismatch",
    "calculation_error",
    "scope_error",
    "unsupported_conclusion",
    "irrelevant_step",
}

VALID_ROLES = {
    "aggregation",
    "assumption",
    "calculation",
    "case_assumption",
    "case_conclusion",
    "case_split",
    "final_conclusion",
    "inference",
    "restatement_of_condition",
    "theorem_use",
    "wlog",
}


def read_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Bad JSON on line {line_number}: {exc}") from exc
    return records


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def spu_ids(record):
    return [spu.get("id") for spu in record.get("spus", [])]


def spu_by_id(record):
    return {spu["id"]: spu for spu in record.get("spus", []) if "id" in spu}


def dependency_errors(record):
    ids = spu_ids(record)
    id_set = set(ids)
    seen = set()
    errors = []

    for spu in record.get("spus", []):
        sid = spu.get("id")
        for dep in spu.get("depends_on", []):
            if dep in SPECIAL_DEPS or str(dep).startswith("external:"):
                continue
            if dep == sid:
                errors.append((sid, dep, "self_dependency"))
            elif dep not in id_set:
                errors.append((sid, dep, "unknown_dependency"))
            elif dep not in seen:
                errors.append((sid, dep, "forward_dependency"))
        seen.add(sid)

    return errors


def build_graph(record):
    id_set = set(spu_ids(record))
    graph = defaultdict(list)
    reverse_graph = defaultdict(list)

    for spu in record.get("spus", []):
        sid = spu.get("id")
        for dep in spu.get("depends_on", []):
            if dep in id_set:
                graph[dep].append(sid)
                reverse_graph[sid].append(dep)

    return graph, reverse_graph


def has_cycle(record):
    ids = [sid for sid in spu_ids(record) if sid is not None]
    graph, _ = build_graph(record)
    indegree = {sid: 0 for sid in ids}

    for source in ids:
        for target in graph[source]:
            indegree[target] += 1

    queue = deque([sid for sid in ids if indegree[sid] == 0])
    seen = 0

    while queue:
        sid = queue.popleft()
        seen += 1
        for target in graph[sid]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    return seen != len(ids)


def first_break_exists(record):
    first_break = record.get("first_break", {})
    return first_break.get("spu_id") in set(spu_ids(record))


def first_break_consistency_errors(record):
    errors = []
    first_break = record.get("first_break", {})
    first_break_id = first_break.get("spu_id")
    by_id = spu_by_id(record)

    if not first_break_id:
        return [("first_break", None, "missing_first_break")]
    if first_break_id not in by_id:
        return [("first_break", first_break_id, "unknown_first_break")]

    break_type = first_break.get("break_type")
    if break_type not in VALID_BREAK_TYPES:
        errors.append(("first_break", break_type, "invalid_break_type"))

    break_spu = by_id[first_break_id]
    if break_spu.get("status") not in BAD_STATUSES:
        errors.append((first_break_id, break_spu.get("status"), "first_break_not_bad"))

    for spu in record.get("spus", []):
        sid = spu.get("id")
        if sid == first_break_id:
            break
        if spu.get("status") in BAD_STATUSES:
            errors.append((sid, spu.get("status"), "bad_step_before_first_break"))

    return errors


def dependency_closure_errors(record):
    by_id = spu_by_id(record)
    errors = []

    for spu in record.get("spus", []):
        sid = spu.get("id")
        status = spu.get("status")
        bad_deps = [
            dep
            for dep in spu.get("depends_on", [])
            if dep in by_id and by_id[dep].get("status") in BAD_STATUSES
        ]
        if bad_deps and status not in BAD_STATUSES:
            errors.append(
                {
                    "spu_id": sid,
                    "status": status,
                    "bad_dependencies": bad_deps,
                    "error": "bad_dependency_not_propagated",
                }
            )

    return errors


def downstream_nodes(record, start_id):
    graph, _ = build_graph(record)
    seen = set()
    queue = deque(graph.get(start_id, []))

    while queue:
        sid = queue.popleft()
        if sid in seen:
            continue
        seen.add(sid)
        queue.extend(graph.get(sid, []))

    return sorted(seen, key=natural_spu_sort_key)


def case_scope_errors(record):
    errors = []
    by_id = spu_by_id(record)
    scopes = {
        spu.get("case_scope")
        for spu in record.get("spus", [])
        if spu.get("case_scope") and spu.get("case_scope") != "global"
    }

    for spu in record.get("spus", []):
        sid = spu.get("id")
        scope = spu.get("case_scope")
        if not scope:
            errors.append({"spu_id": sid, "error": "missing_case_scope"})
            continue

        for dep in spu.get("depends_on", []):
            if dep not in by_id:
                continue
            dep_scope = by_id[dep].get("case_scope")
            if (
                scope != "global"
                and dep_scope not in {"global", scope}
            ):
                errors.append(
                    {
                        "spu_id": sid,
                        "dependency": dep,
                        "case_scope": scope,
                        "dependency_scope": dep_scope,
                        "error": "cross_case_dependency",
                    }
                )

    for scope in scopes:
        scoped_steps = [
            spu for spu in record.get("spus", [])
            if spu.get("case_scope") == scope
        ]
        if not any(spu.get("role") in {"case_assumption", "case_conclusion"} for spu in scoped_steps):
            errors.append({"case_scope": scope, "error": "case_scope_has_no_case_node"})

    declared_cases = set(record.get("case_scopes", []))
    if declared_cases:
        present_cases = scopes
        missing_cases = sorted(declared_cases - present_cases)
        if missing_cases:
            errors.append({"missing_cases": missing_cases, "error": "declared_case_absent"})

    return errors


def validate_record(record):
    errors = []

    for field in ["sample_id", "spus", "first_break"]:
        if field not in record:
            errors.append(("record", field, "missing_field"))

    if "spus" in record and not isinstance(record["spus"], list):
        errors.append(("record", "spus", "spus_not_list"))
        return errors

    ids = spu_ids(record)
    for sid in sorted({sid for sid in ids if ids.count(sid) > 1}):
        errors.append((sid, "id", "duplicate_spu_id"))

    for index, spu in enumerate(record.get("spus", []), 1):
        prefix = spu.get("id", f"spu[{index}]")
        for field in ["id", "text", "role", "depends_on", "case_scope", "status"]:
            if field not in spu:
                errors.append((prefix, field, "missing_field"))
        if "depends_on" in spu and not isinstance(spu["depends_on"], list):
            errors.append((prefix, "depends_on", "depends_on_not_list"))
        if spu.get("role") not in VALID_ROLES:
            errors.append((prefix, spu.get("role"), "invalid_role"))
        if spu.get("status") not in VALID_STATUSES:
            errors.append((prefix, spu.get("status"), "invalid_status"))
        if spu.get("status") == "unsupported" and not (
            spu.get("missing_dependencies")
            or any(dep in spu_by_id(record) and spu_by_id(record)[dep].get("status") in BAD_STATUSES for dep in spu.get("depends_on", []))
            or spu.get("notes")
        ):
            errors.append((prefix, "unsupported", "unsupported_without_reason"))

    errors.extend(dependency_errors(record))
    errors.extend(first_break_consistency_errors(record))

    if has_cycle(record):
        errors.append(("record", "depends_on", "cycle_detected"))

    return errors


def natural_spu_sort_key(spu_id):
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", str(spu_id))
    if not match:
        return (str(spu_id), 0)
    return (match.group(1), int(match.group(2)))
