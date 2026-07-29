#!/usr/bin/env python3
"""Validate a proof-dag-schema-v0.4 JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from dag_core import read_graph, validate_graph, write_json


def validate_json_schema(graph: dict) -> list[str]:
    schema_path = Path(__file__).resolve().parent.parent / "references" / "dag-schema.json"
    with schema_path.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(graph), key=lambda item: list(item.path))
    rendered = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"schema {location}: {error.message}")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    graph = read_graph(args.graph)
    schema_errors = validate_json_schema(graph)
    semantic_errors = validate_graph(graph)
    errors = schema_errors + semantic_errors
    result = {
        "graph_id": graph.get("graph_id"),
        "valid": not errors,
        "error_count": len(errors),
        "schema_error_count": len(schema_errors),
        "semantic_error_count": len(semantic_errors),
        "errors": errors,
    }
    write_json(result, args.output)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
