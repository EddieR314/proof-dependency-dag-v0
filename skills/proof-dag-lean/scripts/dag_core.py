"""Validation and evaluation for proof-dag-schema-v0.4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "proof-dag-schema-v0.4"
ROOT_KINDS = {"given", "assumed", "case_assumed", "constructed"}
FACT_KINDS = ROOT_KINDS | {"derived"}
PROPAGATED_REASON_CODES = {"unsupported_input"}


def read_graph(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("The graph root must be a JSON object.")
    return value


def write_json(value: Any, path: str | Path | None = None) -> None:
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path is None:
        print(payload, end="")
    else:
        Path(path).write_text(payload, encoding="utf-8")


def _objects_by_key(
    items: list[Any], key: str
) -> dict[str, dict[str, Any]]:
    return {
        item[key]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get(key), str)
    }


def _duplicates(values: list[Any]) -> set[Any]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def canonical_predicate(canonical_form: str) -> str:
    head, separator, _ = canonical_form.partition("(")
    return head.strip() if separator else canonical_form.strip()


def inference_input_ids(inference: dict[str, Any]) -> list[str]:
    return [
        binding["fact_id"]
        for binding in inference.get("input_bindings", [])
        if isinstance(binding, dict) and isinstance(binding.get("fact_id"), str)
    ]


def scope_allows(
    fact_scope: str,
    inference_scope: str,
    scopes: dict[str, dict[str, Any]],
) -> bool:
    """Return whether the inference is in the Fact scope or a descendant."""
    current: str | None = inference_scope
    visited: set[str] = set()
    while current is not None and current not in visited:
        if current == fact_scope:
            return True
        visited.add(current)
        scope = scopes.get(current)
        if scope is None:
            return False
        current = scope.get("parent_id")
    return False


def validate_graph(graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if graph.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    graph_kind = graph.get("graph_kind")
    if graph_kind not in {"reference", "candidate"}:
        errors.append("graph_kind must be reference or candidate")

    facts = graph.get("facts")
    inferences = graph.get("inferences")
    targets = graph.get("target_fact_ids")
    scopes = graph.get("scopes")
    rules = graph.get("rule_schemas")
    if not isinstance(facts, list):
        return errors + ["facts must be a list"]
    if not isinstance(inferences, list):
        return errors + ["inferences must be a list"]
    if not isinstance(targets, list) or not targets:
        errors.append("target_fact_ids must be a nonempty list")
        targets = []
    if not isinstance(scopes, list) or not scopes:
        errors.append("scopes must be a nonempty list")
        scopes = []
    if not isinstance(rules, list) or not rules:
        errors.append("rule_schemas must be a nonempty list")
        rules = []

    fact_by_id = _objects_by_key(facts, "id")
    inference_by_id = _objects_by_key(inferences, "id")
    scope_by_id = _objects_by_key(scopes, "id")
    rule_by_id = _objects_by_key(rules, "rule_id")

    for label, values in (
        ("fact id", [item.get("id") for item in facts if isinstance(item, dict)]),
        (
            "inference id",
            [item.get("id") for item in inferences if isinstance(item, dict)],
        ),
        ("scope id", [item.get("id") for item in scopes if isinstance(item, dict)]),
        ("rule id", [item.get("rule_id") for item in rules if isinstance(item, dict)]),
    ):
        for duplicate in sorted(str(value) for value in _duplicates(values)):
            errors.append(f"duplicate {label}: {duplicate}")
    for duplicate in sorted(set(fact_by_id) & set(inference_by_id)):
        errors.append(f"id used by both Fact and Inference: {duplicate}")

    errors.extend(_validate_scopes(scope_by_id))
    errors.extend(_validate_rule_schemas(rule_by_id))
    for target in targets:
        if target not in fact_by_id:
            errors.append(f"unknown target Fact: {target}")

    producers: dict[str, list[str]] = {}
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            errors.append(f"facts[{index}] must be an object")
            continue
        fact_id = fact.get("id", f"facts[{index}]")
        if fact.get("introduction_kind") not in FACT_KINDS:
            errors.append(f"{fact_id}: invalid introduction_kind")
        roles = fact.get("roles")
        if not isinstance(roles, list) or not roles:
            errors.append(f"{fact_id}: roles must be a nonempty list")
        if fact.get("scope") not in scope_by_id:
            errors.append(f"{fact_id}: unknown scope {fact.get('scope')}")
        if not isinstance(fact.get("statement"), str) or not fact["statement"].strip():
            errors.append(f"{fact_id}: statement must be nonempty")
        canonical = fact.get("canonical_form")
        if not isinstance(canonical, str) or not canonical.strip():
            errors.append(f"{fact_id}: canonical_form must be nonempty")

    source_orders: list[int] = []
    for index, inference in enumerate(inferences):
        if not isinstance(inference, dict):
            errors.append(f"inferences[{index}] must be an object")
            continue
        inference_id = inference.get("id", f"inferences[{index}]")
        bindings = inference.get("input_bindings")
        if not isinstance(bindings, list) or not bindings:
            errors.append(f"{inference_id}: input_bindings must be a nonempty list")
            bindings = []
        input_ids: list[str] = []
        premise_roles: list[str] = []
        for binding_index, binding in enumerate(bindings):
            if not isinstance(binding, dict):
                errors.append(
                    f"{inference_id}: input_bindings[{binding_index}] must be an object"
                )
                continue
            fact_id = binding.get("fact_id")
            premise_role = binding.get("premise_role")
            if fact_id not in fact_by_id:
                errors.append(f"{inference_id}: unknown input Fact {fact_id}")
            if not isinstance(premise_role, str) or not premise_role:
                errors.append(f"{inference_id}: every input needs a premise_role")
            input_ids.append(fact_id)
            premise_roles.append(premise_role)
        if len(input_ids) != len(set(input_ids)):
            errors.append(f"{inference_id}: duplicate input Facts")
        if len(premise_roles) != len(set(premise_roles)):
            errors.append(f"{inference_id}: duplicate premise roles")

        output = inference.get("output_fact_id")
        if output not in fact_by_id:
            errors.append(f"{inference_id}: unknown output Fact {output}")
        else:
            producers.setdefault(output, []).append(inference_id)
        source_order = inference.get("source_order")
        if (
            not isinstance(source_order, int)
            or isinstance(source_order, bool)
            or source_order < 1
        ):
            errors.append(f"{inference_id}: source_order must be a positive integer")
        else:
            source_orders.append(source_order)
        if inference.get("scope") not in scope_by_id:
            errors.append(f"{inference_id}: unknown scope {inference.get('scope')}")
        if inference.get("rule_id") not in rule_by_id:
            errors.append(f"{inference_id}: unknown rule_id {inference.get('rule_id')}")
        if not isinstance(inference.get("variable_bindings"), dict):
            errors.append(f"{inference_id}: variable_bindings must be an object")

    expected_orders = list(range(1, len(inferences) + 1))
    if sorted(source_orders) != expected_orders:
        errors.append(
            "source_order must be a bijection onto 1..|I| "
            f"(got {sorted(source_orders)})"
        )
    for fact_id, fact in fact_by_id.items():
        if fact.get("introduction_kind") == "derived" and fact_id not in producers:
            errors.append(f"{fact_id}: derived Fact has no producer")

    cycle_nodes = _cycle_nodes(fact_by_id, inference_by_id)
    if graph_kind == "reference" and cycle_nodes:
        errors.append("reference graph contains a directed cycle")

    mutation = graph.get("mutation")
    if graph_kind == "reference" and mutation is not None:
        errors.append("reference graph must not contain mutation")
    if graph_kind == "candidate" and not isinstance(mutation, dict):
        errors.append("candidate graph requires a mutation record")
    if isinstance(mutation, dict):
        errors.extend(
            _validate_mutation(mutation, fact_by_id, inference_by_id, scope_by_id)
        )

    provenance = graph.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    return errors


def _validate_scopes(scopes: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    global_scope = scopes.get("global")
    if global_scope is None:
        errors.append("scopes must contain global")
    elif global_scope.get("parent_id") is not None:
        errors.append("global scope must have parent_id null")
    for scope_id, scope in scopes.items():
        parent = scope.get("parent_id")
        if parent is not None and parent not in scopes:
            errors.append(f"{scope_id}: unknown parent scope {parent}")
        if parent is not None and not scope_id.startswith(parent + "/"):
            errors.append(f"{scope_id}: hierarchical id must extend parent {parent}")
        current: str | None = scope_id
        visited: set[str] = set()
        while current is not None:
            if current in visited:
                errors.append(f"scope hierarchy contains a cycle at {current}")
                break
            visited.add(current)
            current = scopes.get(current, {}).get("parent_id")
    return errors


def _validate_rule_schemas(rules: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for rule_id, rule in rules.items():
        patterns = rule.get("input_patterns")
        if not isinstance(patterns, list) or not patterns:
            errors.append(f"{rule_id}: input_patterns must be a nonempty list")
            patterns = []
        roles = [
            item.get("premise_role")
            for item in patterns
            if isinstance(item, dict)
        ]
        if len(roles) != len(set(roles)):
            errors.append(f"{rule_id}: duplicate input-pattern premise roles")
        output = rule.get("output_pattern")
        if not isinstance(output, dict) or not isinstance(
            output.get("predicate"), str
        ):
            errors.append(f"{rule_id}: output_pattern needs a predicate")
    return errors


def _validate_mutation(
    mutation: dict[str, Any],
    facts: dict[str, dict[str, Any]],
    inferences: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    site = mutation.get("primary_site", {})
    site_type = site.get("type")
    site_id = site.get("id")
    known_by_type = {"fact": facts, "inference": inferences, "scope": scopes}
    if site_type in known_by_type and site_id not in known_by_type[site_type]:
        errors.append(f"mutation primary_site references unknown {site_type}: {site_id}")
    anchor = mutation.get("injection_anchor", {})
    anchor_type = anchor.get("type")
    anchor_id = anchor.get("id")
    if anchor_type == "fact" and anchor_id not in facts:
        errors.append(f"mutation references unknown Fact anchor: {anchor_id}")
    if anchor_type == "inference" and anchor_id not in inferences:
        errors.append(f"mutation references unknown Inference anchor: {anchor_id}")
    expected = mutation.get("declared_expected_first_break", {})
    expected_type = expected.get("type")
    expected_id = expected.get("id")
    if expected_type == "fact" and expected_id not in facts:
        errors.append(f"mutation references unknown expected Fact: {expected_id}")
    if expected_type == "inference" and expected_id not in inferences:
        errors.append(f"mutation references unknown expected Inference: {expected_id}")
    return errors


def rule_match_issues(
    inference: dict[str, Any],
    facts: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
) -> list[str]:
    rule = rules.get(inference.get("rule_id"))
    if rule is None:
        return ["unknown_rule"]
    expected = {
        pattern["premise_role"]: pattern["predicate"]
        for pattern in rule.get("input_patterns", [])
    }
    actual = {
        binding.get("premise_role"): binding.get("fact_id")
        for binding in inference.get("input_bindings", [])
        if isinstance(binding, dict)
    }
    issues: list[str] = []
    for role, predicate in expected.items():
        fact_id = actual.get(role)
        if fact_id is None:
            issues.append(f"missing_premise_role:{role}")
        elif fact_id in facts and canonical_predicate(
            facts[fact_id]["canonical_form"]
        ) != predicate:
            issues.append(f"premise_predicate_mismatch:{role}")
    for role in actual:
        if role not in expected:
            issues.append(f"unexpected_premise_role:{role}")
    output = facts.get(inference.get("output_fact_id"))
    if output is not None:
        expected_output = rule.get("output_pattern", {})
        if canonical_predicate(output["canonical_form"]) != expected_output.get(
            "predicate"
        ):
            issues.append("output_mismatch")
        exact = expected_output.get("canonical_form")
        if exact and output["canonical_form"] != exact:
            issues.append("output_mismatch")
    variables = set(rule.get("variables", []))
    bindings = set(inference.get("variable_bindings", {}))
    if variables != bindings:
        issues.append("variable_binding_mismatch")
    return sorted(set(issues))


def _scope_issues(
    inference: dict[str, Any],
    facts: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    inference_scope = inference["scope"]
    for fact_id in inference_input_ids(inference):
        fact = facts.get(fact_id)
        if fact is None:
            continue
        fact_scope = fact["scope"]
        if not scope_allows(fact_scope, inference_scope, scopes):
            issues.append(
                {
                    "kind": "invisible_input",
                    "fact_id": fact_id,
                    "fact_scope": fact_scope,
                    "inference_scope": inference_scope,
                }
            )
    output = facts.get(inference.get("output_fact_id"))
    if output is None or output["scope"] == inference_scope:
        return issues
    constraints = rules.get(inference.get("rule_id"), {}).get(
        "scope_constraints", []
    )
    operations = {
        "allow_scope_discharge",
        "allow_scope_merge",
        "allow_scope_export",
    }
    if not operations.intersection(constraints):
        issues.append(
            {
                "kind": "undeclared_scope_export",
                "fact_id": output["id"],
                "fact_scope": output["scope"],
                "inference_scope": inference_scope,
            }
        )
    elif not scope_allows(output["scope"], inference_scope, scopes):
        issues.append(
            {
                "kind": "invalid_scope_export_target",
                "fact_id": output["id"],
                "fact_scope": output["scope"],
                "inference_scope": inference_scope,
            }
        )
    return issues


def _cycle_nodes(
    facts: dict[str, dict[str, Any]],
    inferences: dict[str, dict[str, Any]],
) -> set[str]:
    adjacency: dict[str, set[str]] = {
        node_id: set() for node_id in {*facts, *inferences}
    }
    for inference_id, inference in inferences.items():
        for fact_id in inference_input_ids(inference):
            if fact_id in facts:
                adjacency[fact_id].add(inference_id)
        output = inference.get("output_fact_id")
        if output in facts:
            adjacency[inference_id].add(output)

    visiting: list[str] = []
    visiting_set: set[str] = set()
    visited: set[str] = set()
    cycle_nodes: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting_set:
            cycle_nodes.update(visiting[visiting.index(node) :])
            return
        if node in visited:
            return
        visiting.append(node)
        visiting_set.add(node)
        for child in adjacency[node]:
            visit(child)
        visiting.pop()
        visiting_set.remove(node)
        visited.add(node)

    for node in adjacency:
        visit(node)
    return cycle_nodes


def evaluate_graph(
    graph: dict[str, Any],
    blocked_node: str | None = None,
) -> dict[str, Any]:
    facts = _objects_by_key(graph["facts"], "id")
    inferences = _objects_by_key(graph["inferences"], "id")
    rules = _objects_by_key(graph["rule_schemas"], "rule_id")
    scopes = _objects_by_key(graph["scopes"], "id")
    ordered = sorted(
        graph["inferences"], key=lambda item: item["source_order"]
    )
    cycle_nodes = _cycle_nodes(facts, inferences)

    derived = {
        fact_id
        for fact_id, fact in facts.items()
        if fact["introduction_kind"] in ROOT_KINDS and fact_id != blocked_node
    }
    inference_results: dict[str, dict[str, Any]] = {}
    changed = True
    while changed:
        changed = False
        for inference in ordered:
            inference_id = inference["id"]
            if inference_id == blocked_node:
                continue
            intrinsic_reasons = rule_match_issues(inference, facts, rules)
            scope_violations = _scope_issues(inference, facts, scopes, rules)
            if scope_violations:
                intrinsic_reasons.append("scope_violation")
            if inference_id in cycle_nodes:
                intrinsic_reasons.append("cyclic_dependency")
            intrinsic_reasons = sorted(set(intrinsic_reasons))
            input_ids = inference_input_ids(inference)
            unsupported = [
                fact_id
                for fact_id in input_ids
                if fact_id == blocked_node or fact_id not in derived
            ]
            if intrinsic_reasons:
                intrinsic_status = "invalid"
                effective_status = "invalid"
                reason_codes = intrinsic_reasons
            elif unsupported:
                intrinsic_status = "valid"
                effective_status = "blocked"
                reason_codes = ["unsupported_input"]
            else:
                intrinsic_status = "valid"
                effective_status = "executable"
                reason_codes = []
                output = inference["output_fact_id"]
                if output != blocked_node and output not in derived:
                    derived.add(output)
                    changed = True
            inference_results[inference_id] = {
                "graph_id": graph["graph_id"],
                "inference_id": inference_id,
                "source_order": inference["source_order"],
                "intrinsic_status": intrinsic_status,
                "effective_status": effective_status,
                "reason_codes": reason_codes,
                "unsupported_input_fact_ids": unsupported,
                "computed_by": "dag_core.py",
                "evaluation_version": SCHEMA_VERSION,
            }

    first_break_id = next(
        (
            item["id"]
            for item in ordered
            if item["id"] != blocked_node
            and inference_results[item["id"]]["effective_status"] != "executable"
        ),
        None,
    )
    fact_evaluations = [
        {
            "graph_id": graph["graph_id"],
            "fact_id": fact_id,
            "support_status": (
                "supported" if fact_id in derived else "unsupported"
            ),
            "availability_cache": "unknown",
            "computed_by": "dag_core.py",
            "evaluation_version": SCHEMA_VERSION,
        }
        for fact_id in facts
    ]
    inference_evaluations = [
        inference_results[item["id"]] for item in ordered if item["id"] != blocked_node
    ]
    scope_violations = [
        issue
        for inference in ordered
        for issue in _scope_issues(inference, facts, scopes, rules)
    ]
    targets = graph["target_fact_ids"]
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "graph_id": graph["graph_id"],
        "blocked_node": blocked_node,
        "fact_evaluations": fact_evaluations,
        "inference_evaluations": inference_evaluations,
        "computed_first_break": (
            {"type": "inference", "id": first_break_id}
            if first_break_id is not None
            else None
        ),
        "target_status": {target: target in derived for target in targets},
        "all_targets_derivable": all(target in derived for target in targets),
        "scope_check": {
            "passed": not scope_violations,
            "scope_count": len(scopes),
            "local_scope_count": sum(
                1 for scope_id in scopes if scope_id != "global"
            ),
            "violations": scope_violations,
        },
    }
    mutation = graph.get("mutation")
    if isinstance(mutation, dict):
        expected = mutation["declared_expected_first_break"]
        result["declared_expected_first_break"] = expected
        result["first_break_match"] = result["computed_first_break"] == expected
        result["mutation_evaluation"] = {
            **mutation,
            "computed_first_break": result["computed_first_break"],
            "first_break_match": result["first_break_match"],
        }
    return result


def evaluate_criticality(
    graph: dict[str, Any],
    candidate: str,
) -> dict[str, Any]:
    facts = {fact["id"] for fact in graph.get("facts", [])}
    inferences = {
        inference["id"] for inference in graph.get("inferences", [])
    }
    known_nodes = facts | inferences
    if candidate not in known_nodes:
        raise ValueError(f"Unknown criticality candidate: {candidate}")
    targets = graph["target_fact_ids"]
    if candidate in targets:
        return {
            "graph_id": graph["graph_id"],
            "candidate_id": candidate,
            "candidate_type": "fact",
            "target_fact_ids": targets,
            "critical_status": "not_evaluable",
            "reason": "candidate_is_target",
        }
    baseline = evaluate_graph(graph)
    if not baseline["all_targets_derivable"]:
        return {
            "graph_id": graph["graph_id"],
            "candidate_id": candidate,
            "candidate_type": "fact" if candidate in facts else "inference",
            "target_fact_ids": targets,
            "critical_status": "not_evaluable",
            "derivable_before": False,
            "derivable_after": None,
        }
    blocked = evaluate_graph(graph, blocked_node=candidate)
    critical = any(
        baseline["target_status"][target]
        and not blocked["target_status"][target]
        for target in targets
    )
    return {
        "graph_id": graph["graph_id"],
        "candidate_id": candidate,
        "candidate_type": "fact" if candidate in facts else "inference",
        "target_fact_ids": targets,
        "block_mode": "full_node_block",
        "derivable_before": True,
        "derivable_after": blocked["all_targets_derivable"],
        "critical_status": "critical" if critical else "noncritical",
        "baseline_target_status": baseline["target_status"],
        "blocked_target_status": blocked["target_status"],
    }
